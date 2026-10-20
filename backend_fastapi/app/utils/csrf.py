"""Session-bound CSRF protection for credentialed browser writes."""
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import settings


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            origin = request.headers.get('origin')
            own_origin = f'{request.url.scheme}://{request.url.netloc}'
            if origin and origin != own_origin and origin not in settings.allowed_origins_list:
                return JSONResponse({'detail': 'CSRF origin rejected'}, status_code=403)
            if request.session.get('user_id'):
                token = request.headers.get('x-csrftoken', '')
                expected = request.session.get('csrf_token', '')
                if not token or not expected or not secrets.compare_digest(token, expected):
                    return JSONResponse({'detail': 'CSRF token required'}, status_code=403)
        return await call_next(request)
