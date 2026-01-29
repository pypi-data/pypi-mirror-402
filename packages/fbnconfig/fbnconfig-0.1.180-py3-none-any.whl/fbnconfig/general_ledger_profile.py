
import json
import string
from hashlib import sha256
from typing import List

import httpx
from pydantic import BaseModel, Field, model_validator

from fbnconfig import fund_accounting as fa
from fbnconfig.resource_abc import CamelAlias, Ref, Resource, register_resource
from fbnconfig.urlfmt import Urlfmt

url: string.Formatter = Urlfmt("api/api/chartofaccounts")
GENERAL_LEDGER_URL = ("{base}/{scope}/{code}/generalledgerprofile/{general_ledger_profile_code}")
GENERAL_LEDGER_MAPPINGS_URL = ("{base}/{scope}/{code}/generalledgerprofile/"
                                "{general_ledger_profile_code}/mappings")


class GeneralLedgerProfileMappings(CamelAlias, BaseModel):
    mapping_filter: str
    levels: List[str]


class GeneralLedgerProfileRef(CamelAlias, BaseModel, Ref):
    """Reference to a GeneralLedgerResource"""
    id: str = Field(exclude=True)
    scope: str = Field(exclude=True)
    code: str = Field(exclude=True)
    general_ledger_profile_code: str = Field(exclude=True)

    def attach(self, client):
        formatted_url = url.format(
            GENERAL_LEDGER_URL,
            scope=self.scope,
            code=self.code,
            general_ledger_profile_code=self.general_ledger_profile_code
        )
        try:
            return client.get(formatted_url).json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"General ledger profile with id {self.scope}/{self.code} does not exist"
                )
            else:
                raise ex


@register_resource()
class GeneralLedgerResource(Resource, BaseModel):
    id: str = Field(exclude=True)
    chart_of_accounts: fa.ChartOfAccountsKey
    # Body
    general_ledger_profile_code: str
    display_name: str
    general_ledger_profile_mappings: List[GeneralLedgerProfileMappings]
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data

        # Handle API response format with chartOfAccountsId
        if "chartOfAccountsId" in data:
            data = data | {"chart_of_accounts": data["chartOfAccountsId"]}

        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}

        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        general_ledger_profile_code = old_state.general_ledger_profile_code
        formatted_url = url.format(GENERAL_LEDGER_URL, scope=scope, code=code,
                                   general_ledger_profile_code=general_ledger_profile_code)
        return client.get(formatted_url).json()

    def create(self, client):
        desired = self.model_dump(
            mode="json", exclude_none=True, by_alias=True,
            exclude={"scope", "code", "chart_of_accounts", "general_ledger_profile_mappings"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()

        # Calculate mappings hash
        mappings_data = [mapping.model_dump(mode="json", by_alias=True)
                        for mapping in self.general_ledger_profile_mappings]
        sorted_mappings = json.dumps(mappings_data, sort_keys=True)
        mappings_hash = sha256(sorted_mappings.encode()).hexdigest()

        full_body = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                    exclude={"scope", "code", "chart_of_accounts"})

        formatted_url = url.format(("{base}/{scope}/{code}/generalledgerprofile"),
                                   scope=self.chart_of_accounts.scope, code=self.chart_of_accounts.code)
        client.request("POST", formatted_url, json=full_body)

        return {
            "scope": self.chart_of_accounts.scope,
            "code": self.chart_of_accounts.code,
            "general_ledger_profile_code": self.general_ledger_profile_code,
            "mappings_hash": mappings_hash,
            "content_hash": content_hash
        }

    def update(self, client, old_state):
        if ((self.chart_of_accounts.scope, self.chart_of_accounts.code, self.general_ledger_profile_code)
            != (old_state.scope, old_state.code, old_state.general_ledger_profile_code)):
            self.delete(client, old_state)
            return self.create(client)

        desired = self.model_dump(
            mode="json", exclude_none=True, by_alias=True,
            exclude={"scope", "code", "chart_of_accounts", "general_ledger_profile_mappings"}
        )

        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()

        # Calculate new mappings hash
        mappings_data = [mapping.model_dump(mode="json", by_alias=True)
                        for mapping in self.general_ledger_profile_mappings]
        sorted_mappings = json.dumps(mappings_data, sort_keys=True)
        mappings_hash = sha256(sorted_mappings.encode()).hexdigest()

        old_mappings_hash = getattr(old_state, "mappings_hash", None)
        old_content_hash = getattr(old_state, "content_hash", None)

        core_fields_changed = desired_hash != old_content_hash
        mappings_changed = old_mappings_hash and mappings_hash != old_mappings_hash

        if not core_fields_changed and not mappings_changed:
            return None  # No changes

        if core_fields_changed:
            self.delete(client, old_state)
            return self.create(client)

        return self.update_ledger_profile_mappings(client, mappings_hash, desired_hash)

    @staticmethod
    def delete(client, old_state):
        scope, code = old_state.scope, old_state.code
        general_ledger_profile_code = old_state.general_ledger_profile_code
        formatted_url = url.format(GENERAL_LEDGER_URL, scope=scope, code=code,
                                   general_ledger_profile_code=general_ledger_profile_code)
        client.request("DELETE", formatted_url)

    def deps(self):
        return [self.chart_of_accounts]

    def update_ledger_profile_mappings(self, client, mappings_hash, content_hash):
        glp_mappings = []

        for glp_maps in self.general_ledger_profile_mappings:
            glp_mappings.append(glp_maps.model_dump(mode="json", by_alias=True))

        client.request(
            "PUT",
            url.format(
                GENERAL_LEDGER_MAPPINGS_URL,
                scope=self.chart_of_accounts.scope,
                code=self.chart_of_accounts.code,
                general_ledger_profile_code=self.general_ledger_profile_code
            ),
            json=glp_mappings
        )

        return {
            "scope": self.chart_of_accounts.scope,
            "code": self.chart_of_accounts.code,
            "general_ledger_profile_code": self.general_ledger_profile_code,
            "mappings_hash": mappings_hash,
            "content_hash": content_hash
        }
