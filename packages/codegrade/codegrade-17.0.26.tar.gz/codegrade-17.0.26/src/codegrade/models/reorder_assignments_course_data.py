"""The module that defines the ``ReorderAssignmentsCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class ReorderAssignmentsCourseData:
    """Input data required for the `Course::ReorderAssignments` operation."""

    #: A list of assignment IDs in the desired order.
    assignment_ids: t.Sequence[int]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "assignment_ids",
                rqa.List(rqa.SimpleValue.int),
                doc="A list of assignment IDs in the desired order.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "assignment_ids": to_dict(self.assignment_ids),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ReorderAssignmentsCourseData], d: t.Dict[str, t.Any]
    ) -> ReorderAssignmentsCourseData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            assignment_ids=parsed.assignment_ids,
        )
        res.raw_data = d
        return res
