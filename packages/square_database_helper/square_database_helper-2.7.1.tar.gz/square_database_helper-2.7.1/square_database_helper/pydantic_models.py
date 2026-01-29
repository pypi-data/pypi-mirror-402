from typing import Any, Dict, Optional, List

from pydantic import BaseModel, RootModel


class FilterConditionsV0(BaseModel):
    eq: Optional[Any] = None
    ne: Optional[Any] = None
    lt: Optional[Any] = None
    lte: Optional[Any] = None
    gt: Optional[Any] = None
    gte: Optional[Any] = None
    like: Optional[str] = None
    in_: Optional[List[Any]] = None
    is_null: Optional[bool] = None


class FiltersV0(RootModel):
    root: Dict[str, FilterConditionsV0]


class InsertRowsV0Response(BaseModel):
    main: List[Dict[str, Any]]
    affected_count: int


class GetRowsV0Response(BaseModel):
    main: List[Dict[str, Any]]
    total_count: int


class EditRowsV0Response(BaseModel):
    main: List[Dict[str, Any]]
    affected_count: int


class DeleteRowsV0Response(BaseModel):
    main: List[Dict[str, Any]]
    affected_count: int
