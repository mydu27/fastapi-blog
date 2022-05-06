import traceback
from typing import Any
from loguru import logger
from app.models import Article
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from sqlalchemy.future import select
from fastapi.encoders import jsonable_encoder
from app.schemas import ArticleCreateBase, ArticleUpdateBase


class CRUDArticle(CRUDBase[Article, ArticleCreateBase, ArticleUpdateBase]):
    """
    query_info={
    'and':{
    'id':1, 'filed1':xxx, 'filed2':xxx,
    },
    page: 1
    page_size: 10,
    order_by: str='id'
    like: 0 or 1
    }
    """
    async def get_(self, db: Session, id: Any):
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        article_obj = result.scalars().first()
        return article_obj

    async def get_filter(self, db: Session, *, query_info={}):
        query_, querys_count = await self.get_filter_base(
            db=db, query_info=query_info)
        query_ = self.filter_page_size_order(query_info=query_info,
                                             query_=query_)
        result = await db.execute(query_)
        article_list = result.scalars().all()
        data = [item.to_dict() for item in article_list]
        paging = {
            'total': querys_count,
            'query_total': len(data),
            'page': query_info['page'],
            'page_size': query_info['page_size']
        }
        return data, paging

    async def create_(self, db: Session, *,
                      obj_in: ArticleCreateBase) -> Article():

        if not isinstance(obj_in, dict):
            obj_in_data = jsonable_encoder(obj_in)
        else:
            obj_in_data = obj_in
        try:
            db_obj = Article(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        except Exception:
            logger.debug(traceback.print_exc())
            await db.rollback()
            db_obj = None
        return db_obj

    async def update_(self, db: Session, info: ArticleUpdateBase) -> Article():
        if not isinstance(info, dict):
            info = info.dict(exclude_unset=True)
        if 'id' not in info:
            print(info)
            return None
        article_obj = await self.get_(db, id=info.get('id'))
        if not article_obj:
            raise HTTPException(status_code=404, detail="文章不存在")
        try:
            info_data = {
                item: info[item]
                for item in info if item not in ['id']
                if info[item] is not None
                if info[item] != article_obj.to_dict()[item]
            }
            for k, v in info_data.items():
                setattr(article_obj, k, v)
            await db.commit()
            await db.refresh(article_obj)
            return article_obj
        except Exception:
            logger.debug(traceback.print_exc())
            await db.rollback()
            return None

    async def delete_(self, db: Session, id: int):
        article_obj = await self.get_(db, id=id)
        if not article_obj:
            raise HTTPException(status_code=404, detail="文章不存在")
        try:
            await db.delete(article_obj)
            await db.commit()
        except Exception:
            logger.debug(traceback.print_exc())
            await db.rollback()
            raise HTTPException(status_code=403, detail="删除失败")


crud_article = CRUDArticle(Article)
