from main import app
from utilities.auth import verify_token
from database.database import SessionLocal
from database.models import RequestLog, CriticalActionLog, Metrics

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTasks
from starlette.responses import Response


import time
import logging
import traceback
import json

logging.basicConfig(filename='info.log', level=logging.DEBUG)

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)

EXCLUDED_PATHS = ['/docs','/auth/login','/auth/register','/openapi.json', '/favicon.ico']

RESOURCES_FOR_ROLES = {
        "/auth/logout": ["admin","user"],
        "/dashboard/manage_users": ["admin"],
        "/dashboard/user_profile": ["admin","user"],
        "/dashboard/edit_user": ["admin"],
        "/dashboard/delete_user": ["admin"],
        "/dashboard/search_user": ["admin","user"]
    }

# def convert_method_to_action(request_method: str) -> str:
#     method_permission_mapping = {
#         "GET": "read",
#         "PUT": "edit",
#         "DELETE": "delete"
#     }
#     return method_permission_mapping.get(request_method)

def has_permission(user_role, resource):
    if resource in RESOURCES_FOR_ROLES and user_role in RESOURCES_FOR_ROLES[resource]:
        return True
    return False

class RBACMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
      try:
        resource = request.url.path
        if resource in EXCLUDED_PATHS:
                return await call_next(request)
        token = request.headers.get("Authorization")
        if token.startswith("Bearer"):
            token = token.split(" ")[1]
            _, role = verify_token(token)
         
        if not has_permission(role, resource):
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
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="UnAuthorized"
                )
            if token.startswith("Bearer"):
                token = token.split(" ")[1] 
            
            if not verify_token(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Token"
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


from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
import traceback
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        db: Session = None
        try:
            db = SessionLocal()

            req_body = await request.body()

            response = await call_next(request)

            request_log = RequestLog(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            db.add(request_log)

            res_body = b''
            async for chunk in response.body_iterator:
                res_body += chunk

            if request.url.path in ["/auth/login"]:
                action = "login"

                try:
                    response_body = res_body.decode('utf-8')
                    response_json = json.loads(response_body)
                    user_id = response_json.get("user_id")

                    if user_id:
                        critical_log = CriticalActionLog(
                            user_id=user_id,
                            action=action
                        )
                        db.add(critical_log)
                except (json.JSONDecodeError, KeyError):
                    traceback.print_exc()

            # Update metrics
            metrics = db.query(Metrics).first()
            if not metrics:
                metrics = Metrics()
                db.add(metrics)

            if request.url.path == "/auth/login":
                metrics.login_attempts += 1
            elif request.url.path == "/dashboard/edit_user":
                metrics.profile_updates += 1

            db.commit()

            background_task = BackgroundTasks()
            background_task.add_task(log_info, req_body.decode('utf-8'), res_body.decode('utf-8'))

            return Response(
                content=res_body, 
                status_code=response.status_code, 
                headers=dict(response.headers), 
                media_type=response.media_type,
                background=background_task
            )
        
        except HTTPException as exc:
            traceback.print_exc()
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        
        except Exception as exc:
            traceback.print_exc()
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=500)

app.add_middleware(CustomMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(LoggingMiddleware)

# @app.middleware('http')
# async def logging_middleware(request: Request, call_next):
#     try:
#         req_body = await request.body()
#         res_body = b''
#         async for chunk in request.stream():
#             req_body += chunk

#         response = await call_next(request)
#         res_body = b''
#         async for chunk in response.body_iterator:
#             res_body += chunk

        