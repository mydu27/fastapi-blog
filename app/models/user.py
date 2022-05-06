from app.db.database import Base
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Text


# 用户表
class Users(BaseModel, Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), index=True, nullable=False, comment="姓名")
    sex = Column(String(32), index=True, nullable=True, comment="性别")
    email = Column(String(50), comment="邮箱")
    password = Column(Text, nullable=False, comment="密码")
    superuser = Column(Integer,
                       default=False,
                       nullable=False,
                       comment="是否是超级管理员")
    deleted = Column(Integer, nullable=False, default=1)  # 软删除字段，1为正常，2为删除
