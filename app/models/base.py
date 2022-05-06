from datetime import datetime
from sqlalchemy import Column, DateTime


# 时间基类
class BaseModel(object):
    createTime = Column(DateTime, default=datetime.now,
                        nullable=False)  # 记录的创建时间

    def to_dict(self, exclude=[], reverse=True, time_=False):
        """
        1.reverse=True: not in exclude：输出去除该列表里面的字段
        2.reverse=False: in exclude：输出只有该列表里面的字段
        """
        if reverse:
            data = {
                c.name: getattr(self, c.name)
                for c in self.__table__.columns if c.name not in exclude
            }
        else:
            if time_:
                exclude = exclude + ['createTime']
            data = {
                c.name: getattr(self, c.name)
                for c in self.__table__.columns if c.name in exclude
            }
        if 'createTime' in data:
            data['createTime'] = data['createTime'].strftime(
                "%Y-%m-%d %H:%M:%S") if data['createTime'] else ''
        return data
