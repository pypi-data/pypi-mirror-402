# mypy: ignore-errors

from typing import Any, Optional, Type

from fastapi import Depends, HTTPException
from pydantic import create_model

from ._types import PAGINATION, T


def schema_factory(
    schema_cls: Type[T], pk_field_name: str = "id", name: str = "Create"
) -> Type[T]:
    """
    Is used to create a CreateSchema which does not contain pk
    """

    fields = {}

    for field_name, field_info in schema_cls.model_fields.items():
        if field_name != pk_field_name:

            annotation = field_info.annotation

            if field_info.is_required():
                fields[field_name] = (annotation, ...)
            else:

                default = field_info.default if field_info.default is not ... else ...
                fields[field_name] = (annotation, default)

    name = schema_cls.__name__ + name

    schema: Type[T] = create_model(name, **fields)
    return schema


def create_query_validation_exception(field: str, msg: str) -> HTTPException:
    return HTTPException(
        422,
        detail={
            "detail": [
                {"loc": ["query", field], "msg": msg, "type": "type_error.integer"}
            ]
        },
    )


def pagination_factory(max_limit: Optional[int] = None) -> Any:
    """
    Created the pagination dependency to be used in the router
    """

    def pagination(skip: int = 0, limit: Optional[int] = max_limit) -> PAGINATION:
        if skip < 0:
            raise create_query_validation_exception(
                field="skip",
                msg="skip query parameter must be greater or equal to zero",
            )

        if limit is not None:
            if limit <= 0:
                raise create_query_validation_exception(
                    field="limit", msg="limit query parameter must be greater than zero"
                )
            elif max_limit and max_limit < limit:
                raise create_query_validation_exception(
                    field="limit",
                    msg=f"limit query parameter must be less than {max_limit}",
                )

        return {"skip": skip, "limit": limit}

    return Depends(pagination)
