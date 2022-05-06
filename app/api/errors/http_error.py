from typing import Union
from loguru import logger
from fastapi import HTTPException
from fastapi import Request, status
from pydantic import ValidationError
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


# 不符合传参规则错误 统一处理
async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError],
):
    """pydantic错误处理"""
    msg = exc.errors()[0].get('msg')
    try:
        err_field = ''
        for x in exc.errors():
            err_field += x['loc'][1] + ','
        err = '({}) '.format(err_field[0:-1]) + msg
        err = '({}) '.format(err_field[0:-1]) + '字段错误，请重新填写'
        logger.debug(err)
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content={
                                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                                'msg': err
                            })
    except IndexError:
        err = '{} '.format(msg)
        logger.debug(err)
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content={
                                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                                'msg': err
                            })
    except TypeError:
        err = '{} '.format(msg)
        logger.debug(err)
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content={
                                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                                'msg': "请求体格式错误"
                            })


# 正常错误返回 统一处理
async def http_error_handler(
        request: Request, exc: Union[HTTPException,
                                     RequestValidationError]) -> JSONResponse:
    """全局错误处理"""
    code = exc.status_code
    msg = exc.detail
    logger.debug(msg)
    return JSONResponse(content={"code": code, 'msg': msg})
