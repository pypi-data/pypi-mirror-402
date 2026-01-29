from __future__ import annotations

# mypy: disable-error-code="assignment"
from datetime import date
from enum import StrEnum
from typing import MutableMapping

from diracx.core.config.schema import BaseModel
from diracx.core.config.schema import Config as _Config
from diracx.core.config.schema import OperationsConfig as _OperationsConfig
from diracx.core.config.schema import RegistryConfig as _RegistryConfig
from diracx.core.config.schema import UserConfig as _UserConfig
from pydantic import Field

"""
In order to add extra config, you need to redefine
the whole tree down to the point you are interested in changing
"""


class CERNAccountType(StrEnum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    SERVICE = "Service"
    NON_CERN_ACCOUNT = "NonCERNAccount"


class UserConfig(_UserConfig):
    # Use default values here as we have non-CERN accounts like local IAM users
    CERNAccountType: CERNAccountType = CERNAccountType.NON_CERN_ACCOUNT
    PrimaryCERNAccount: str = ""
    CERNPersonId: int = -1
    # Mapping from VO name to affiliation end date (YYYY-MM-DD)
    AffiliationEnds: dict[str, date] = Field(default_factory=dict)


class RegistryConfig(_RegistryConfig):
    Users: MutableMapping[str, UserConfig]


class AnalysisProductionsConfig(BaseModel):
    ForceActiveInput: list[str] = []


class OperationsConfig(_OperationsConfig):
    AnalysisProductions: AnalysisProductionsConfig = AnalysisProductionsConfig()


class Config(_Config):

    Operations: MutableMapping[str, OperationsConfig]
    Registry: MutableMapping[str, RegistryConfig]
