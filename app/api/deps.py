from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request, Header

from jose import jwt
from datetime import datetime
from pydantic import ValidationError
from sqlalchemy.orm import Session
from resources import strings as base
from app import crud, models, schemas
from core.config import settings
from db.database import get_db
from db.database import cache
from core.security import YunAuthJWT
from doc.permissions_key import UsersPermissions

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token")


# 根据token获取用户对象类
class CURRENTUSER(object):
    def __init__(self,
                 db: Session = Depends(get_db),
                 token: str = Depends(reusable_oauth2)):
        self.db = db
        self.token = token

    def get_current_user(self) -> models.Users:
        """user obj"""
        try:
            payload = jwt.decode(self.token,
                                 settings.FIXED_SECRET_KEY,
                                 algorithms=[settings.ALGORITHM])
            token_data = schemas.TokenPayload(**payload)
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法验证token",
            )
        user = crud.user.get(self.db, id=token_data.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_current_active_user(
        self,
        current_user: models.Users = Depends(get_current_user),
    ) -> models.Users:
        """active user obj"""
        if not crud.user.is_active(current_user):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    def get_current_active_superuser(
        self,
        current_user: models.Users = Depends(get_current_user),
    ) -> models.Users:
        """superuser user obj"""
        if not crud.user.superuser(current_user):
            raise HTTPException(
                status_code=400,
                detail="The user doesn't have enough privileges")
        return current_user


# 验证、权限类
class APIVERIFY(object):
    def __init__(self, fixed_content: str = None):
        self.fixed_content = fixed_content

    def _verify_expire_time_in_token(self, token: str):
        """验证token过期"""
        playload = YunAuthJWT().analysis_token(token=token)
        if datetime.now().timestamp() > playload['exp'] - 28800:
            return None
        return True

    def _get_token_type_jti(self, token: str):
        """获取token类型"""
        playload = YunAuthJWT().analysis_token(token=token)
        return playload['type'], playload['jti']

    async def __call__(self,
                       request: Request,
                       token: str = Header(None),
                       db: Session = Depends(get_db)):
        """
        token验证+权限验证+Cookies验证
        TODO:
        目前权限方式未定
        """
        if not token:
            raise HTTPException(status_code=404, detail="token为空,请登入")
        else:
            if not cache.exists(token):
                raise HTTPException(status_code=401,
                                    detail="token已失效,请登入")  # 令牌头无效(redis过期)
            verify_token_result = self._verify_expire_time_in_token(
                token=token)
            if verify_token_result is None:
                raise HTTPException(status_code=401,
                                    detail="此token已过期,请登入")  # 令牌头过期(配置时间过期)
            token_type, token_jti = self._get_token_type_jti(token=token)
            if token_type == base.TOKEN_REFRESH:
                raise HTTPException(status_code=401,
                                    detail="无效token")  # refresh token 无权访问接口
            token_key = cache.get(token)
            # 验证第三方
            if token_jti == base.JTI_SERVER:
                third_obj = db.query(models.ThirdPartyServiceId).filter_by(
                    clientId=token_key.decode(encoding='UTF-8')).first()
                if not third_obj:
                    raise HTTPException(status_code=401,
                                        detail="此token下的第三方已失效,请重新获取token")
                return True
            # 验证用户
            if token_jti == base.JTI_USER:
                user_id = token_key
                user_obj = db.query(
                    models.Users).filter_by(id=int(user_id)).first()
                if not user_obj:
                    raise HTTPException(status_code=401,
                                        detail="此token下的用户已失效,请登入")  # 令牌头无效
                if user_obj.flag != 0:
                    raise HTTPException(status_code=401,
                                        detail="已{}".format(
                                            base.flag_map[user_obj.flag]))
                if user_obj.superuser:
                    return True
                else:
                    if "Cookies" not in request.headers:
                        raise HTTPException(status_code=404,
                                            detail="Cookies为空,请登入")
                    orgcode = (request.headers['Cookies']).split('=')[1]
                    orgcode_list = crud.user.get_user_orgcode(db, int(user_id))
                    if not orgcode_list and user_obj.superuser != 1:
                        raise HTTPException(status_code=404,
                                            detail="此机构未与用户绑定，请询问管理员")
                    if orgcode not in orgcode_list:
                        raise HTTPException(status_code=404,
                                            detail="此机构未与用户绑定，请询问管理员")
                    org_ = crud.crud_org.get_(db, orgcode)
                    if org_.flag > 0:
                        raise HTTPException(status_code=404,
                                            detail="此机构已被{}，请询问管理员".format(
                                                base.flag_map[org_.flag]))
                if self.fixed_content:
                    print(self.fixed_content)
                    if token_jti == base.JTI_USER:
                        if user_obj.superuser:
                            return True
                        loginOrg_msg = crud.user.get_user_roles(
                            db, orgcode, user_id)
                        pers_list = loginOrg_msg['permissionsList']
                        if pers_list:
                            if self.fixed_content in pers_list:
                                return True
                            else:
                                try:
                                    hint = UsersPermissions[self.fixed_content]
                                except KeyError:
                                    hint = self.fixed_content
                                raise HTTPException(
                                    status_code=407,
                                    detail="无'{}'操作权限".format(hint))
                        raise HTTPException(status_code=407, detail="请添加操作权限")


# 管理页面
# 关于验证、权限类
class APIVERIFYSUPER(object):
    def __init__(self):
        pass

    def _verify_expire_time_in_token(self, token: str):
        """验证token过期"""
        playload = YunAuthJWT().analysis_token(token=token)
        # playload['exp']为时间戳格式
        if datetime.now().timestamp() > playload['exp']:
            return None
        return True

    async def get_token_header(self,
                               request: Request,
                               token: str = Header(None),
                               db: Session = Depends(get_db)):
        """
        token验证+权限验证
        TODO:
        目前权限方式未定
        """
        if not token:
            raise HTTPException(status_code=404, detail="token为空,请登入")
        else:
            if not cache.exists(token):
                raise HTTPException(status_code=401,
                                    detail="token已失效,请登入")  # 令牌头无效
            verify_token_result = self._verify_expire_time_in_token(
                token=token)
            if verify_token_result == None:
                raise HTTPException(status_code=401,
                                    detail="此token已过期,请登入")  # 令牌头过期(配置时间过期)
            user_id = cache.get(token)
            user_obj = db.query(
                models.Users).filter_by(id=int(user_id)).first()
            if not user_obj:
                raise HTTPException(status_code=401,
                                    detail="此token下的用户已失效,请登入")  # 令牌头无效
            if user_obj.flag != 0:
                raise HTTPException(status_code=401,
                                    detail="此账号已{}".format(
                                        base.flag_map[user_obj.flag]))
            if not user_obj.superuser:
                raise HTTPException(status_code=407,
                                    detail="未授权此操作")  # 不是超级管理员
