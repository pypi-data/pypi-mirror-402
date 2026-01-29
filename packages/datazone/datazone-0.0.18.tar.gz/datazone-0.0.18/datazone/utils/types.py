from typing import Any

import pydantic
from bson import ObjectId
from bson.objectid import InvalidId

IS_PYDANTIC_V2 = int(pydantic.VERSION.split(".")[0]) >= 2

if IS_PYDANTIC_V2:
    from pydantic import (
        GetCoreSchemaHandler,
        GetJsonSchemaHandler,
    )
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema, core_schema
    from pydantic_core.core_schema import (
        ValidationInfo,
        str_schema,
    )


class PydanticObjectId(ObjectId):
    """
    Object Id field. Compatible with Pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    if IS_PYDANTIC_V2:

        @classmethod
        def validate(cls, v, _: ValidationInfo):
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            try:
                return PydanticObjectId(v)
            except (InvalidId, TypeError):
                raise ValueError("Id must be of type PydanticObjectId")

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:  # type: ignore
            return core_schema.json_or_python_schema(
                python_schema=core_schema.with_info_plain_validator_function(
                    cls.validate,
                ),
                json_schema=str_schema(),
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda instance: str(instance),
                ),
            )

        @classmethod
        def __get_pydantic_json_schema__(
            cls,
            schema: core_schema.CoreSchema,
            handler: GetJsonSchemaHandler,  # type: ignore
        ) -> JsonSchemaValue:
            json_schema = handler(schema)
            json_schema.update(
                type="string",
                example="5eb7cf5a86d9755df3a6c593",
            )
            return json_schema

    else:

        @classmethod
        def validate(cls, v):  # type: ignore[misc]
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            try:
                return PydanticObjectId(v)
            except InvalidId:
                raise TypeError("Id must be of type PydanticObjectId")

        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(
                type="string",
                example="5eb7cf5a86d9755df3a6c593",
            )
