from typing import Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

OWASP_SECURITY_HEADERS: Dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(self)",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none';"
}

def apply_security_headers(response: Response) -> Response:
    """Applies standard OWASP defensive headers to an outgoing HTTP response."""
    for header_name, header_val in OWASP_SECURITY_HEADERS.items():
        response.headers[header_name] = header_val
    return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    OWASP-compliant security headers middleware.
    Protects against MIME sniffing, clickjacking, XSS, and frame injection.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        return apply_security_headers(response)
