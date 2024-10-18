from database.database import engine
from database import models
from routers import authentication, dashboard

from fastapi import FastAPI
from fastapi_pagination import add_pagination

app = FastAPI()
add_pagination(app)

import middleware
app.include_router(authentication.router)
app.include_router(dashboard.router)

models.Base.metadata.create_all(bind=engine)

