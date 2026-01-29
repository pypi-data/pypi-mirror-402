from typing import ClassVar

from pydantic import BaseModel, Field

from fbnconfig import schemagen
from fbnconfig.resource_abc import CamelAlias, Ref, Resource


class SimpleModel(BaseModel, CamelAlias):
    id: str
    x_value: int
    y_value: int


class TestRef(BaseModel, Ref, CamelAlias):
    id: str
    # this is what the register decorator puts on
    resource_type: ClassVar = "TestRef"
    no_init: str = Field(None, init=False)
    normal_field: str


class TestResource(BaseModel, Resource, CamelAlias):
    id: str
    resource_type: ClassVar = "TestRef"
    simple: SimpleModel
    optional: int | None = None
    unioned: int | str | None = None


def test_simple_model():
    # given a simple (not resource or ref) model, when we generate the schema
    schema = schemagen.schema(SimpleModel)
    assert schema["properties"]
    # it contains the fields in camelCase
    assert schema["properties"]["xValue"]
    assert schema["properties"]["yValue"]
    # it keeps it's id field because it's not a resource
    assert schema["properties"]["id"]
    # the camel fields get converted to a title case title
    assert schema["properties"]["xValue"]["title"] == "X Value"


def test_ref():
    # given a ref class when we generate the schema
    schema = schemagen.schema(TestRef)
    assert schema["properties"]
    # it contains the fields in camelCase
    assert schema["properties"]["normalField"]
    # the id field is removed
    assert schema["properties"].get("id", None) is None
    # the non-init field is marked as readonly
    assert schema["properties"]["noInit"]["readOnly"] is True


def test_resource():
    # given a ref class when we generate the schema
    schema = schemagen.schema(TestResource)
    # the embedded type will get put into $defs
    assert schema["$defs"].get("SimpleModel", None) is not None
    # the primary type will go into the top
    assert schema["properties"]
    assert schema["properties"]["optional"]
    # the anyOf which pydantic puts in for the nullable field is simplified
    assert schema["properties"]["optional"]["type"] == "integer"
    # genuine unions are preserved
    assert schema["properties"]["unioned"]
    assert schema["properties"]["unioned"]["anyOf"]
