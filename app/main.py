from fastapi import FastAPI
from app.api.user import router as user_router
from app.api.post import router as post_router

app = FastAPI()

app.include_router(user_router)
app.include_router(post_router)