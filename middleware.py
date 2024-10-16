from main import app
from utilities.auth import verify_token

from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import time
import logging

logger = logging.getLogger('uvicorn.access')
logger.disabled = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)
class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            if request.url.path in ['/docs','/login','/register','/openapi.json']:
                return await call_next(request)
            token = request.headers.get("Authorization")
            if token.startswith("Bearer"):
                token = token.split(" ")[1] 
            if not verify_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="UnAuthorized"
                )
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

app.add_middleware(CustomMiddleware)

@app.middleware('http')
async def custom_logging(request: Request, call_next):
    start_time = time.time()
    print("start time", start_time)
    response = await call_next(request)
    proccessing_time = time.time() - start_time
    message = f"{request.client.host} : {request.client.port} - {request.method} {request.url.path} {response.status_code} proccessed after {proccessing_time}"
    print(message)
    return response