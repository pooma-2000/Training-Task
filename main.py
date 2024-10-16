from database.database import engine
from database import models
from routers import authentication, dashboard

from fastapi import FastAPI

app = FastAPI()

import middleware
app.include_router(
        authentication.router
        )
app.include_router(
        dashboard.router
        )

models.Base.metadata.create_all(bind=engine)

