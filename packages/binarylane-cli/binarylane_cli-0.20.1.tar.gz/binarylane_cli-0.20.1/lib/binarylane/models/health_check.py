from __future__ import annotations

from typing import Any, Dict, List, Type, TypeVar

import attr

from binarylane.models.health_check_protocol import HealthCheckProtocol

T = TypeVar("T", bound="HealthCheck")


@attr.s(auto_attribs=True)
class HealthCheck:
    """
    Attributes:
        protocol (HealthCheckProtocol): The protocol used for the health check.

            | Value | Description |
            | ----- | ----------- |
            | http | The health check will be performed via HTTP. |
            | https | The health check will be performed via HTTPS. |
            | both | The health check will be performed via both HTTP and HTTPS. Failing a health check on one protocol will
            remove the server from the pool of servers only for that protocol. |

        path (str): The path to the health check endpoint.
    """

    protocol: HealthCheckProtocol
    path: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        protocol = self.protocol.value

        path = self.path

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "protocol": protocol,
                "path": path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        protocol = HealthCheckProtocol(d.pop("protocol"))

        path = d.pop("path")

        health_check = cls(
            protocol=protocol,
            path=path,
        )

        health_check.additional_properties = d
        return health_check

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
