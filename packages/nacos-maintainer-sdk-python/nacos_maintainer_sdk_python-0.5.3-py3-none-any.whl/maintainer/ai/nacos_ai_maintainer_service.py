# -*- coding: utf-8 -*-
from typing import List, Tuple

from a2a.types import AgentCard
from pydantic import TypeAdapter
from v2.nacos import ClientConfig
from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo
from v2.nacos.ai.model.mcp.mcp import (
    McpServerBasicInfo,
    McpServerDetailInfo,
    McpToolSpecification,
    McpEndpointSpec,
)
from v2.nacos.common.constants import Constants

from maintainer.ai.model.a2a import AgentVersionDetail, AgentCardVersionInfo
from maintainer.common.auth import RequestResource
from maintainer.nacos_maintainer_client import NacosMaintainerClient
from maintainer.transport.client_http_proxy import ClientHttpProxy, HttpRequest


DEFAULT_NAMESPACE_ID = "public"


class NacosAIMaintainerService(NacosMaintainerClient):
    def __init__(self, ai_client_config: ClientConfig):
        super().__init__(ai_client_config, Constants.AI_MODULE)
        self.http_proxy = ClientHttpProxy(
            self.logger,
            ai_client_config,
            self.http_agent,
        )

    @staticmethod
    async def create_mcp_service(client_config: ClientConfig):
        return await NacosAIMaintainerService.create_ai_service(client_config)

    @staticmethod
    async def create_ai_service(client_config: ClientConfig):
        return NacosAIMaintainerService(client_config)

    async def list_mcp_servers(
        self,
        namespace_id: str,
        mcp_name: str,
        page_no: int,
        page_size: int,
    ) -> Tuple[int, int, int, List[McpServerBasicInfo]]:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "pageNo": page_no,
            "pageSize": page_size,
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
            "search": "accurate",
        }
        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            None,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp/list",
            method="GET",
            request_resource=request_resource,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"list ai servers failed, result:{result}")
            raise Exception(result["message"])

        result_data = result["data"]
        total_count = result_data["totalCount"]
        page_number = result_data["pageNumber"]
        page_available = result_data["pagesAvailable"]
        page_items = result_data["pageItems"]
        try:
            adapter = TypeAdapter(List[McpServerBasicInfo])
            mcp_servers: List[McpServerBasicInfo] = adapter.validate_python(
                page_items,
            )
        except Exception as e:
            self.logger.error(e)
            raise

        return total_count, page_number, page_available, mcp_servers

    async def search_mcp_server(
        self,
        namespace_id: str,
        mcp_name: str,
        page_no: int,
        page_size: int,
    ) -> Tuple[int, int, int, List[McpServerBasicInfo]]:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "pageNo": page_no,
            "pageSize": page_size,
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
            "search": "blur",
        }
        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            None,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp/list",
            method="GET",
            request_resource=request_resource,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"search ai server failed, result:{result}")
            raise Exception(result["message"])

        result_data = result["data"]
        total_count = result_data["totalCount"]
        page_number = result_data["pageNumber"]
        page_available = result_data["pagesAvailable"]
        page_items = result_data["pageItems"]
        try:
            adapter = TypeAdapter(List[McpServerBasicInfo])
            mcp_servers: List[McpServerBasicInfo] = adapter.validate_python(
                page_items,
            )
        except Exception as e:
            self.logger.error(e)
            raise
        return total_count, page_number, page_available, mcp_servers

    async def get_mcp_server_detail(
        self,
        namespace_id: str,
        mcp_name: str,
        version: str,
    ) -> McpServerDetailInfo:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
            "version": version,
        }
        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            mcp_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp",
            method="GET",
            request_resource=request_resource,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"get mcp server detail failed, result:{result}")
            raise Exception(result["message"])

        result_data = result["data"]
        try:
            adapter = TypeAdapter(McpServerDetailInfo)
            mcp_server: McpServerDetailInfo = adapter.validate_python(
                result_data,
            )
        except Exception as e:
            self.logger.error(e)
            raise
        return mcp_server

    async def create_mcp_server(
        self,
        namespace_id: str,
        mcp_name: str,
        server_spec: McpServerBasicInfo,
        tool_spec: McpToolSpecification,
        endpoint_spec: McpEndpointSpec,
    ) -> bool:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
            "serverSpecification": server_spec.model_dump_json(
                exclude_none=True,
            ),
        }
        if tool_spec is not None:
            params["toolSpecification"] = tool_spec.model_dump_json(
                exclude_none=True,
            )
        if endpoint_spec is not None:
            params["endpointSpecification"] = endpoint_spec.model_dump_json(
                exclude_none=True,
            )

        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            mcp_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp",
            method="POST",
            request_resource=request_resource,
            data=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"create mcp server failed, result:{result}")
            return False

        return True

    async def update_mcp_server(
        self,
        namespace_id: str,
        mcp_name: str,
        is_latest: bool,
        server_spec: McpServerBasicInfo,
        tool_spec: McpToolSpecification,
        endpoint_spec: McpEndpointSpec,
    ):
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
            "latest": is_latest,
            "serverSpecification": server_spec.model_dump_json(
                exclude_none=True,
            ),
        }
        if tool_spec is not None:
            params["toolSpecification"] = tool_spec.model_dump_json(
                exclude_none=True,
            )
        if endpoint_spec is not None:
            params["endpointSpecification"] = endpoint_spec.model_dump_json(
                exclude_none=True,
            )

        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            mcp_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp",
            method="PUT",
            request_resource=request_resource,
            data=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"update mcp server failed, result:{result}")
            return False

        return True

    async def delete_mcp_server(
        self,
        namespace_id: str,
        mcp_name: str,
    ) -> bool:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "namespaceId": namespace_id,
            "mcpName": mcp_name,
        }
        request_resource = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            mcp_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/mcp",
            method="DELETE",
            request_resource=request_resource,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"delete mcp server failed, result:{result}")
            return False

        return True

    async def register_agent(
        self,
        agent_card: AgentCard,
        namespace_id: str,
        registration_type: str,
    ) -> bool:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID

        params = {
            "agentCard": agent_card.model_dump_json(),
            "namespaceId": namespace_id,
            "agentName": agent_card.name,
            "registrationType": registration_type,
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            agent_card.name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a",
            method="POST",
            request_resource=request_source,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"register agent failed, result:{result}")
            return False

        return True

    async def get_agent_card(
        self,
        agent_name: str,
        version:str,
        namespace_id: str,
        registration_type: str,
    ) -> AgentCardDetailInfo:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID

        params = {
            "agentName": agent_name,
            "version": version,
            "namespaceId": namespace_id,
            "registrationType": registration_type,
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            agent_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a",
            method="GET",
            request_resource=request_source,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"get agent card failed, result:{result}")
            raise Exception(result["message"])

        result_data = result["data"]
        try:
            adapter = TypeAdapter(AgentCardDetailInfo)
            agent_card_detail_info: AgentCardDetailInfo = (
                adapter.validate_python(
                    result_data,
                )
            )
        except Exception as e:
            self.logger.error(e)
            raise
        return agent_card_detail_info

    async def update_agent_card(
        self,
        agent_card: AgentCard,
        namespace_id: str,
        set_as_latest: bool,
        registration_type: str,
    ) -> bool:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID

        params = {
            "agentCard": agent_card.model_dump_json(),
            "namespaceId": namespace_id,
            "agentName": agent_card.name,
            "setAsLatest": set_as_latest,
            "registrationType": registration_type,
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            agent_card.name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a",
            method="PUT",
            request_resource=request_source,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"update agent card failed, result:{result}")
            return False

        return True

    async def delete_agent(
        self,
        agent_name: str,
        namespace_id: str,
        version: str,
    ) -> bool:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID

        params = {
            "agentName": agent_name,
            "namespaceId": namespace_id,
            "version": version,
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            agent_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a",
            method="DELETE",
            request_resource=request_source,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"delete agent failed, result:{result}")
            return False

        return True

    async def list_all_version_of_agent(
        self,
        agent_name: str,
        namespace_id: str,
    ) -> List[AgentVersionDetail]:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID

        params = {
            "agentName": agent_name,
            "namespaceId": namespace_id,
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            agent_name,
        )
        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a/version/list",
            method="GET",
            request_resource=request_source,
            params=params,
        )
        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(
                f"list all version of agent failed, result:{result}",
            )
            raise Exception(result["message"])

        result_data = result["data"]
        try:
            adapter = TypeAdapter(List[AgentVersionDetail])
            agent_version_detail_list: List[
                AgentVersionDetail
            ] = adapter.validate_python(
                result_data,
            )
        except Exception as e:
            self.logger.error(e)
            raise
        return agent_version_detail_list

    async def search_agent_cards_by_name(
        self,
        namespace_id: str,
        agent_name_pattern: str,
        page_no: int,
        page_size: int,
    ) -> Tuple[int, int, int, List[AgentCardVersionInfo]]:
        return await self._list_or_search_agent_cards_by_name(
            namespace_id,
            agent_name_pattern,
            page_no,
            page_size,
            True,
        )

    async def list_agent_cards_by_name(
        self,
        namespace_id: str,
        agent_name: str,
        page_no: int,
        page_size: int,
    ) -> Tuple[int, int, int, List[AgentCardVersionInfo]]:
        return await self._list_or_search_agent_cards_by_name(
            namespace_id,
            agent_name,
            page_no,
            page_size,
            False,
        )

    async def _list_or_search_agent_cards_by_name(
        self,
        namespace_id: str,
        agent_name: str,
        page_no: int,
        page_size: int,
        is_blur: bool,
    ) -> Tuple[int, int, int, List[AgentCardVersionInfo]]:
        if namespace_id is None or len(namespace_id) == 0:
            namespace_id = DEFAULT_NAMESPACE_ID

        params = {
            "namespaceId": namespace_id,
            "agentName": agent_name,
            "pageNo": page_no,
            "pageSize": page_size,
            "search": "blur" if is_blur else "accurate",
        }

        request_source = RequestResource(
            Constants.AI_MODULE,
            namespace_id,
            "",
            None,
        )

        request = HttpRequest(
            path="/nacos/v3/admin/ai/a2a/list",
            method="GET",
            request_resource=request_source,
            params=params,
        )

        result = await self.http_proxy.request(request)
        if result["code"] != 0:
            self.logger.error(f"list agent cards failed, result:{result}")
            raise Exception(result["message"])

        result_data = result["data"]
        total_count = result_data["totalCount"]
        page_number = result_data["pageNumber"]
        page_available = result_data["pagesAvailable"]
        page_items = result_data["pageItems"]
        try:
            adapter = TypeAdapter(List[AgentCardVersionInfo])
            agent_card_version_info_list: List[
                AgentCardVersionInfo
            ] = adapter.validate_python(
                page_items,
            )
        except Exception as e:
            self.logger.error(e)
            raise

        return (
            total_count,
            page_number,
            page_available,
            agent_card_version_info_list,
        )
