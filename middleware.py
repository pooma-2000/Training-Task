from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from utilities import auth
from main import app

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            print("executing the middleware.......")
            print("request", request.headers)
            auth.verify_token(request)
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

app.add_middleware(CustomMiddleware)
