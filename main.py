from database.database import engine
from fastapi import FastAPI
from database import models
from routers import api
# from fastapi_auth_middleware import AuthMiddleware, FastAPIUser


app = FastAPI()

import middleware
app.include_router(api.router)

models.Base.metadata.create_all(bind=engine)

