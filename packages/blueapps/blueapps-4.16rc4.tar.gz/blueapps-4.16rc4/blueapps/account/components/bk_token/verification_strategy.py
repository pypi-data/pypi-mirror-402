import json
import logging
import os
from abc import ABC, abstractmethod

import requests
from django.conf import settings

from blueapps import metrics
from blueapps.account.conf import ConfFixture
from blueapps.account.utils.http import send
from blueapps.core.exceptions.base import MethodError
from blueapps.utils import client
from blueapps.utils.tools import resolve_login_url

logger = logging.getLogger("component")

ROLE_TYPE_ADMIN = "1"

TOKEN_TYPE = "bk_token"


def get_apigw_url(api_name: str, path: str, stage: str = "prod") -> str:
    """
    生成网关url
    """
    endpoint = f"{settings.BK_API_URL_TMPL.format(api_name=api_name)}/{stage}"
    url = f"{endpoint}{path}"
    return url


def make_apigw_request(api_name, path, method="GET", params=None, data=None, json_data=None):
    """
    通用的网关API请求函数，通过指定的API名称和路径发送请求
    """
    url = get_apigw_url(api_name, path)
    headers = {
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": settings.APP_CODE, "bk_app_secret": settings.SECRET_KEY})
    }

    # 网关对于请求头的租户ID强校验，全租户应用默认补充default
    if os.getenv("BKPAAS_APP_TENANT_ID") == "":
        headers.update({"X-Bk-Tenant-Id": "default"})

    # 根据HTTP方法选择请求方式
    request_method = getattr(requests, method.lower(), requests.get)

    response = request_method(url=url, headers=headers, params=params, data=data, json=json_data)
    return response


class VerificationStrategy(ABC):
    @abstractmethod
    def verify_token(self, bk_token):
        """验证给定的令牌"""
        pass

    @abstractmethod
    def get_user_info(self, bk_token):
        """获取用户信息"""
        pass


class APIGWVerificationStrategy(VerificationStrategy):
    api_name = "bk-login"
    login_path = "/login/api/v3/open/bk-tokens/verify/"
    user_info_path = "/login/api/v3/open/bk-tokens/userinfo/"

    def verify_token(self, bk_token):
        try:
            with metrics.observe(
                metrics.BLUEAPPS_USER_TOKEN_VERIFY_DURATION,
                hostname=metrics.HOSTNAME,
                token_type=TOKEN_TYPE,
            ):
                api_params = {"bk_token": bk_token}
                response = make_apigw_request(self.api_name, self.login_path, "GET", api_params)
        except (NotImplementedError, MethodError, AttributeError):
            raise
        except Exception:  # pylint: disable=broad-except
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME,
                token_type=TOKEN_TYPE,
                err="unknow_execption_raise",
            ).inc()
            logger.exception("Abnormal error in verify_bk_token...")
            return False, None

        if response.status_code == 200:
            response = response.json()
            data = response.get("data")
            username = data.get("bk_username")
            return True, username
        else:
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME, token_type=TOKEN_TYPE, err="verify_fail"
            ).inc()
            response = response.json()
            error = response.get("error", "")
            if error:
                error_msg = error.get("message", "")
                error_data = error.get("data", "")
                logger.error("Fail to verify bk_token, error={}, ret={}".format(error_msg, error_data))
            return False, None

    def get_user_info(self, bk_token):
        api_params = {"bk_token": bk_token}
        try:
            response = make_apigw_request(
                self.api_name,
                self.user_info_path,
                method="GET",
                params=api_params,
            )
        except Exception as err:  # pylint: disable=broad-except
            logger.exception("Abnormal error in get_user_info...:%s" % err)
            return False, {}
        if response.status_code == 200:
            response = response.json()
            origin_user_info = response.get("data", "")
            user_info = dict()
            user_info["wx_userid"] = origin_user_info.get("wx_userid", "")
            user_info["language"] = origin_user_info.get("language", "")
            user_info["time_zone"] = origin_user_info.get("time_zone", "")
            user_info["phone"] = origin_user_info.get("phone", "")
            user_info["chname"] = origin_user_info.get("chname", "")
            user_info["email"] = origin_user_info.get("email", "")
            user_info["qq"] = origin_user_info.get("qq", "")
            user_info["tenant_id"] = origin_user_info.get("tenant_id", "")
            user_info["display_name"] = origin_user_info.get("display_name", "")
            user_info["username"] = origin_user_info.get("bk_username", "")
            user_info["role"] = origin_user_info.get("bk_role", "")
            return True, user_info
        else:
            response = response.json()
            error = response.get("error", "")
            error_msg = error.get("message", "")
            error_data = error.get("data", "")
            logger.error("Failed to Get User Info: error=%(err)s, ret=%(ret)s" % {"err": error_msg, "ret": error_data})
            return False, {}


class ESBVerificationStrategy(VerificationStrategy):
    def verify_token(self, bk_token, request=None):
        try:
            return self.verify_bk_token_through_esb(bk_token)
        except (NotImplementedError, MethodError, AttributeError):
            # 对应版本 esb 不支持 client.bk_login.is_login 接口的情况
            return self.verify_bk_token_through_verify_url(bk_token, request)

    def verify_bk_token_through_esb(self, bk_token):
        api_params = {"bk_token": bk_token}

        try:
            with metrics.observe(
                metrics.BLUEAPPS_USER_TOKEN_VERIFY_DURATION,
                hostname=metrics.HOSTNAME,
                token_type=TOKEN_TYPE,
            ):
                response = client.bk_login.is_login(api_params)
        except (NotImplementedError, MethodError, AttributeError):
            raise
        except Exception:  # pylint: disable=broad-except
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME,
                token_type=TOKEN_TYPE,
                err="unknow_execption_raise",
            ).inc()
            logger.exception("Abnormal error in verify_bk_token...")
            return False, None

        if response.get("result"):
            data = response.get("data")
            username = data.get("bk_username")
            return True, username
        else:
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME, token_type=TOKEN_TYPE, err="verify_fail"
            ).inc()
            error_msg = response.get("message", "")
            error_data = response.get("data", "")
            logger.error("Fail to verify bk_token, error={}, ret={}".format(error_msg, error_data))
            return False, None

    def verify_bk_token_through_verify_url(self, bk_token, request=None):
        api_params = {"bk_token": bk_token}

        try:
            with metrics.observe(
                metrics.BLUEAPPS_USER_TOKEN_VERIFY_DURATION, hostname=metrics.HOSTNAME, token_type=TOKEN_TYPE
            ):
                response = send(
                    resolve_login_url(ConfFixture.VERIFY_URL, request, "http"),
                    "GET",
                    api_params,
                    verify=False,
                )
        except Exception:  # pylint: disable=broad-except
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME, token_type=TOKEN_TYPE, err="unknow_execption_raise"
            ).inc()
            logger.exception("Abnormal error in verify_bk_token...")
            return False, None

        if response.get("result"):
            data = response.get("data")
            username = data.get("username")
            return True, username
        else:
            metrics.BLUEAPPS_USER_TOKEN_VERIFY_FAILED_TOTAL.labels(
                hostname=metrics.HOSTNAME, token_type=TOKEN_TYPE, err="verify_fail"
            ).inc()
            error_msg = response.get("message", "")
            error_data = response.get("data", "")
            logger.error("Fail to verify bk_token, error={}, ret={}".format(error_msg, error_data))
            return False, None

    def get_user_info(self, bk_token):
        api_params = {"bk_token": bk_token}
        try:
            response = client.bk_login.get_user(api_params)
        except Exception as err:  # pylint: disable=broad-except
            logger.exception("Abnormal error in get_user_info...:%s" % err)
            return False, {}
        if response.get("result") is True:
            origin_user_info = response.get("data", "")
            user_info = dict()
            user_info["wx_userid"] = origin_user_info.get("wx_userid", "")
            user_info["language"] = origin_user_info.get("language", "")
            user_info["time_zone"] = origin_user_info.get("time_zone", "")
            user_info["phone"] = origin_user_info.get("phone", "")
            user_info["chname"] = origin_user_info.get("chname", "")
            user_info["email"] = origin_user_info.get("email", "")
            user_info["qq"] = origin_user_info.get("qq", "")
            user_info["tenant_id"] = origin_user_info.get("tenant_id", "")
            user_info["display_name"] = origin_user_info.get("display_name", "")
            user_info["username"] = origin_user_info.get("bk_username", "")
            user_info["role"] = origin_user_info.get("bk_role", "")
            return True, user_info
        else:
            error_msg = response.get("message", "")
            error_data = response.get("data", "")
            logger.error("Failed to Get User Info: error=%(err)s, ret=%(ret)s" % {"err": error_msg, "ret": error_data})
            return False, {}


# 策略上下文
class TokenVerifier:
    def __init__(self):
        enable_multi_tenant_mode = os.getenv("BKPAAS_MULTI_TENANT_MODE", "false").lower() == "true"
        # 根据开关选择具体的策略类
        if enable_multi_tenant_mode:
            self.strategy = APIGWVerificationStrategy()
        else:
            self.strategy = ESBVerificationStrategy()

    def verify_bk_token(self, bk_token):
        return self.strategy.verify_token(bk_token)

    def get_user_info(self, bk_token):
        return self.strategy.get_user_info(bk_token)
