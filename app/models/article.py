from app.db.database import Base
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Text


# 文章表
class Article(BaseModel, Base):
    __tablename__ = 'Articles'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="正文")
    summary = Column(String(50), comment="摘要")
    author_id = Column(Integer, index=True, nullable=False, comment="作者ID")
    deleted = Column(Integer, nullable=False, default=1)  # 软删除字段，1为正常，2为删除
