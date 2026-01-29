import json
import re
from typing import Any, Dict, List, Union

import click
from pydantic import BaseModel, json_schema

from fbnconfig.resource_abc import RESOURCE_REGISTRY, CamelAlias


def create_resource_union():
    resource_classes = tuple(info["class"] for info in RESOURCE_REGISTRY.values())
    return Union[resource_classes]


# this is the class that will define the types that go into the schema
ResourceOrRef = create_resource_union()


class Resource(BaseModel, CamelAlias):
    resource_id: str
    resource_type: str
    value: ResourceOrRef  # pyright: ignore[reportInvalidTypeForm]


class Deployment(BaseModel, CamelAlias):
    deployment_id: str
    resources: List[Resource]


class CustomSchemaGenerator(json_schema.GenerateJsonSchema):

    def model_schema(self, schema):
        model_class = schema["cls"]
        json_schema = super().model_schema(schema)
        # if it has been registered as a resource/ref remove the id field
        if getattr(model_class, "resource_type", None):
            json_schema["properties"].pop("id", None)
            json_schema["required"] = [i for i in json_schema["required"] if i != "id"]
        # for each json property, lookup the corresponding field in the python class
        for prop_name, prop in json_schema["properties"].items():
            field_match = [
                m for k, m in model_class.model_fields.items()
                if m.serialization_alias == prop_name
            ]
            if len(field_match) == 1:
                model_field = field_match[0]
                # if its not an init field, mark it as readonly so the ui can hide it
                if model_field.init is False:
                    json_schema["properties"][prop_name]["readOnly"] = True
        return json_schema

    def get_title_from_name(self, name):
        return camel_to_sentence(name)


def camel_to_sentence(inp):
    if len(inp) == 0:
        return inp
    output = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", inp)
    output = output[0].upper() + output[1:]
    return output


def simplify_prop(k, p):
    # if it is an anyOf remove any nulls
    if p.get("anyOf", None):
        options = [e for e in p["anyOf"] if e.get("type", None) != "null"]
        if len(options) == 1:
            p = p | options[0]
            p.pop("anyOf")
        if len(options) > 1:
            p = p | {"anyOf": options}
    # any allOf with only one element can be flattened
    if p.get("allOf", None) and len(p["allOf"]) == 1:
        p = p | p["allOf"][0]
        p.pop("allOf")
    # # create a title if there isn't one
    p = p | {"title": camel_to_sentence(k)}
    return p


def simplify_def(d):
    if d.get("properties"):
        new_props = {k: simplify_prop(k, p) for k, p in d["properties"].items()}
        d = d | {"properties": new_props}
    return d


def sanitize(schema: Dict[str, Any]) -> Dict[str, Any]:
    # top level properties
    schema = simplify_def(schema)
    # embedded defs
    defs = schema.get("$defs", None)
    if defs is None:
        return schema
    new_defs = {k: simplify_def(d) for k, d in defs.items()}
    return schema | {"$defs": new_defs}


class RegexOption(click.ParamType):
    name = "regex"

    def convert(self, value, param, ctx):
        try:
            return re.compile(value)
        except re.error as e:
            self.fail(f"Invalid regex: {e}", param, ctx)


@click.command()
@click.option("-m", "--mini-schemas", is_flag=True)
@click.option("-p", "--pattern", type=RegexOption(),
              help="Regexp to filter the mini-schema resource types")
def main(mini_schemas, pattern):
    if mini_schemas:
        schema = cmd_mini_schemas(pattern)
    else:
        schema = cmd_deployment_schema()
    print(json.dumps(schema, indent=2))


def schema(klass):
    schema = klass.model_json_schema(
        mode="validation",
        ref_template="#/$defs/{model}",
        schema_generator=CustomSchemaGenerator
    )
    return sanitize(schema)


def cmd_mini_schemas(pattern):
    return {
        key: schema(v["class"])
        for key, v in RESOURCE_REGISTRY.items()
        if pattern.match(key)
    }


def cmd_deployment_schema():
    return schema(Deployment)


if __name__ == "__main__":
    main()
