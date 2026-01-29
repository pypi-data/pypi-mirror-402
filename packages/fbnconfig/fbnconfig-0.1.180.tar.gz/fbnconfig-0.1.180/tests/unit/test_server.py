import pathlib
import textwrap
from unittest import mock

import httpx
import pytest
from click.testing import CliRunner
from starlette.testclient import TestClient

from server.app import app


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeServer:

    @pytest.fixture()
    def api(self):
        client = TestClient(app)
        client.event_hooks = {"response": [lambda x: x.raise_for_status()]}
        return client

    def test_homepage(self, api):
        response = api.get("/api/fbnconfig/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, Banana!", "status": "success"}

    def test_log(self, api, respx_mock):
        # given lusid has no deployments
        respx_mock.get("/api/api/customentities/~deployment").mock(
            return_value=httpx.Response(200, json={
                "values": []
            })
        )
        # when we request them
        headers = {
            "Authorization": "Bearer BINGOBANGO",
            "X-LUSID-Host": "https://foo.lusid.com",
        }
        response = api.get("/api/fbnconfig/log/something", headers=headers)
        assert response.status_code == 200
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer BINGOBANGO"
        assert request.headers["Host"] == "foo.lusid.com"

    def test_schema(self, api):
        # when we get the schema
        s = api.get("/api/fbnconfig/schema").json()
        # then it has defs and properties at the top level as expected
        assert s
        assert "$defs" in s
        assert "properties" in s

    @pytest.fixture()
    def example_dir(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # given there is one example script in the examples folder
            script = textwrap.dedent("""\
                from fbnconfig import Deployment
                def configure(env):
                    return Deployment('test1', [])
            """)
            example_dir = pathlib.Path.cwd()
            with open("script.py", "w") as f:
                f.write(script)
            yield example_dir

    def test_examples(self, api, example_dir):
        # given a dir with one example script
        # and we mock the server to use it
        with mock.patch("server.app.get_examples_path", return_value=example_dir):
            # when we request examples
            examples = api.get("/api/fbnconfig/examples/").json()
            # there is one example
            assert examples == [{
                "name": "script",
                "path": "/api/fbnconfig/examples/script"
            }]

    def test_one_example(self, api, example_dir):
        # given a dir with one example script
        # and we mock the server to use it
        with mock.patch("server.app.get_examples_path", return_value=example_dir):
            # when we request an example that exists
            example = api.get("/api/fbnconfig/examples/script").json()
            # then we get a json with zero resources
            assert example == {
                "deploymentId": "test1",
                "resources": []
            }
