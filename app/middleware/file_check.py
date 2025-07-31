from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_FILE_SIZE_MB = 800
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class FileSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check for multipart/form-data (file uploads)
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type.lower():
            # Read the body to check the size
            body = await request.body()
            if len(body) > MAX_FILE_SIZE_BYTES:

                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Uploaded file size exceeds {MAX_FILE_SIZE_MB}MB limit."},
                )

            # Re-inject the body for downstream handlers
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive
        response = await call_next(request)
        return response
