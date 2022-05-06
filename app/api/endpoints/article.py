import traceback
from loguru import logger
from datetime import datetime
from app import crud, schemas
from app.db.database import get_db
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()


@router.get('/{id}')
async def get_article(id: int, *, db: Session = Depends(get_db)):
    """查询单篇文章"""
    article_obj = await crud.crud_article.get_(db, id=id)
    if not article_obj:
        raise HTTPException(status_code=404, detail="文章不存在")
    content = {
        'code': 200,
        'msg': '查询成功',
        'data': article_obj.to_dict(exclude=['deleted'])
    }
    return JSONResponse(status_code=200, content=content)


@router.get('')
async def get_article_list(*,
                           db: Session = Depends(get_db),
                           deleted: int = 1,
                           order_by: str = '-createTime',
                           page: int = 1,
                           page_size: int = 10,
                           title: str = None,
                           create_st: str = None,
                           create_et: str = None):
    """查询单篇文章"""
    if (not create_st and create_et) or (create_st and not create_et):
        raise HTTPException(status_code=400, detail="时间参数不完整")
    if create_st:
        try:
            create_st = datetime.strptime(create_st, "%Y-%m-%d %H:%M:%S")
            create_et = datetime.strptime(create_et, "%Y-%m-%d %H:%M:%S")
        except Exception:
            logger.debug(traceback.print_exc())
            raise HTTPException(status_code=401, detail="查询时间参数错误")
        else:
            if create_et < create_st:
                raise HTTPException(status_code=400, detail="起始时间不能大于截止时间")
    info = {
        'and': {
            'deleted': deleted
        },
        'page': page,
        'page_size': page_size,
        'order_by': order_by,
        'like': {
            'title': title
        },
        'time_range': None if not create_st else {
            'create_st': create_st,
            'create_et': create_et
        },
    }
    data, paging = await crud.crud_article.get_filter(db=db, query_info=info)
    content = {'code': 200, 'msg': '查询成功', 'data': data, 'paging': paging}
    return JSONResponse(status_code=200, content=content)


@router.post('')
async def add_article(*,
                      db: Session = Depends(get_db),
                      article_info: schemas.ArticleCreateBase = None):
    """添加文章"""
    article_obj = await crud.crud_article.create_(db, obj_in=article_info)
    if not article_obj:
        raise HTTPException(status_code=403, detail="创建失败")
    content = {
        'code': 200,
        'msg': '添加成功',
        'data': article_obj.to_dict(exclude=['deleted'])
    }
    return JSONResponse(status_code=200, content=content)


@router.put('/{id}')
async def update_article(id: int,
                         *,
                         db: Session = Depends(get_db),
                         update_info: schemas.ArticleUpdateBase = None):
    """更新文章"""
    if not update_info:
        raise HTTPException(status_code=400, detail="修改参数不能为空")
    update_info_dict = update_info.dict()
    update_info_dict['id'] = id
    update_obj = await crud.crud_article.update_(db, info=update_info_dict)
    if not update_obj:
        raise HTTPException(status_code=403, detail="修改失败")
    return JSONResponse(status_code=200, content={'code': 200, 'msg': '修改成功'})


@router.delete('/{id}')
async def delete_article(id: int, *, db: Session = Depends(get_db)):
    """删除文章"""
    await crud.crud_article.delete_(db, id=id)
    return JSONResponse(status_code=200, content={'code': 200, 'msg': '删除成功'})
