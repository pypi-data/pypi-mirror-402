from __future__ import annotations

from dataclasses import dataclass, fields

from httpx import Response

from .constants import API_BASE_URL, MAPPER, SortBy, SortDirection
from .filters import FilterOptions
from .session import SystembolagetClient


@dataclass(frozen=True)
class QueryParam:
    name: str
    value: str | int


@dataclass(frozen=True)
class SystembolagetAPI:
    client: SystembolagetClient

    def _get(self, path: str, params: list[QueryParam]) -> Response:
        response = self.client.get(
            f"{API_BASE_URL}/{path}",
            params=[(param.name, param.value) for param in params],
        )
        response.raise_for_status()
        return response

    def search(
        self,
        query: str | None = None,
        options: FilterOptions = FilterOptions(),
        sort_by: SortBy | None = None,
        sort_direction: SortDirection | None = None,
    ) -> dict:
        params = []

        if query:
            params.append(QueryParam(MAPPER["query"], query))
        if sort_by:
            params.append(QueryParam(MAPPER["sort_by"], sort_by))
        if sort_direction:
            params.append(QueryParam(MAPPER["sort_direction"], sort_direction))

        for field in fields(options):
            value = getattr(options, field.name)
            if value is None:
                continue

            if isinstance(value, bool):
                value = "true" if value else "false"

            api_param_name = MAPPER[field.name]

            if isinstance(value, list):
                params.extend([QueryParam(api_param_name, str(v)) for v in value])
            else:
                params.append(QueryParam(api_param_name, str(value)))

        response = self._get(
            "sb-api-ecommerce/v1/productsearch/search",
            params=params,
        )
        response.raise_for_status()
        return response.json()
