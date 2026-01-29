# -*- coding: utf-8 -*-
# Python version: 3.9
# @TianZhen

from __future__ import annotations
from typing import (List, Optional, Any)

from ._utils import to_str


def to_ExtStr(obj: Any, /) -> ExtStr:
    r"""
    Convert a single object to **`Extended String`**.
    Ensure it is a subclass of :class:`ExtStr`.
    """
    return obj if isinstance(obj, ExtStr) else ExtStr(obj)


class ExtStr(str):
    r"""
    A class of **`{Extended String}`** extends the built-in :class:`str` class.
    """
    _is_fg_colored: bool = False
    _is_bg_colored: bool = False
    _is_styled: bool = False
    _is_plain: bool = True

    @classmethod
    def from_iter(cls, *objects: Any):
        r"""
        Create an **`Extended String`** from an iterable of objects.
        """
        return cls("".join(map(to_str, objects)))

    def findall(
        self,
        sub: Any,
        start: int = 0,
        end: Optional[int] = None,
        /,
        limit: int = -1
    ) -> List[int]:
        r"""
        Find all occurrences of a substring in the **`Extended String`** from the `left`.

        Parameters
        ----------
            sub : Any
                The substring to search for.

            start : int, default to `0`
                The starting index applied to the search.

            end : Optional[int], default to `None`
                The ending index applied to the search.

            limit : int, default to `-1`
                The maximum number of occurrences to find, by default -1 (no limit).

        Returns
        -------
            List[int]
                A list of starting indices where the substring is found.
        """
        return list(self._search(to_str(sub), start, end, limit))

    def rfindall(
        self,
        sub: Any,
        start: int = 0,
        end: Optional[int] = None,
        /,
        limit: int = -1
    ) -> List[int]:
        r"""
        Find all occurrences of a substring in the **`Extended String`** from the `right`.
        (Parameter ref to :func:`ExtStr.findall()`)
        """
        indices = list(self._search(to_str(sub), start, end, limit, True))
        indices.reverse()
        return indices

    def _search(
        self,
        sub: str,
        start: int = 0,
        end: Optional[int] = None,
        /,
        limit: int = -1,
        reverse: bool = False
    ):
        r"""Create a generator to search for occurrences of a substring in the **`Extended String`**."""
        count = 0
        while limit < 0 or count < limit:
            if reverse:
                end = idx = super().rfind(sub, start, end)
            else:
                idx = super().find(sub, start, end)
                start = idx + len(sub)
            if idx == -1:
                break
            yield idx
            # update
            count += 1

    def _add_judgment(self, segments: List[Any], /):
        r"""Add pattern judgment attributes to the **`Extended String`**."""
        self._is_fg_colored = any(seg.isfgcolored for seg in segments)
        self._is_bg_colored = any(seg.isbgcolored for seg in segments)
        self._is_styled = any(seg.isstyled for seg in segments)
        self._is_plain = not any((self.isfgcolored, self.isbgcolored, self.isstyled))

    def __add__(self, other: Any, /) -> ExtStr:
        return type(self)(super().__add__(other))

    def __mul__(self, n: Any, /) -> ExtStr:
        return type(self)(super().__mul__(n))

    def __rmul__(self, n: Any, /):
        return self.__mul__(n)

    @property
    def isfgcolored(self) -> bool:
        r"""
        Whether the **`Extended String`** has any foreground color applied.
        """
        return self._is_fg_colored

    @property
    def isbgcolored(self) -> bool:
        r"""
        Whether the **`Extended String`** has any background color applied.
        """
        return self._is_bg_colored

    @property
    def isstyled(self) -> bool:
        r"""
        Whether the **`Extended String`** has any style applied.
        """
        return self._is_styled

    @property
    def isplain(self) -> bool:
        r"""
        Whether the **`Extended String`** is plain (no pattern applied).
        """
        return self._is_plain

    @property
    def plain(self) -> ExtStr:
        r"""
        The **`Extended String`**.
        """
        return self
