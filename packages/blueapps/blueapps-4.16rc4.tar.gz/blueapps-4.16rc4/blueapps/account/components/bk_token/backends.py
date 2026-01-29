# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import logging
import traceback

from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError

from blueapps.account import get_user_model
from blueapps.account.components.bk_token.verification_strategy import TokenVerifier

logger = logging.getLogger("component")

ROLE_TYPE_ADMIN = "1"

TOKEN_TYPE = "bk_token"


class TokenBackend(ModelBackend):
    def authenticate(self, request=None, bk_token=None):
        logger.debug("Enter in TokenBackend")
        # 判断是否传入验证所需的bk_token,没传入则返回None
        if not bk_token:
            return None

        verify_result, username = self.verify_bk_token(bk_token)
        # 判断bk_token是否验证通过,不通过则返回None
        if not verify_result:
            return None

        user_model = get_user_model()
        try:
            user, _ = user_model.objects.get_or_create(username=username)
            get_user_info_result, user_info = self.get_user_info(bk_token)
            # 判断是否获取到用户信息,获取不到则返回None
            if not get_user_info_result:
                return None

            user.display_name = user_info.get("display_name", "")
            user.tenant_id = user_info.get("tenant_id", "")

            # 用户如果不是管理员，则需要判断是否存在平台权限，如果有则需要加上
            if not user.is_superuser and not user.is_staff:
                role = user_info.get("role", "")
                is_admin = True if str(role) == ROLE_TYPE_ADMIN else False
                user.is_superuser = is_admin
                user.is_staff = is_admin
                user.save()

            return user

        except IntegrityError:
            logger.exception(traceback.format_exc())
            logger.exception("get_or_create UserModel fail or update_or_create UserProperty")
            return None
        except Exception:  # pylint: disable=broad-except
            logger.exception(traceback.format_exc())
            logger.exception("Auto create & update UserModel fail")
            return None

    @staticmethod
    def get_user_info(bk_token):
        """
        请求平台ESB接口获取用户信息
        @param bk_token: bk_token
        @type bk_token: str
        @return:True, {
            u'message': u'\u7528\u6237\u4fe1\u606f\u83b7\u53d6\u6210\u529f',
            u'code': 0,
            u'data': {
                u'qq': u'',
                u'wx_userid': u'',
                u'language': u'zh-cn',
                u'username': u'test',
                u'time_zone': u'Asia/Shanghai',
                u'role': 2,
                u'phone': u'11111111111',
                u'email': u'test',
                u'chname': u'test'
            },
            u'result': True,
            u'request_id': u'eac0fee52ba24a47a335fd3fef75c099'
        }
        @rtype: bool,dict
        """
        verifier = TokenVerifier()
        return verifier.get_user_info(bk_token)

    def verify_bk_token(self, bk_token):
        """
        请求VERIFY_URL,认证bk_token是否正确
        @param bk_token: "_FrcQiMNevOD05f8AY0tCynWmubZbWz86HslzmOqnhk"
        @type bk_token: str
        @return: False,None True,username
        @rtype: bool,None/str
        """
        verifier = TokenVerifier()
        return verifier.verify_bk_token(bk_token)
