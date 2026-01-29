"""The module that defines the ``Proxy`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class Proxy:
    """The JSON representation of a proxy."""

    #: The id of this proxy.
    id: str
    #: The URL to start this proxy. You can add a path to a file to this URL to
    #: make this the root of the proxy that is started. The URL will always be
    #: without trailing slashes.
    start_url: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of this proxy.",
            ),
            rqa.RequiredArgument(
                "start_url",
                rqa.SimpleValue.str,
                doc="The URL to start this proxy. You can add a path to a file to this URL to make this the root of the proxy that is started. The URL will always be without trailing slashes.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "start_url": to_dict(self.start_url),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[Proxy], d: t.Dict[str, t.Any]) -> Proxy:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            start_url=parsed.start_url,
        )
        res.raw_data = d
        return res
