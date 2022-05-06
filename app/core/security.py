import time, rsa
from datetime import datetime, timedelta
from typing import Any, Union

from loguru import logger
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
from resources import strings as base
from pydantic import ValidationError
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token")


# 封装JWT
class YunAuthJWT:
    def __init__(self):
        self._access_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_expire = settings.REFRESH_TOKEN_EXPIRE_MINUTES
        self._ALGORITHM = settings.ALGORITHM
        self._secret_key = settings.FIXED_SECRET_KEY
        self._TOKEN_TYPE = base.TOKEN_TYPE
        self._JTI = base.JTI

    def get_expire_time(self, key):
        if key == "access":
            _expire = self._access_expire
        else:
            _expire = self._refresh_expire
        return _expire

    def get_password_hash(self, password: str) -> str:
        """加密密码"""
        decript_password = self.decript(password)
        return pwd_context.hash(decript_password)

    def verify_password(self, plain_password: str,
                        hashed_password: str) -> bool:
        """验证密码与hash密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @logger.catch
    def create_token(self,
                     subject: Union[str, Any],
                     token_type: str,
                     jti: str,
                     expires_delta: timedelta = None) -> str:
        """
        token生成的方法:
        sub: jwt所面向的用户
        exp: jwt的过期时间
        iat: jwt的签发时间
        type: token类型
        jti: token是否是第三方还是客户端的标识
        """

        if token_type not in self._TOKEN_TYPE:
            raise TypeError("token类型错误")
        if jti not in self._JTI:
            raise TypeError("token类型错误")

        # expire 为过期时间
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            _expire = self.get_expire_time(key=token_type)
            expire = datetime.now() + timedelta(seconds=_expire)
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "iat": datetime.now(),
            "type": token_type,
            "jti": jti
        }
        # 加密生成token
        encoded_jwt = jwt.encode(to_encode,
                                 self._secret_key,
                                 algorithm=self._ALGORITHM)
        return encoded_jwt

    def analysis_token(self, token: str) -> dict:
        """解token"""
        try:
            payload = jwt.decode(token,
                                 self._secret_key,
                                 algorithms=[self._ALGORITHM])
        except (jwt.JWTError, ValidationError) as e:
            logger.debug(e)
            raise HTTPException(status_code=403, detail="token无效")
        return payload

    def verify_access_token(self, token: str) -> bool:
        """验证access token"""
        payload = self.analysis_token(token)
        if payload['jti'] == "thirdServer" and payload['type'] == "access":
            return True
        return False
