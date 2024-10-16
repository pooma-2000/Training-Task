from main import app
from utilities.auth import verify_token

from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTasks

import time
import logging

logging.basicConfig(filename='info.log', level=logging.DEBUG)

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)

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
            start_time = time.time()
            print("start time", start_time)
            response = await call_next(request)
            proccessing_time = time.time() - start_time
            message = f"{request.client.host} : {request.client.port} - {request.method} {request.url.path} {response.status_code} proccessed after {proccessing_time}"
            print(message)
            return response
        except HTTPException as exc:
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

app.add_middleware(CustomMiddleware)

@app.middleware('http')
async def logging_middleware(request: Request, call_next):
    req_body = await request.body()
    response = await call_next(request)
    res_body = b''
    async for chunk in response.body_iterator:
        res_body += chunk
    background_task = BackgroundTasks()
    background_task.add_task(log_info,req_body.decode('utf-8'), res_body.decode('utf-8'))
    return Response(content=res_body, status_code=response.status_code, 
        headers=dict(response.headers), media_type=response.media_type, background=background_task)