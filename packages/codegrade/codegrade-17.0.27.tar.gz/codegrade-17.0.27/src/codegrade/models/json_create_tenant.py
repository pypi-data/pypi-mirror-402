"""The module that defines the ``JsonCreateTenant`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict


@dataclass
class JsonCreateTenant:
    """ """

    #: The name of the new tenant
    name: str
    #: The abbreviated name of this tenant, useful for searching.
    abbreviated_name: str
    #: The HubSpot company ID associated with this tenant
    hubspot_company_id: Maybe[str] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the new tenant",
            ),
            rqa.RequiredArgument(
                "abbreviated_name",
                rqa.SimpleValue.str,
                doc="The abbreviated name of this tenant, useful for searching.",
            ),
            rqa.OptionalArgument(
                "hubspot_company_id",
                rqa.SimpleValue.str,
                doc="The HubSpot company ID associated with this tenant",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.hubspot_company_id = maybe_from_nullable(self.hubspot_company_id)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "name": to_dict(self.name),
            "abbreviated_name": to_dict(self.abbreviated_name),
        }
        if self.hubspot_company_id.is_just:
            res["hubspot_company_id"] = to_dict(self.hubspot_company_id.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[JsonCreateTenant], d: t.Dict[str, t.Any]
    ) -> JsonCreateTenant:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
            abbreviated_name=parsed.abbreviated_name,
            hubspot_company_id=parsed.hubspot_company_id,
        )
        res.raw_data = d
        return res
