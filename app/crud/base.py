from sqlalchemy import func
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.base_class import Base
from sqlalchemy.future import select
from fastapi.encoders import jsonable_encoder

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self,
                  db: Session,
                  *,
                  skip: int = 0,
                  limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def filter_page_size_order(self, query_info, query_):
        if query_info['page'] and query_info['page_size']:
            start = (int(query_info['page']) - 1) * int(
                query_info['page_size'])
            if query_info['order_by']:
                if '-' in query_info['order_by']:
                    query_ = query_.order_by(
                        getattr(
                            self.model,
                            (query_info['order_by'].split('-')
                             )[1]).desc().nulls_last()).limit(
                                 int(query_info['page_size'])).offset(start)
                else:
                    query_ = query_.order_by(
                        getattr(
                            self.model,
                            query_info['order_by']).asc().nulls_last()).limit(
                                int(query_info['page_size'])).offset(start)
            else:
                query_ = query_.limit(int(
                    query_info['page_size'])).offset(start)
        return query_

    async def get_filter_base(self,
                              db: Session,
                              *,
                              query_info: dict = None,
                              id: int = None):
        query_ = None
        if query_info:
            query_curd = []
            if 'and' in query_info and query_info['and']:
                query_info['and'] = {
                    item: query_info['and'][item]
                    for item in query_info['and'] if query_info['and'][item]
                }
                for item in query_info['and']:
                    if query_info['and'][item] and getattr(
                            self.model, item, None):
                        query_curd.append(
                            getattr(self.model, item) == query_info['and']
                            [item])
            if 'like' in query_info and query_info['like']:
                for item in query_info['like']:
                    if query_info['like'][item] and getattr(
                            self.model, item, None):
                        query_curd.append(
                            getattr(self.model, item).ilike("%{0}%".format(
                                query_info['like'][item])))
            if 'time_range' in query_info and query_info['time_range']:
                query_curd.append(
                    self.model.createTime >=
                    query_info['time_range']['create_st'],
                    self.model.createTime <=
                    query_info['time_range']['create_et'])
            query_ = select(self.model).where(*query_curd)
            querys_count_sql = select(func.count(
                self.model.id)).where(self.model.deleted == 1)
            result = await db.execute(querys_count_sql)
            querys_count = result.scalars().fetchall()[0]
            return query_, querys_count
        else:
            if id:
                results = select(self.model).where(self.model.id == id,
                                                   self.model.deleted == 1)
                return results, 1
            else:
                results = select(self.model)
                querys_count_sql = select(func.count(
                    self.model.id)).where(self.model.deleted == 1)
                result = await db.execute(querys_count_sql)
                querys_count = result.scalars().fetchall()[0]
                return results, querys_count

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType,
               obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
