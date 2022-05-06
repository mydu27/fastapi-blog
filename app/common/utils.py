import rsa
import pathlib
import random
import uuid, time
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from core.config import settings
from db.database import cache
from core import security
from core.security import YunAuthJWT
from models.study import Study
from resources import strings as base
from models.user import OrgUserRoles, \
    Organizations, RolesPermission, Permissions, Roles, UsersRecords

yunauth = YunAuthJWT()


#处理对象中有时间类型的datetime转换成str ‘2020-01-01 12:12:12’
def change_datetime_format(obj):
    if 'createTime' in obj:
        if isinstance(obj['create_time'], str) and obj['create_time']:
            timestamps = obj['create_time'].split('T')
            obj['create_time'] = ''.join(timestamps[0]) + ' ' + timestamps[1]

    if 'updateTime' in obj:
        if isinstance(obj['update_time'], str) and obj['update_time']:
            timestamps = obj['update_time'].split('T')
            obj['update_time'] = ''.join(timestamps[0]) + ' ' + timestamps[1]

    return obj


def get_token_key(request, user):
    """获取当前后台登录用户的token_key"""
    token_key = ''
    referer = False
    for row in request.headers.raw:
        # print(row)
        if bytes.decode(row[0]) == 'token':
            token_key = bytes.decode(row[1])
        if bytes.decode(row[0]) == 'referer':
            referer_str = bytes.decode(row[1])
            # print(referer_str, referer_str.split('/'),'3333333333333')
            referer = True if referer_str.split(
                '/')[2] == 'cloud.vote_docs' else False
    # print(token_key)
    if referer:
        # token_key = 'token' + encrypt_password(str(15950378016551623))
        access_token_expires = timedelta(
            seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_key = security.YunAuthJWT().create_token(
            user.id, expires_delta=access_token_expires)
        # print(token_key,'...........')
    return token_key


def get_current_user_token(request: Request):
    """获取当前后台登录用户"""
    token_key = get_token_key(request)
    return eval(cache.get(token_key))


#第二种获得当前登录用户的token
def from_redis_token(kw: str):
    res = cache.scan_iter("*")
    for i in res:
        key = cache.get(i)
        if key.decode(encoding='UTF-8') == str(kw):
            if isinstance(i, bytes):
                return i.decode(encoding='UTF-8', errors='strict')


#将模型形式的list转成[{},{}]
def return_data_type(queryset):
    if queryset:
        if hasattr(queryset[0], "to_dict"):
            return {"list": [v.to_dict() for v in queryset]}
        else:
            return {"list": [v for v in queryset]}
    else:
        return {"list": []}


# 获取uuid
def get_uuid():
    uid = str(uuid.uuid4())
    u_id = ''.join(uid.split('-'))
    return u_id


#根据机构名称和日期得到code
#########获取中文字符的拼音简写#######
def single_get_first(unicode1):
    str1 = unicode1.encode('gbk')
    try:
        ord(str1)
        return str1
    except:
        asc = str1[0] * 256 + str1[1] - 65536
        if asc >= -20319 and asc <= -20284:
            return 'a'
    if asc >= -20283 and asc <= -19776:
        return 'b'
    if asc >= -19775 and asc <= -19219:
        return 'c'
    if asc >= -19218 and asc <= -18711:
        return 'd'
    if asc >= -18710 and asc <= -18527:
        return 'e'
    if asc >= -18526 and asc <= -18240:
        return 'f'
    if asc >= -18239 and asc <= -17923:
        return 'g'
    if asc >= -17922 and asc <= -17418:
        return 'h'
    if asc >= -17417 and asc <= -16475:
        return 'j'
    if asc >= -16474 and asc <= -16213:
        return 'k'
    if asc >= -16212 and asc <= -15641:
        return 'l'
    if asc >= -15640 and asc <= -15166:
        return 'm'
    if asc >= -15165 and asc <= -14923:
        return 'n'
    if asc >= -14922 and asc <= -14915:
        return 'o'
    if asc >= -14914 and asc <= -14631:
        return 'p'
    if asc >= -14630 and asc <= -14150:
        return 'q'
    if asc >= -14149 and asc <= -14091:
        return 'r'
    if asc >= -14090 and asc <= -13119:
        return 's'
    if asc >= -13118 and asc <= -12839:
        return 't'
    if asc >= -12838 and asc <= -12557:
        return 'w'
    if asc >= -12556 and asc <= -11848:
        return 'x'
    if asc >= -11847 and asc <= -11056:
        return 'y'
    if asc >= -11055 and asc <= -10247:
        return 'z'
    return ''


def getPinyin(string):
    in_string = "~!@#$%^&*()_+-*/<>,.[]\/"
    if string == None:
        return None
    lst = list(string)
    charLst = []
    for l in lst:
        if l in in_string or ' ' in l:
            raise HTTPException(status_code=404, detail="机构名称不得含有特殊符号")
        values = single_get_first(l)
        if isinstance(values, bytes):
            values = str(int(values))
        charLst.append(values)
    year = datetime.now().strftime("%Y")
    day = datetime.now().strftime("%m%d")
    return ''.join(charLst) + '_' + year + '_' + day


#获取Headers中的Cookies中的orgcode
def get_cookie_orgcode(request):
    return (request.headers['Cookies']).split('=')[1]


#读取.env环境变量
def read_env(file):
    env_path = pathlib.Path(file)
    d = {}
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                d[key] = value.strip("'")
    return d


#-------------------------***第三方***-------------------------
#随机获得key
def get_appId():
    str1 = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
    code = ''
    for i in range(4):
        num = random.randint(0, len(str1) - 1)
        code += str1[num]
    return code


#获取两个token
def third_get_token(clientId):
    access_token_expires = timedelta(
        seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = yunauth.create_token(clientId,
                                        expires_delta=access_token_expires,
                                        token_type="access",
                                        jti="user")
    refresh_token_expires = timedelta(
        seconds=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = yunauth.create_token(clientId,
                                         expires_delta=refresh_token_expires,
                                         token_type="refresh",
                                         jti="thirdServer")
    return access_token, refresh_token


#根据用户获取机构名称
def get_user_orgname(db: Session, user_id, code):
    if code:
        orguserroles = db.query(OrgUserRoles).filter(
            OrgUserRoles.userId == int(user_id),
            OrgUserRoles.organizationCode == code).all()
    else:
        orguserroles = db.query(OrgUserRoles).filter(
            OrgUserRoles.userId == int(user_id)).all()
    orgcode = list(set([item.organizationCode for item in orguserroles]))
    roleid = list(set([item.roleId for item in orguserroles]))
    orgname = [(db.query(Organizations).filter(
        Organizations.code == item).first()).title for item in orgcode]
    rolename = [(db.query(Roles).filter(Roles.id == item).first()).title
                for item in roleid]
    return orgname, rolename


#获取用户所有权限
def get_user_permissions(db: Session, user_id):
    orguserroles = db.query(OrgUserRoles).filter(
        OrgUserRoles.userId == int(user_id)).all()
    roleid_list = list(set([item.roleId for item in orguserroles]))
    if len(roleid_list) <= 0:
        return []
    persid_list = [(db.query(RolesPermission).filter(
        RolesPermission.roleId == item).first()).permissionId
                   for item in roleid_list]
    permissions_list = [
        item.title for item in (db.query(Permissions).filter(
            Permissions.id.in_(persid_list)).all())
    ]
    return permissions_list


#从header authorization bearer 中获得token
def get_authorization_token(request):
    from typing import Tuple

    def get_authorization_scheme_param(
            authorization_header_value: str) -> Tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme, param

    authorization: str = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    return scheme, param


#获取n天前的日期
def get_date(beforeday):
    today = datetime.now()
    # 计算偏移量
    offset = timedelta(days=-beforeday)
    # 获取想要的日期的时间
    re_date = (today + offset).strftime('%Y-%m-%d %H:%M:%S')
    return re_date


#删除超过时间的用户记录信息
def delete_timeout_records(db, user_id):
    before = get_date(settings.DELETE_TIMEOUT_DAY)
    querys = db.query(UsersRecords).filter(UsersRecords.createTime <= before,
                                           UsersRecords.userId == user_id)
    querys.delete()
    try:
        db.commit()
        db.close()
    except:
        db.rollback()
        return False
    return True


#病例模块获取病人信息
def get_patinets_data(db, case_list):
    for item in case_list:
        user_obj = crud.user.get(db=db, id=item['userId'])
        study_obj = db.query(Study).filter(Study.id == item["studyId"]).first()
        if study_obj:
            study_data = jsonable_encoder(study_obj)
        else:
            study_data = {}
        item['study_info'] = study_data
        item['operator'] = user_obj.name
    return case_list


import os
from resources import strings as base


#存储图片
class CustUploadFile():
    @staticmethod
    def upload(file, file_read, save_path=None, p_name=None):
        # 判断文件夹是否定义
        if not ('STATIC_DIR' in vars(base)) and not ('FILE_PATH'
                                                     in vars(base)):
            raise HTTPException(status_code=403, detail="请在配置中添加文件存储路径")
        # 文件大小
        if (file.spool_max_size / 1024 / 1024) > base.HEAD_SIZE:
            raise HTTPException(status_code=403,
                                detail='上传的文件不能大于{}m'.format(base.HEAD_SIZE))

        name = p_name + '_' if p_name else 'head_'

        # 插入的真实路径
        on_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        insert_file_path_no = os.path.join(
            os.path.join(on_path, 'static_vote'), base.STATIC_DIR)
        # 插入表的字段的路径
        file_name = name + str(time.time()).split('.')[0] + str(random.randrange(1, 999, 3)) + '.' + \
                    file.filename.split('.')[len(file.filename.split('.')) - 1]

        # 获取静态文件夹的目录
        if not save_path:
            insert_file_path = os.path.join(insert_file_path_no, file_name)
            # 返回前端供入库的路径
            file_path = os.path.join(file_name)
        else:
            save_path = save_path[1:] if save_path[0] == '/' or save_path[
                0] == '\\' else save_path
            insert_file_path = os.path.join(
                os.path.join(insert_file_path_no, save_path))
            if not os.path.exists(insert_file_path):
                os.makedirs(insert_file_path)
            insert_file_path = os.path.join(insert_file_path, file_name)
            file_path = os.path.join(os.path.join(save_path, file_name))
        isExists = os.path.exists(insert_file_path_no)

        if not isExists:  # 路径不存在，即文件名不存在
            os.makedirs(insert_file_path_no)
        try:
            with open(insert_file_path, 'wb') as f:
                f.write(file_read)
        except:
            raise HTTPException(status_code=500, detail="上传失败")
        return (file_path).replace('\\', '/')


#公钥加密
def encrypt(mess):
    # 生成密钥
    # public_key, private_key = rsa.newkeys(1024)
    # pub = public_key.save_pkcs1()
    # pri = private_key.save_pkcs1('PEM')
    #
    # with open('pubkey.pem', mode='wb') as f, open('privkey.pem', mode='wb')  as f1:
    #     f.write(pub)
    #     f1.write(pri)

    publickey = rsa.PublicKey.load_pkcs1(base.pub)
    info = rsa.encrypt(mess.encode('utf-8'), publickey)
    return info


def decript(text):
    privatekey = rsa.PrivateKey.load_pkcs1(base.pri)
    msg = rsa.decrypt(text, privatekey)
    print(msg.decode('utf-8'))
    return msg.decode('utf-8')
