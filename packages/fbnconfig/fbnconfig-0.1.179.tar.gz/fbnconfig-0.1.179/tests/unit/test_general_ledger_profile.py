import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import general_ledger_profile as glp
from fbnconfig.fund_accounting import ChartOfAccountsRef

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    return response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeGeneralLedgerProfile:

    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def create_chart_of_accounts():
        return ChartOfAccountsRef(
            id="test_chart",
            scope="test_scope",
            code="test_coa_code"
        )

    def test_create(self, respx_mock):
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_code = "test_general_ledger_code"

        respx_mock.post(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile"
        ).mock(return_value=httpx.Response(200, json={}))

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code=general_ledger_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        state = sut.create(self.client)

        expected_body = {
            "generalLedgerProfileCode": general_ledger_code,
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
              {
                  "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                  "levels": ["EconomicBucket"]
              }
        ]

        }

        assert state["scope"] == scope
        assert state["code"] == coa_code
        assert state["general_ledger_profile_code"] == general_ledger_code
        assert "content_hash" in state
        assert "mappings_hash" in state

        request = respx_mock.calls.last.request

        assert request.method == "POST"
        assert request.url.path == f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile"

        request_body = json.loads(request.content)

        assert request_body == expected_body

    def test_read(self, respx_mock):
        """Test reading an existing general ledger profile"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_profile_code = "test_general_ledger_code"

        mock_response = {
            "chartOfAccountsId": {
                "scope": scope,
                "code": coa_code
            },
            "generalLedgerProfileCode": general_ledger_profile_code,
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
                {
                    "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    "levels": ["EconomicBucket"]
                }
            ]
        }

        respx_mock.get(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code=general_ledger_profile_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        old_state = SimpleNamespace(
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=general_ledger_profile_code
        )

        result = sut.read(self.client, old_state)

        assert result == mock_response
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == (
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        )

    def test_read_not_found(self, respx_mock):
        """Test reading a non-existent general ledger profile"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_profile_code = "nonexistent_glp"

        respx_mock.get(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        ).mock(return_value=httpx.Response(404, json={"error": "Not found"}))

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code=general_ledger_profile_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        old_state = SimpleNamespace(
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=general_ledger_profile_code
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            sut.read(self.client, old_state)

        assert exc_info.value.response.status_code == 404

        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == (
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        )

    def test_update(self, respx_mock):
        """Test update when mappings change - should call PUT mappings endpoint"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_profile_code = "test_general_ledger_code"

        # Mock PUT for mappings update
        respx_mock.put(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}/mappings"
        ).mock(return_value=httpx.Response(200, json={}))

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code=general_ledger_profile_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                ),
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'CASH'",
                    levels=["Asset"]
                )
            ]
        )

        desired = sut.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"id", "scope", "code", "chart_of_accounts", "general_ledger_profile_mappings"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()

        old_mappings = [
            {
                "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                "levels": ["EconomicBucket"]
            }
        ]
        old_mappings_json = json.dumps(old_mappings, sort_keys=True)
        old_mappings_hash = sha256(old_mappings_json.encode()).hexdigest()

        old_state = SimpleNamespace(
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=general_ledger_profile_code,
            content_hash=content_hash,
            mappings_hash=old_mappings_hash
        )
        state = sut.update(self.client, old_state)

        assert state is not None
        assert state["scope"] == scope
        assert state["code"] == coa_code
        assert state["general_ledger_profile_code"] == general_ledger_profile_code
        assert "content_hash" in state
        assert "mappings_hash" in state

        # Should only call PUT mappings endpoint
        assert len(respx_mock.calls) == 1
        put_request = respx_mock.calls[0].request
        assert put_request.method == "PUT"
        assert put_request.url.path == (
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}/mappings"
        )

    def test_update_with_scope_or_code_change(self, respx_mock):
        """Test that changing scope or code triggers delete and recreate"""
        old_scope = "old_scope"
        old_coa_code = "old_coa_code"
        new_scope = "new_scope"
        new_coa_code = "new_coa_code"
        general_ledger_profile_code = "test_general_ledger_code"

        # Mock DELETE for old resource
        respx_mock.delete(
            f"/api/api/chartofaccounts/{old_scope}/{old_coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        ).mock(return_value=httpx.Response(200, json={}))

        # Mock POST for new resource
        respx_mock.post(
            f"/api/api/chartofaccounts/{new_scope}/{new_coa_code}/generalledgerprofile"
        ).mock(return_value=httpx.Response(200, json={}))

        new_chart = ChartOfAccountsRef(
            id="new_test_chart",
            scope=new_scope,
            code=new_coa_code
        )

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=new_chart,
            general_ledger_profile_code=general_ledger_profile_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        old_state = SimpleNamespace(
            scope=old_scope,
            code=old_coa_code,
            general_ledger_profile_code=general_ledger_profile_code,
            content_hash="old_hash_value",
            mappings_hash="old_mappings_hash"
        )

        state = sut.update(self.client, old_state)

        # Verify delete was called on old resource and create on new
        assert state is not None
        assert state["scope"] == new_scope
        assert state["code"] == new_coa_code
        assert state["general_ledger_profile_code"] == general_ledger_profile_code
        assert "mappings_hash" in state

        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        create_request = respx_mock.calls[1].request

        assert delete_request.method == "DELETE"
        assert delete_request.url.path == (
            f"/api/api/chartofaccounts/{old_scope}/{old_coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        )

        assert create_request.method == "POST"
        assert create_request.url.path == (
            f"/api/api/chartofaccounts/{new_scope}/{new_coa_code}/generalledgerprofile"
        )

    def test_update_no_change(self, respx_mock):
        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code="test_general_ledger_code",
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        desired = sut.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"id", "scope", "code", "chart_of_accounts", "general_ledger_profile_mappings"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()

        mappings_data = [mapping.model_dump(mode="json", by_alias=True)
                        for mapping in sut.general_ledger_profile_mappings]
        sorted_mappings = json.dumps(mappings_data, sort_keys=True)
        mappings_hash = sha256(sorted_mappings.encode()).hexdigest()

        old_state = SimpleNamespace(
            scope="test_scope",
            code="test_coa_code",
            general_ledger_profile_code="test_general_ledger_code",
            content_hash=content_hash,
            mappings_hash=mappings_hash
        )

        state = sut.update(self.client, old_state)

        assert state is None

        assert len(respx_mock.calls) == 0

    def test_delete(self, respx_mock):
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_profile_code = "test_general_ledger_code"

        respx_mock.delete(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        ).mock(return_value=httpx.Response(200, json={}))

        old_state = SimpleNamespace(
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=general_ledger_profile_code
        )

        glp.GeneralLedgerResource.delete(self.client, old_state=old_state)

        request = respx_mock.calls.last.request

        assert request.method == "DELETE"
        assert request.url.path == (
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_profile_code}"
        )

    def test_dump(self):
        general_ledger_profile_code = "test_general_ledger_code"

        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=self.create_chart_of_accounts(),
            general_ledger_profile_code=general_ledger_profile_code,
            description="Test description",
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        dumped = sut.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            round_trip=True,
            context={"style": "dump"}
        )

        expected_body = {
            "generalLedgerProfileCode": general_ledger_profile_code,
            "description": "Test description",
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
                {
                    "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    "levels": ["EconomicBucket"]
                }
            ],
            "chartOfAccounts": {"$ref": "test_chart"}
        }

        assert dumped == expected_body

    def test_undump(self):
        """Test undump - should be symmetrical with test_dump"""
        chart_of_accounts = self.create_chart_of_accounts()

        # This is what test_dump outputs, so undump should accept it
        data = {
            "chartOfAccounts": {"$ref": "test_chart"},
            "generalLedgerProfileCode": "test_general_ledger_code",
            "description": "Test description",
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
                {
                    "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    "levels": ["EconomicBucket"]
                }
            ]
        }

        result = glp.GeneralLedgerResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "test_id",
                "$refs": {
                    "test_chart": chart_of_accounts
                }
            }
        )

        expected = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=chart_of_accounts,
            general_ledger_profile_code="test_general_ledger_code",
            description="Test description",
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        assert result == expected

    def test_deps(self):
        general_ledger_profile_code = "test_general_ledger_code"

        chart_of_accounts = self.create_chart_of_accounts()
        sut = glp.GeneralLedgerResource(
            id="test_id",
            chart_of_accounts=chart_of_accounts,
            general_ledger_profile_code=general_ledger_profile_code,
            display_name="Test General Ledger Profile",
            general_ledger_profile_mappings=[
                glp.GeneralLedgerProfileMappings(
                    mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    levels=["EconomicBucket"]
                )
            ]
        )

        deps = sut.deps()

        assert deps == [chart_of_accounts]

    def test_parse_api(self):
        """Test parsing API response format"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        general_ledger_profile_code = "test_general_ledger_code"

        chart_of_accounts = self.create_chart_of_accounts()

        api_response = {
            "chartOfAccountsId": {
                "$ref": "test_chart"
            },
            "generalLedgerProfileCode": general_ledger_profile_code,
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
                {
                    "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    "levels": ["EconomicBucket"]
                }
            ]
        }

        result = glp.GeneralLedgerResource.model_validate(
            api_response,
            context={
                "id": "some-id",
                "$refs": {
                    "test_chart": chart_of_accounts
                }
            }
        )

        assert result.chart_of_accounts.scope == scope
        assert result.chart_of_accounts.code == coa_code
        assert result.general_ledger_profile_code == general_ledger_profile_code
        assert result.display_name == "Test General Ledger Profile"
        assert isinstance(result.general_ledger_profile_mappings[0], glp.GeneralLedgerProfileMappings)
        assert result.general_ledger_profile_mappings == [
            glp.GeneralLedgerProfileMappings(
                mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                levels=["EconomicBucket"]
            )
        ]


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeGeneralLedgerProfileRef:

    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_success(self, respx_mock):
        """Test attach when the general ledger profile exists"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        glp_code = "test_glp_code"

        mock_response = {
            "chartOfAccountsId": {
                "scope": scope,
                "code": coa_code
            },
            "generalLedgerProfileCode": glp_code,
            "displayName": "Test General Ledger Profile",
            "generalLedgerProfileMappings": [
                {
                    "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                    "levels": ["EconomicBucket"]
                }
            ]
        }

        respx_mock.get(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{glp_code}"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        sut = glp.GeneralLedgerProfileRef(
            id="test_ref",
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=glp_code
        )

        result = sut.attach(self.client)

        assert result == mock_response
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == (
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{glp_code}"
        )

    def test_attach_not_found(self, respx_mock):
        """Test attach when the general ledger profile doesn't exist"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        glp_code = "nonexistent_glp"

        respx_mock.get(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{glp_code}"
        ).mock(return_value=httpx.Response(404, json={"error": "Not found"}))

        sut = glp.GeneralLedgerProfileRef(
            id="test_ref",
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=glp_code
        )

        with pytest.raises(RuntimeError) as exc_info:
            sut.attach(self.client)

        assert f"General ledger profile with id {scope}/{coa_code} does not exist" in str(exc_info.value)

    def test_attach_error(self, respx_mock):
        """Test attach when there's a server error"""
        scope = "test_scope"
        coa_code = "test_coa_code"
        glp_code = "test_glp_code"

        respx_mock.get(
            f"/api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{glp_code}"
        ).mock(return_value=httpx.Response(500, json={"error": "Internal server error"}))

        sut = glp.GeneralLedgerProfileRef(
            id="test_ref",
            scope=scope,
            code=coa_code,
            general_ledger_profile_code=glp_code
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            sut.attach(self.client)
        assert exc_info.value.response.status_code == 500
