from fastapi import Request


async def log_request(request: Request, call_next):
    """Middleware to log incoming requests and response status."""
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response
