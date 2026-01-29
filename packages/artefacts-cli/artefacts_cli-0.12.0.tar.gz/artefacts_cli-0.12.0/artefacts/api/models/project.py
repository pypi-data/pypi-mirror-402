from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset


T = TypeVar("T", bound="Project")


@_attrs_define
class Project:
    """
    Attributes:
        organization (str):
        name (str):
        framework (str | Unset):
        simulator (str | Unset):
    """

    organization: str
    name: str
    framework: str | Unset = UNSET
    simulator: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        organization = self.organization

        name = self.name

        framework = self.framework

        simulator = self.simulator

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "organization": organization,
                "name": name,
            }
        )
        if framework is not UNSET:
            field_dict["framework"] = framework
        if simulator is not UNSET:
            field_dict["simulator"] = simulator

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        organization = d.pop("organization")

        name = d.pop("name")

        framework = d.pop("framework", UNSET)

        simulator = d.pop("simulator", UNSET)

        project = cls(
            organization=organization,
            name=name,
            framework=framework,
            simulator=simulator,
        )

        return project
