import hmac
import hashlib
import time
import asyncio
import json
import logging
import inspect
from functools import wraps
from typing import Optional, Callable, Dict, Any, List, Union, Awaitable
from .exceptions import InvalidSignatureError, ExpiredTimestampError

try:
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

logger = logging.getLogger("lazyhooks")

def verify_signature(payload_body: bytes, signature_header: str, secret: str, timestamp_header: str, tolerance: int = 300) -> bool:
    """
    Verifies that the signature header matches the HMAC-SHA256 of the payload body + timestamp.
    Also checks if the timestamp is within the tolerance window (default 5 minutes).
    
    :param payload_body: The raw bytes of the request body.
    :param signature_header: The value of 'X-Lh-Signature' (e.g., 'v1=...')
    :param secret: The shared secret key.
    :param timestamp_header: The value of 'X-Lh-Timestamp'.
    :param tolerance: Maximum age of the request in seconds.
    :return: True if valid, False otherwise.
    """
    if not signature_header or not timestamp_header:
        raise InvalidSignatureError("Missing signature or timestamp headers")

    # 1. Verify Timestamp Freshness
    try:
        timestamp = int(timestamp_header)
    except ValueError:
        raise InvalidSignatureError("Invalid timestamp format")

    now = int(time.time())
    if now - timestamp > tolerance:
        raise ExpiredTimestampError(f"Timestamp expired. Age: {now - timestamp}s, Limit: {tolerance}s", age=now-timestamp, max_age=tolerance)

    # 2. Verify Signature
    # reconstruct: "timestamp.body"
    if not signature_header.startswith("v1="):
        raise InvalidSignatureError("Invalid signature format. Must start with v1=")
        
    to_sign = f"{timestamp}.".encode() + payload_body
    
    expected_sig = hmac.new(
        secret.encode(),
        to_sign,
        hashlib.sha256
    ).hexdigest()

    incoming_sig = signature_header.split("v1=")[1]
    
    if not hmac.compare_digest(expected_sig, incoming_sig):
        raise InvalidSignatureError("Signature mismatch")
    
    return True

class WebhookReceiver:
    def __init__(
        self, 
        signing_secret: str,
        tolerance: int = 300,
        on_error: Optional[Callable[[Exception], None]] = None,
        return_errors: bool = False,
        enable_metrics: bool = False
    ):
        self.signing_secret = signing_secret
        self.tolerance = tolerance
        self.on_error = on_error
        self.return_errors = return_errors
        self.enable_metrics = enable_metrics
        self.handlers: Dict[str, Dict[str, Any]] = {}
        self.middlewares: List[Callable] = []
        self._catch_all_handler: Optional[Dict[str, Any]] = None

    def on(self, event_type: str, schema: Any = None):
        """
        Decorator to register an event handler.
        :param event_type: The event type string to match (e.g., "user.created"). Use "*" for catch-all.
        :param schema: Optional Pydantic model to validate the payload against.
        """
        def decorator(func):
            if event_type == "*":
                self._catch_all_handler = {"func": func, "schema": schema}
            else:
                self.handlers[event_type] = {"func": func, "schema": schema}
            return func
        return decorator

    def middleware(self, func):
        """
        Decorator to register a middleware.
        Middleware signature: async def my_middleware(event, next_handler)
        """
        self.middlewares.append(func)
        return func

    def use(self, func):
        """Register a middleware function directly."""
        self.middlewares.append(func)

    async def _run_middleware_chain(self, event: Dict[str, Any]) -> Any:
        """
        Executes the middleware chain and then the appropriate handler.
        """
        
        async def final_handler(evt):
            event_type = evt.get("event")
            handler_info = self.handlers.get(event_type)
            
            # Wildcard or exact matching logic
            if not handler_info:
                # Try simple wildcard matching event.*
                for key, info in self.handlers.items():
                    if key.endswith("*") and event_type.startswith(key[:-1]):
                         handler_info = info
                         break
            
            if not handler_info:
                if self._catch_all_handler:
                    handler_info = self._catch_all_handler
                else:
                    logger.debug(f"No handler for event: {event_type}")
                    return None
            
            func = handler_info["func"]
            schema = handler_info["schema"]
            
            # Pydantic validation
            if schema and HAS_PYDANTIC:
                try:
                    if issubclass(schema, BaseModel):
                        evt_data = schema(**evt)
                        
                        # Check function signature
                        sig = inspect.signature(func)
                        if len(sig.parameters) == 1:
                            if inspect.iscoroutinefunction(func):
                                return await func(evt_data)
                            else:
                                return func(evt_data)
                except Exception as e:
                     logger.error(f"Schema validation failed: {e}")
                     raise ValueError(f"Schema validation failed: {e}")

            # Standard Dict handling
            if inspect.iscoroutinefunction(func):
                return await func(evt)
            else:
                return func(evt)

        # Build the chain
        # inner(event) -> middleware1(event, next=middleware2) -> ... -> final_handler(event)
        
        chain = final_handler
        
        for md in reversed(self.middlewares):
            # Create a closure to capture 'md' and current 'chain'
            def make_wrapped_middleware(current_middleware, next_step):
                async def wrapped(evt):
                    if inspect.iscoroutinefunction(current_middleware):
                        return await current_middleware(evt, next_step)
                    else:
                        # For sync middleware, we assume it might return an awaitable (from next_step)
                        # or a direct value.
                        res = current_middleware(evt, next_step)
                        if inspect.isawaitable(res):
                            return await res
                        return res
                return wrapped
            
            chain = make_wrapped_middleware(md, chain)
            
        return await chain(event)

    def verify_and_parse(
        self, 
        body: bytes, 
        signature: str, 
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Verifies the webhook signature and parses the body.
        Raises InvalidSignatureError, ExpiredTimestampError, or ValueError on JSON error.
        """
        # Raises verification exceptions directly
        verify_signature(body, signature, self.signing_secret, timestamp, self.tolerance)
        
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    async def process_event(self, event_data: Dict[str, Any]):
        """
        Internal method to process the parsed event through middleware and handlers (Async).
        """
        try:
            await self._run_middleware_chain(event_data)
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            logger.error(f"Error processing webhook: {e}")
            if self.return_errors:
                raise e

    def process_event_sync(self, event_data: Dict[str, Any]):
        """
        Synchronous wrapper for process_event.
        Uses asyncio.run() to execute the handler chain.
        WARNING: Do not use this if already inside an async loop.
        """
        try:
            asyncio.run(self.process_event(event_data))
        except RuntimeError as e:
            # Fallback if loop is already running? 
            # Ideally we shouldn't be here if loop is running. 
            # But if user made a mistake, maybe we can direct them?
            if "Event loop is closed" in str(e):
                 # Create new loop? No, default behavior of run() handles it.
                 pass
            raise e

    # --- Framework Adapters ---

    def as_flask_view(self):
        """Returns a view function for Flask."""
        from flask import request, jsonify, Response # type: ignore

        async def flask_handler():
            # Flask 2.0+ supports async route handlers
            sig = request.headers.get("X-Lh-Signature")
            ts = request.headers.get("X-Lh-Timestamp")
            body = request.get_data()

            try:
                event = self.verify_and_parse(body, sig, ts)
            except (InvalidSignatureError, ExpiredTimestampError) as e:
                return jsonify({"error": str(e)}), 401
            except ValueError as e:
                 # JSON error
                return jsonify({"error": str(e)}), 400
            
            # Process in background? Or await?
            # User example suggests await.
            try:
                await self.process_event(event)
                return jsonify({"status": "ok"}), 200
            except Exception as e:
                # process_event usually catches errors if on_error is set, 
                # but if return_errors is True or it bubbles up:
                status = 500
                msg = str(e) if self.return_errors else "Internal Server Error"
                return jsonify({"error": msg}), status

        # Flask async support requires 'asgiref' usually if running with standard wsgi, 
        # checking if we need to wrap it or if the user is using async flask (Quart or Flask 2.0+ with suitable runner).
        # Assuming standard Flask 2.0+ async routes.
        return flask_handler

    def as_fastapi_endpoint(self):
        """Returns an endpoint function for FastAPI."""
        from fastapi import Request, HTTPException, status # type: ignore
        from fastapi.responses import JSONResponse # type: ignore

        async def fastapi_handler(request: Request):
            sig = request.headers.get("X-Lh-Signature")
            ts = request.headers.get("X-Lh-Timestamp")
            body = await request.body()

            try:
                event = self.verify_and_parse(body, sig, ts)
            except (InvalidSignatureError, ExpiredTimestampError) as e:
                raise HTTPException(status_code=401, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            try:
                await self.process_event(event)
                return JSONResponse(content={"status": "ok"}, status_code=200)
            except Exception as e:
                detail = str(e) if self.return_errors else "Internal Server Error"
                raise HTTPException(status_code=500, detail=detail)

        return fastapi_handler
    
    def as_django_view(self):
        """Returns a view function for Django."""
        from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError # type: ignore
        from django.views.decorators.csrf import csrf_exempt # type: ignore
        import asyncio

        @csrf_exempt
        def django_handler(request):
            if request.method != "POST":
                return HttpResponseBadRequest("Only POST allowed")
            
            sig = request.headers.get("X-Lh-Signature")
            ts = request.headers.get("X-Lh-Timestamp")
            body = request.body

            return _async_django_view(request)

        async def _async_django_view(request):
            sig = request.headers.get("X-Lh-Signature")
            ts = request.headers.get("X-Lh-Timestamp")
            body = request.body
            
            try:
                # verify_signature raises exception now
                verify_signature(body, sig, self.signing_secret, ts, self.tolerance)
                event = json.loads(body)
            except (InvalidSignatureError, ExpiredTimestampError) as e:
                 return HttpResponseForbidden(str(e))
            except json.JSONDecodeError:
                 return HttpResponseBadRequest("Invalid JSON")
            except Exception:
                return HttpResponseBadRequest("Invalid request")

            try:
                await self.process_event(event)
                return JsonResponse({"status": "ok"})
            except Exception as e:
                if self.return_errors:
                    return HttpResponseServerError(str(e))
                return HttpResponseServerError("Internal Server Error")

        return _async_django_view

    def run(self, host: str = "0.0.0.0", port: int = 5000):
        """Run a standalone simple server using aiohttp."""
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp is required for WebhookReceiver.run(). Install it with 'pip install aiohttp'.")

        async def handler(request):
            sig = request.headers.get("X-Lh-Signature")
            ts = request.headers.get("X-Lh-Timestamp")
            body = await request.read()

            try:
                event = self.verify_and_parse(body, sig, ts)
            except ValueError as e:
                return web.json_response({"error": str(e)}, status=401)
            
            try:
                await self.process_event(event)
                return web.json_response({"status": "ok"})
            except Exception as e:
                logger.exception("Error handling webhook")
                msg = str(e) if self.return_errors else "Internal Server Error"
                return web.json_response({"error": msg}, status=500)

        app = web.Application()
        app.router.add_post("/", handler)
        
        print(f"WebhookReceiver running on http://{host}:{port}")
        web.run_app(app, host=host, port=port)
