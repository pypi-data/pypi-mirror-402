import json
import pathlib

import jsonschema
import pytest

from fbnconfig import dump_deployment, schemagen
from fbnconfig.load_module import load_module


@pytest.fixture()
def this_folder():
    return pathlib.Path(__file__).parent.resolve()


@pytest.fixture()
def repo_root(this_folder):
    return this_folder.parent.parent


def test_commited_schema_matches_generated(this_folder):
    new_schema = schemagen.cmd_deployment_schema()
    new_schema_json = json.dumps(new_schema, indent=2)
    schema_path = this_folder.parent.parent / "deployment.schema.json"
    # read the raw json into a dict and re-serialise to remove any whitespace
    # differences
    with open(schema_path, "r") as schema_io:
        old_schema = json.load(schema_io)
    old_schema_json = json.dumps(old_schema, indent=2)
    print("""
        The current json schema is stored in project-root/deployment.schema.json.
        If you have made changes that affect schema generation them it needs to be updated
        and comitted to git.

        uv run fbnconfig/schemagen.py > deployment.schema.json
    """)
    assert new_schema_json == old_schema_json


def pytest_generate_tests(metafunc):
    if "example_path" in metafunc.fixturenames:
        this_dir = pathlib.Path(__file__).parent.resolve()
        repo_dir = this_dir.parent.parent
        examples_dir = repo_dir / "public_examples" / "examples"
        script_paths = examples_dir.glob("*.py")
        metafunc.parametrize("example_path", script_paths)


def test_examples_against_schema(repo_root, example_path):
    host_vars = {}
    module = load_module(example_path, str(example_path.parent))
    d = module.configure(host_vars)
    deployment_json = dump_deployment(d)
    schema_path = repo_root / "deployment.schema.json"
    with open(schema_path, "r") as schema_io:
        schema_json = json.load(schema_io)
    jsonschema.validate(instance=deployment_json, schema=schema_json)
