from typing import Dict, Any, Optional, List, overload, Literal

from square_commons.api_utils import make_request, StandardResponse

from square_database_helper.pydantic_models import (
    FiltersV0,
    InsertRowsV0Response,
    GetRowsV0Response,
    EditRowsV0Response,
    DeleteRowsV0Response,
)


class SquareDatabaseHelper:
    def __init__(
        self,
        param_int_square_database_port: int = 10010,
        param_str_square_database_ip: str = "localhost",
        param_str_square_database_protocol: str = "http",
    ):
        try:
            self.global_str_square_database_url_base = (
                f"{param_str_square_database_protocol}://"
                f"{param_str_square_database_ip}:{param_int_square_database_port}"
            )
        except Exception:
            raise

    def _make_request(
        self, method, endpoint, json=None, data=None, params=None, headers=None
    ):
        try:
            return make_request(
                method=method,
                url=self.global_str_square_database_url_base,
                endpoint=endpoint,
                json=json,
                data=data,
                params=params,
                headers=headers,
                return_type="json",
            )
        except Exception:
            raise

    @overload
    def insert_rows_v0(
        self,
        data: List[Dict[str, Any]],
        database_name: str,
        schema_name: str,
        table_name: str,
        skip_conflicts: bool = False,
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[InsertRowsV0Response]: ...

    @overload
    def insert_rows_v0(
        self,
        data: List[Dict[str, Any]],
        database_name: str,
        schema_name: str,
        table_name: str,
        skip_conflicts: bool = False,
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def insert_rows_v0(
        self,
        data: List[Dict[str, Any]],
        database_name: str,
        schema_name: str,
        table_name: str,
        skip_conflicts: bool = False,
        response_as_pydantic: bool = False,
    ) -> Any:
        try:
            endpoint = "insert_rows/v0"
            payload = {
                "data": data,
                "database_name": database_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "skip_conflicts": skip_conflicts,
            }
            response = self._make_request("POST", endpoint, json=payload)
            if response_as_pydantic:
                return StandardResponse[InsertRowsV0Response](**response)
            else:
                return response
        except Exception:
            raise

    @overload
    def get_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        columns: Optional[List[str]] = None,
        order_by: List[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[GetRowsV0Response]: ...

    @overload
    def get_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        columns: Optional[List[str]] = None,
        order_by: List[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def get_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        columns: Optional[List[str]] = None,
        order_by: List[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        response_as_pydantic: bool = False,
    ) -> Any:
        if order_by is None:
            order_by = []
        try:
            endpoint = "get_rows/v0"
            payload = {
                "database_name": database_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "filters": filters.model_dump(),
                "apply_filters": apply_filters,
                "columns": columns,
                "order_by": order_by,
                "limit": limit,
                "offset": offset,
            }
            response = self._make_request("POST", endpoint, json=payload)
            if response_as_pydantic:
                return StandardResponse[GetRowsV0Response](**response)
            else:
                return response
        except Exception:
            raise

    @overload
    def edit_rows_v0(
        self,
        data: Dict[str, Any],
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[EditRowsV0Response]: ...

    @overload
    def edit_rows_v0(
        self,
        data: Dict[str, Any],
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def edit_rows_v0(
        self,
        data: Dict[str, Any],
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: bool = False,
    ) -> Any:
        try:
            endpoint = "edit_rows/v0"
            payload = {
                "data": data,
                "filters": filters.model_dump(),
                "database_name": database_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "apply_filters": apply_filters,
            }
            response = self._make_request("PATCH", endpoint, json=payload)
            if response_as_pydantic:
                return StandardResponse[EditRowsV0Response](**response)
            else:
                return response
        except Exception:
            raise

    @overload
    def delete_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[InsertRowsV0Response]: ...

    @overload
    def delete_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def delete_rows_v0(
        self,
        filters: FiltersV0,
        database_name: str,
        schema_name: str,
        table_name: str,
        apply_filters: bool = True,
        response_as_pydantic: bool = False,
    ) -> Any:
        try:
            endpoint = "delete_rows/v0"
            payload = {
                "filters": filters.model_dump(),
                "database_name": database_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "apply_filters": apply_filters,
            }
            response = self._make_request("POST", endpoint, json=payload)
            if response_as_pydantic:
                return StandardResponse[DeleteRowsV0Response](**response)
            else:
                return response
        except Exception:
            raise
