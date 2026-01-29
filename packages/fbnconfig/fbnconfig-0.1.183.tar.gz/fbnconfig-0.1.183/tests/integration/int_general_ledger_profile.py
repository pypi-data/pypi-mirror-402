
import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import fund_accounting as fa
from fbnconfig import general_ledger_profile as glp
from tests.integration.generate_test_name import gen

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)
base_url = "api/api/chartofaccounts/"


@fixture(scope="module")
def setup_deployment():
    scope = gen("general_ledger_profile")

    yield SimpleNamespace(name=scope)
    coa_code = "coa_int_test_code"
    general_ledger_code = "fbnconfig_general_ledger_code"

    items_to_delete = [
        f"{base_url}{scope}/{coa_code}/generalledgerprofile/{general_ledger_code}"
        f"{base_url}{scope}/{coa_code}",
    ]
    for item in items_to_delete:
        try:
            client.delete(item)
        except Exception as e:
            print(f"Failed to clean up {item}, got error {e}")
            pass


@fixture
def base_resources(setup_deployment):
    scope = setup_deployment.name
    coa_code = "coa_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=coa_code,
        display_name="fbn config COA integration test"
    )

    general_ledger_profile = glp.GeneralLedgerResource(
        id="general_ledger_int_test_id",
        chart_of_accounts=chart_of_account,
        general_ledger_profile_code="fbnconfig_general_ledger_code",
        display_name="fbnconfig general ledger",
        general_ledger_profile_mappings=[
            glp.GeneralLedgerProfileMappings(
                mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                levels=[
                    "EconomicBucket"
                ]
            )
        ]
    )

    return [chart_of_account, general_ledger_profile]


@fixture
def updated_resources(setup_deployment):
    scope = setup_deployment.name
    coa_code = "coa_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=coa_code,
        display_name="fbn config COA integration test"
    )

    general_ledger_profile = glp.GeneralLedgerResource(
        id="general_ledger_int_test_id",
        chart_of_accounts=chart_of_account,
        general_ledger_profile_code="updated_fbnconfig_general_ledger_code",
        display_name="updated fbnconfig general ledger display name",
        general_ledger_profile_mappings=[
            glp.GeneralLedgerProfileMappings(
                mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                levels=[
                    "EconomicBucket"
                ]
            )
        ]
    )
    return [chart_of_account, general_ledger_profile]


def test_general_ledger_profile(base_resources, setup_deployment):
    scope = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    coa_code = "coa_int_test_code"
    general_ledger_code = "fbnconfig_general_ledger_code"

    formatted_url = (
        f"api/api/chartofaccounts/{scope}/{coa_code}/generalledgerprofile/{general_ledger_code}"
    )

    response = client.get(formatted_url).json()
    assert response is not None

    expected_general_ledger_profile_mappings = [
        {
      "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
      "levels": [
        "EconomicBucket"
      ]
    }
    ]
    assert response["chartOfAccountsId"] == {
        "scope": scope,
        "code": coa_code
    }
    assert response["generalLedgerProfileCode"] == general_ledger_code
    assert response["displayName"] == "fbnconfig general ledger"
    assert "description" not in response
    assert "generalLedgerProfileMappings" in response
    assert response["generalLedgerProfileMappings"] == expected_general_ledger_profile_mappings


def test_update_general_ledger_profile(setup_deployment, base_resources, updated_resources):
    scope = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    updated_deployment = fbnconfig.Deployment(setup_deployment.name, updated_resources)
    updated_deploy = fbnconfig.deploy(updated_deployment, lusid_env, token)

    general_ledger_changes_list = [a.change for a in updated_deploy if a.type == "GeneralLedgerResource"]

    assert general_ledger_changes_list == ["update"]

    updated_profile = client.get(
        f"api/api/chartofaccounts/{scope}/coa_int_test_code/generalledgerprofile/updated_fbnconfig_general_ledger_code"
    ).json()

    assert updated_profile["generalLedgerProfileCode"] == "updated_fbnconfig_general_ledger_code"
    assert updated_profile["displayName"] == "updated fbnconfig general ledger display name"
    assert updated_profile["generalLedgerProfileMappings"] == [
        {
      "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
      "levels": [
        "EconomicBucket"
      ]
    }
    ]


def test_update_general_ledger_profile_mappings(setup_deployment, base_resources):
    scope = setup_deployment.name
    coa_code = "coa_int_test_code"
    general_ledger_code = "fbnconfig_general_ledger_code"

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    chart_of_account = base_resources[0]

    updated_mappings = glp.GeneralLedgerResource(
        id="general_ledger_int_test_id",
        chart_of_accounts=chart_of_account,
        general_ledger_profile_code=general_ledger_code,
        display_name="fbnconfig general ledger",
        general_ledger_profile_mappings=[
            glp.GeneralLedgerProfileMappings(
                mapping_filter="GeneralLedgerAccountCode eq 'INVESTMENTS'",
                levels=[
                    "EconomicBucket"
                ]
            ),
            glp.GeneralLedgerProfileMappings(
                mapping_filter="true",
                levels=["DefaultCurrency"]
            )
        ]
    )

    deployment = fbnconfig.Deployment(setup_deployment.name, [chart_of_account, updated_mappings])
    updated_deployment = fbnconfig.deploy(deployment, lusid_env, token)

    gl_changes_list = [a.change for a in updated_deployment if a.type == "GeneralLedgerResource"]

    assert gl_changes_list == ["update"]

    updated_profile = client.get(
        f"api/api/chartofaccounts/{scope}/coa_int_test_code/generalledgerprofile/{general_ledger_code}"
    ).json()

    updated_profile.pop("links")
    updated_profile.pop("href")
    updated_profile.pop("version")

    expected_response = {
        "chartOfAccountsId": {"scope": scope, "code": coa_code},
        "generalLedgerProfileCode": general_ledger_code,
        "displayName": "fbnconfig general ledger",
        "generalLedgerProfileMappings": [
            {
                "mappingFilter": "GeneralLedgerAccountCode eq 'INVESTMENTS'",
                "levels": ["EconomicBucket"]
            },
            {
                "mappingFilter": "true",
                "levels": ["DefaultCurrency"]
            }
        ]
    }

    assert updated_profile == expected_response


def test_nochange(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    no_change_deploy = fbnconfig.deploy(deployment, lusid_env, token)

    no_change_list = [a.change for a in no_change_deploy if a.type == "GeneralLedgerResource"]

    assert no_change_list == ["nochange"]


def test_delete_general_ledger_profile(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    updated_deployment = fbnconfig.Deployment(setup_deployment.name, base_resources[:1])
    tear_down_deploy = fbnconfig.deploy(updated_deployment, lusid_env, token)

    general_ledger_updates = [a.change for a in tear_down_deploy if a.type == "GeneralLedgerResource"]

    assert general_ledger_updates == ["remove"]
