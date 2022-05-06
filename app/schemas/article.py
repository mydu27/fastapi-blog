from pydantic import BaseModel, Field


class ArticleCreateBase(BaseModel):
    title: str = Field(max_length=50)
    content: str
    summary: str = Field(None, max_length=50)
    author_id: int = 1


class ArticleUpdateBase(BaseModel):
    title: str = Field(None, max_length=50)
    content: str = None
    summary: str = Field(None, max_length=50)
