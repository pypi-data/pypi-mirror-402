# -*- coding: utf-8 -*-
import asyncio
import base64
import hashlib
import hmac
import json
from random import randrange

from v2.nacos import ClientConfig, NacosException
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import (
    INVALID_PARAM,
    INVALID_SERVER_STATUS,
    SERVER_ERROR,
)

from maintainer.common.auth import RequestResource
from maintainer.common.utils import get_current_time_millis
from maintainer.transport.auth_client import AuthClient
from maintainer.transport.http_agent import HttpAgent


class HttpRequest:
    def __init__(
        self,
        path: str,
        method: str,
        request_resource: RequestResource,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
    ):
        self.path = path
        self.method = method
        self.request_resource = request_resource
        if headers is None:
            headers = {}
        self.headers = headers
        if params is None:
            params = {}
        self.params = params
        if data is None:
            data = {}
        self.data = data


class ClientHttpProxy:
    def __init__(
        self,
        logger,
        ai_client_config: ClientConfig,
        http_agent: HttpAgent,
    ):
        self.logger = logger

        if len(ai_client_config.server_list) == 0:
            raise NacosException(
                INVALID_PARAM,
                "both server list and endpoint are empty",
            )

        self.ai_client_config = ai_client_config
        self.server_list = ai_client_config.server_list
        self.current_index = 0
        self.http_agent = http_agent

        self.refresh_server_list_internal = 30  # second
        if len(self.server_list) != 0:
            self.current_index = randrange(0, len(self.server_list))

        if ai_client_config.username and ai_client_config.password:
            self.auth_client = AuthClient(
                self.logger,
                ai_client_config,
                self.get_server_list,
                http_agent,
            )
            asyncio.create_task(self.auth_client.get_access_token(True))

    def get_server_list(self):
        return self.server_list

    def get_next_server(self):
        if not self.server_list:
            raise NacosException(INVALID_SERVER_STATUS, "server list is empty")
        self.current_index = (self.current_index + 1) % len(self.server_list)
        server = self.server_list[self.current_index]

        if ':' not in server.split('//')[-1]:
            server = f"{server}:8848"

        return server

    async def request(self, http_reqeust: HttpRequest):
        end_time = get_current_time_millis() + self.ai_client_config.timeout_ms
        headers = http_reqeust.headers
        resource = http_reqeust.request_resource
        if self.ai_client_config.username and self.ai_client_config.password:
            access_token = await self.auth_client.get_access_token(False)
            if access_token is not None and access_token != "":
                headers[Constants.ACCESS_TOKEN] = access_token

        now = get_current_time_millis()
        credentials = (
            self.ai_client_config.credentials_provider.get_credentials()
        )
        if (
            credentials.get_access_key_id()
            and credentials.get_access_key_secret()
        ):
            if resource.namespace:
                resource = resource.namespace + "+" + resource.group
            else:
                resource = resource.group

            if resource.strip():
                sign_str = f"{resource}+{now}"
            else:
                sign_str = str(now)

            headers.update(
                {
                    "Spas-AccessKey": credentials.get_access_key_id(),
                    "Spas-Signature": base64.encodebytes(
                        hmac.new(
                            credentials.get_access_key_secret().encode(),
                            sign_str.encode(),
                            digestmod=hashlib.sha1,
                        ).digest(),
                    )
                    .decode()
                    .strip(),
                    "Timestamp": str(now),
                },
            )

            if credentials.get_security_token():
                headers[
                    "Spas-SecurityToken"
                ] = credentials.get_security_token()

        retry_count = 3
        nacos_exception = None
        result_code = 200
        error_msg = None
        url = None
        while get_current_time_millis() < end_time and retry_count > 0:
            try:
                url = self.get_next_server() + http_reqeust.path
                resp, err_code, error_msg = await self.http_agent.request(
                    url,
                    http_reqeust.method,
                    headers,
                    http_reqeust.params,
                    http_reqeust.data,
                )
                if not resp or error_msg:
                    self.logger.error(f"request error: {error_msg}")
                    raise NacosException(err_code, error_msg)

                response_data = json.loads(resp.decode("UTF-8"))
                return response_data
            except NacosException as e:
                nacos_exception = e
                result_code = nacos_exception.error_code
            except Exception as e:
                self.logger.error(f"request error: {e}")
                result_code = SERVER_ERROR

            if result_code != 200:
                retry_count -= 1

            await asyncio.sleep(100 / 1000)

        if nacos_exception:
            raise nacos_exception
        raise NacosException(
            SERVER_ERROR,
            f"request error,url:{url},method:{http_reqeust.method},result_code:{result_code},error_msg:{error_msg}",
        )
