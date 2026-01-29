# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types.applications import (
    AuthFlowListResponse,
    AuthFlowCreateResponse,
    AuthFlowDeleteResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAuthFlows:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Anchorbrowser) -> None:
        auth_flow = client.applications.auth_flows.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        )
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Anchorbrowser) -> None:
        auth_flow = client.applications.auth_flows.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
            custom_fields=[{"name": "name"}],
            description="Username and password authentication",
            is_recommended=True,
        )
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Anchorbrowser) -> None:
        response = client.applications.auth_flows.with_raw_response.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = response.parse()
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Anchorbrowser) -> None:
        with client.applications.auth_flows.with_streaming_response.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = response.parse()
            assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            client.applications.auth_flows.with_raw_response.create(
                application_id="",
                methods=["username_password"],
                name="Standard Login",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Anchorbrowser) -> None:
        auth_flow = client.applications.auth_flows.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Anchorbrowser) -> None:
        response = client.applications.auth_flows.with_raw_response.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = response.parse()
        assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Anchorbrowser) -> None:
        with client.applications.auth_flows.with_streaming_response.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = response.parse()
            assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            client.applications.auth_flows.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Anchorbrowser) -> None:
        auth_flow = client.applications.auth_flows.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Anchorbrowser) -> None:
        response = client.applications.auth_flows.with_raw_response.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = response.parse()
        assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Anchorbrowser) -> None:
        with client.applications.auth_flows.with_streaming_response.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = response.parse()
            assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            client.applications.auth_flows.with_raw_response.delete(
                auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                application_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `auth_flow_id` but received ''"):
            client.applications.auth_flows.with_raw_response.delete(
                auth_flow_id="",
                application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )


class TestAsyncAuthFlows:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAnchorbrowser) -> None:
        auth_flow = await async_client.applications.auth_flows.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        )
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        auth_flow = await async_client.applications.auth_flows.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
            custom_fields=[{"name": "name"}],
            description="Username and password authentication",
            is_recommended=True,
        )
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.applications.auth_flows.with_raw_response.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = await response.parse()
        assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.applications.auth_flows.with_streaming_response.create(
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            methods=["username_password"],
            name="Standard Login",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = await response.parse()
            assert_matches_type(AuthFlowCreateResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            await async_client.applications.auth_flows.with_raw_response.create(
                application_id="",
                methods=["username_password"],
                name="Standard Login",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAnchorbrowser) -> None:
        auth_flow = await async_client.applications.auth_flows.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.applications.auth_flows.with_raw_response.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = await response.parse()
        assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.applications.auth_flows.with_streaming_response.list(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = await response.parse()
            assert_matches_type(AuthFlowListResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            await async_client.applications.auth_flows.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncAnchorbrowser) -> None:
        auth_flow = await async_client.applications.auth_flows.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.applications.auth_flows.with_raw_response.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth_flow = await response.parse()
        assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.applications.auth_flows.with_streaming_response.delete(
            auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            auth_flow = await response.parse()
            assert_matches_type(AuthFlowDeleteResponse, auth_flow, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `application_id` but received ''"):
            await async_client.applications.auth_flows.with_raw_response.delete(
                auth_flow_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                application_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `auth_flow_id` but received ''"):
            await async_client.applications.auth_flows.with_raw_response.delete(
                auth_flow_id="",
                application_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )
