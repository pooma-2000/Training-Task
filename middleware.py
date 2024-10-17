from main import app
from utilities.auth import verify_token

from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTasks

import time
import logging
import traceback

logging.basicConfig(filename='info.log', level=logging.DEBUG)

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)

EXCLUDED_PATHS = ['/docs','/auth/login','/auth/register','/openapi.json', '/favicon.ico']

RESOURCES_FOR_ROLES = {
        "/dashboard/manage_users": {
            "admin": ['read','delete','edit'],
        },
        "/dashboard/user_profile": {
            "user": ['read','delete','edit'],
            "admin": ['read','delete','edit']
        },
        "/dashboard/edit_user/{user_id}":{
            "user": ['read','delete','edit'],
            "admin": ['read','delete','edit']
        },
        "/dashboard/delete_user/{user_id}":{
            "user": ['read','delete','edit'],
            "admin": ['read','delete','edit']
        }
    }

def convert_method_to_action(request_method: str) -> str:
    method_permission_mapping = {
        "GET": "read",
        "PUT": "edit",
        "DELETE": "delete"
    }
    return method_permission_mapping.get(request_method)

def has_permission(user_role, resource, required_permission):
    if resource in RESOURCES_FOR_ROLES and user_role in RESOURCES_FOR_ROLES[resource]:
        return required_permission in RESOURCES_FOR_ROLES[resource][user_role]
    return False

class RBACMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
      try:
        request_method = str(request.method).upper()
        action = convert_method_to_action(request_method)
        resource = request.url.path
        if resource in EXCLUDED_PATHS:
                return await call_next(request)
        token = request.headers.get("Authorization")
        if token.startswith("Bearer"):
            token = token.split(" ")[1]
            _, role = verify_token(token)
         
        if not has_permission(role, resource, action):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        response = await call_next(request)
        return response
      except HTTPException as exc:
            traceback.print_exc()
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
      except Exception as exc:
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
            if request.url.path in EXCLUDED_PATHS:
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
            traceback.print_exc()
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

app.add_middleware(CustomMiddleware)
app.add_middleware(RBACMiddleware)

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