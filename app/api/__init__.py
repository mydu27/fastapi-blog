from fastapi import APIRouter
from .endpoints import article, users

api_router = APIRouter()

api_router.include_router(article.router, prefix="/article", tags=["article"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
