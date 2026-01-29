import typing
from dataclasses import dataclass


@dataclass
class Tag:
    """Represents a tag.

    Utilizes a DSL-like system of combining Tag objects.

    Operators
    -----------
        | `&`: "tag1 tag2"
        | `|`: "( tag1 ~ tag2 )"
        | `-`: "tag1 -tag2"
        | `-` (unary) OR `~`: "-tag"

    Notes
    -----------
        | All binary operators support :class:`str` inputs for `other`"""

    content: str = ""

    @classmethod
    def fuzzy(cls, content: str) -> "Tag":
        return cls(f"{content.strip()}~")

    def __and__(self, other: typing.Union[typing.Self, str]) -> "Tag":
        if isinstance(other, Tag):
            return Tag(f"( {self.content} ) ( {other.content} )".strip())
        elif isinstance(other, str):
            return Tag(f"( {self.content} ) ( {other.strip()} )".strip())
        return NotImplemented

    def __rand__(self, other: str) -> "Tag":
        if isinstance(other, str):
            return Tag(f"( {other.strip()} ) ( {self.content} )".strip())
        return NotImplemented

    def __or__(self, other: typing.Union[typing.Self, str]) -> "Tag":
        if isinstance(other, Tag):
            return Tag(f"( ( {self.content} ) ~ ( {other.content} ) )".strip())
        elif isinstance(other, str):
            return Tag(f"( ( {self.content} ) ~ ( {other.strip()} ) )".strip())
        return NotImplemented

    def __ror__(self, other: str) -> "Tag":
        if isinstance(other, str):
            return Tag(f"(  ( {other.strip()} ) ~ ( {self.content} ) )".strip())
        return NotImplemented

    def __sub__(self, other: typing.Union[typing.Self, str]) -> "Tag":
        if isinstance(other, Tag):
            return Tag(f"( {self.content} ) {(-other).content}".strip())
        elif isinstance(other, str):
            return Tag(f"( {self.content} ) -{other.strip()}".strip())
        return NotImplemented

    def __rsub__(self, other: str) -> "Tag":
        if isinstance(other, str):
            return Tag(f"( {other.strip()} ) {(-self).content}".strip())
        return NotImplemented

    def __neg__(self) -> "Tag":
        tmp = self.content.strip()
        if tmp.startswith("( ") and tmp.endswith(" )"):
            raise ValueError("Excluding a group is prohibited by search standards.")
        return Tag(f"-{tmp}")

    def __invert__(self) -> "Tag":
        return -self

    def __repr__(self) -> str:
        return f"<Tag {repr(self.content)}>"

    def __str__(self) -> str:
        return self.content
