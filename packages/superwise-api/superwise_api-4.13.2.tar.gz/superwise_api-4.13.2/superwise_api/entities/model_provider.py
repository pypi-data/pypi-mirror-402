from typing import Optional

from pydantic import conint

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.model_provider.model_provider import (
    ModelProvider,
    PrebuiltProviderStatus,
    ProviderCreateConfig,
)


class ModelProviderApi(BaseApi):
    _model_name = "model_provider"
    _resource_path = "/v1/model-providers"
    _model_class = ModelProvider

    def create(
        self,
        name: str,
        config: ProviderCreateConfig,
        **kwargs,
    ) -> ModelProvider:
        """
        Create a new model provider.

        Args:
            name: The name of the model provider.
            config: The config of the model provider.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The created model provider.
        """
        response_types_map = {
            "201": self._model_class,
            "401": "HTTPUnauthorized",
            "422": "HTTPValidationError",
        }
        payload = {
            "name": name,
            "config": config,
        }
        return self.api_client.post(
            resource_path=self._resource_path,
            model_name=self._model_name,
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def get_by_id(
        self,
        model_provider_id: str,
        with_deleted: bool = False,
        **kwargs,
    ) -> ModelProvider:
        """
        Get a model provider by id.

        Args:
            model_provider_id: The id of the model provider.
            with_deleted: Whether to include deleted model providers.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The model provider.
        """
        query_params = {"with_deleted": with_deleted}
        return super().get_by_id(_id=model_provider_id, query_params=query_params, **kwargs)

    def get(
        self,
        search: Optional[str] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=25)] = None,
        with_deleted: bool = False,
        **kwargs,
    ) -> Page:
        """
        Gets model providers. Filter if any of the parameters are provided.

        Args:
            search (str, optional): The search query.
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            with_deleted: Whether to include deleted model providers.
        Returns:
            Page: A page of model providers.
        """

        query_params = {
            k: v
            for k, v in dict(
                search=search,
                page=page,
                size=size,
                with_deleted=with_deleted,
            ).items()
            if v is not None
        }

        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        model_provider_id: str,
        name: Optional[str] = None,
        **kwargs,
    ) -> ModelProvider:
        """
        Update a model provider.

        Args:
            model_provider_id: The id of the model provider.
            name: The name of the model provider.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The updated model provider.
        """

        payload = {
            "name": name,
        }
        data = {k: v for k, v in payload.items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            entity_id=model_provider_id,
            data=data,
            **kwargs,
        )

    def delete(
        self,
        model_provider_id: str,
        **kwargs,
    ) -> None:
        """
        Delete a model provider.

        Args:
            model_provider_id: The id of the model provider.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """
        return super().delete(_id=model_provider_id, **kwargs)

    def prebuilt_provider_status(self, **kwargs) -> PrebuiltProviderStatus:
        """
        Get the status of the prebuilt model providers.

        Returns:
            The status of the prebuilt model providers.
        """
        response_types_map = {
            "200": PrebuiltProviderStatus,
            "401": "HTTPUnauthorized",
        }

        header_params = kwargs.pop("_headers", {}).copy()
        header_params["Accept"] = self.api_client.select_header_accept(["application/json"])
        auth_settings = ["implicit"]

        return self.api_client.call_api(
            resource_path=f"{self._resource_path}/prebuilt-provider/status",
            method="GET",
            header_params=header_params,
            query_params={},
            auth_settings=auth_settings,
            response_types_map=response_types_map,
            **kwargs,
        )
