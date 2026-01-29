import typing
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

if typing.TYPE_CHECKING:
    from .client import ClientAPI
    from .tags import Tag


class Rating(Enum):
    """Safe, Questionable, or Explicit."""

    SAFE = 1
    QUESTIONABLE = 2
    EXPLICIT = 3

    @classmethod
    def str_to_rating(cls, rating: str) -> "Rating":
        """Maps "safe", "questionable", and "explicit" to enum values."""
        normalized = rating.lower()
        match normalized:
            case "safe":
                return cls.SAFE
            case "questionable":
                return cls.QUESTIONABLE
            case "explicit":
                return cls.EXPLICIT
            case _:
                raise ValueError(f"Unknown post rating type: {rating}")

    @classmethod
    def rating_to_str(cls, rating) -> str:
        """Maps enum values to "safe", "questionable", and "explicit"."""
        match rating:
            case cls.SAFE:
                return "safe"
            case cls.QUESTIONABLE:
                return "questionable"
            case cls.EXPLICIT:
                return "explicit"
            case _:
                raise ValueError(f"Unknown post rating type: {rating}")


@dataclass
class Comment:
    """Represents a comment.

    Attributes
    -----------
    id: :class:`int`
        ID of the comment.
    post: :class:`Post`
        Post the comment is under.
    content: :class:`str`
        Content of the comment.
    author: :class:`str`
        Creator of the comment.
    created_at: :class:`datetime.datetime`
        Timestamp of the comment's creation in UTC.
    """

    _raw: dict
    created_at: datetime
    post: "Post"
    content: str
    author: str
    id: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Comment):
            return self.id == other.id
        elif isinstance(other, str):
            return self.content == other
        elif isinstance(other, int):
            return self.id == other
        return NotImplemented

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"<Comment #{self.id} content={repr(self.content)} author={repr(self.author)} post={self.post.id}>"


@dataclass
class Post:
    """Represents a post.

    Attributes
    -----------
    id: :class:`int`
        ID of the post.
    tags: :class:`list[Tag]`
        List of post's tags.
    author: :class:`str`
        User who created the post.
    source: :class:`str`
        Where the post came from.
    score: :class:`int`
        Post's score.
    rating: :class:`Rating`
        Safe, Questionable, or Explicit.
    last_change: :class:`datetime.datetime`
        Timestamp of the post's last edit in UTC.
    content_url: :class:`str`
        URL of the post's image.
    comments: :class:`list[Comment]`
        Lazy-loaded list of comments.
    """

    _client: "ClientAPI"
    _raw: dict
    id: int
    tags: list["Tag"]
    author: str
    source: str
    score: int
    rating: Rating
    last_change: datetime
    content_url: str
    _comments: typing.Union[list[Comment], None] = None

    @property
    def comments(self):
        """Lazy-loaded list of comments.

        Only loaded once. Use :meth:`get_comments` for real-time querying."""
        if self._comments == None:
            self._comments = self.get_comments()
        return self._comments

    def get_comments(self):
        """Fetch comments of post."""
        return self._client.get_comments(self)

    def get_url(self):
        """URL of post."""
        return f"{self._client._base_url}/index.php?page=post&s=view&id={self.id}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Post):
            return self.id == other.id
        elif isinstance(other, int):
            return self.id == other
        return NotImplemented

    def __str__(self) -> str:
        return self.get_url()

    def __repr__(self) -> str:
        return f"<Post id={self.id} author={repr(self.author)} score={self.score} rating={Rating.rating_to_str(self.rating)}>"
