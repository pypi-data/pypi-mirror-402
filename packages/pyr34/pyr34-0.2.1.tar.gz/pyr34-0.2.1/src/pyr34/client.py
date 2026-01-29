import typing, requests, logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from dataclasses import dataclass

from .tags import Tag
from .models import Post, Comment, Rating


@dataclass
class Authentication:
    user_id: int
    api_key: str


class ClientAPI:
    """Represents a connection to the R34 API.

    Central component of the library. Handles all communication to and from the API.

    Parameters
    -----------

    user_id: :class:`int`
        The ID of the user associated with the API key
    api_key: :class:`str`
        The API key used to authenticate the R34 API
    url: :class:`str`, optional
        Base URL for the API, should be an `index.php` (keyword-only).

        If omitted, `https://api.rule34.xxx/index.php` is used.
    base_url: :class:`str`, optional
        Base URL for the website (keyword-only).

        If omitted, `https://rule34.xxx/` is used.
    """

    def __init__(
        self, user_id: int, api_key: str, *, url: str = "", base_url: str = ""
    ):
        self._log = logging.getLogger("R34 API")
        self._api_url = url or "https://api.rule34.xxx/index.php"
        self._base_url = base_url or "https://rule34.xxx/"
        self._auth = Authentication(user_id, api_key)
        self._session = requests.Session()

        if url:
            self._log.info(f"Setting API url to {url}")

    def _get_params(
        self, params: typing.Mapping[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return (
            {"page": "dapi"}
            | dict(params)
            | {"api_key": self._auth.api_key, "user_id": self._auth.user_id}
        )

    def _request(
        self, params: typing.Mapping[str, typing.Any]
    ) -> typing.Union[ET.Element, typing.Any, None]:
        self._log.debug(
            f"Attempting following API call: {self._api_url}?{"&".join([f"{k}={str(v)}" for k, v in ({"page": "dapi"} | dict(params)).items()])}"
        )
        response = self._session.get(self._api_url, params=self._get_params(params))

        if (
            "<error>Missing authentication. Go to api.rule34.xxx for more information</error>"
            in response.text
        ):
            self._log.error("Attempted to make unauthorized API call! Report this!")
            raise PermissionError("401 Unauthorized.")

        content_type = response.headers.get("Content-Type", "")

        self._log.debug(
            f"Received {len(response.text)} bytes, Content-Type={content_type}"
        )

        if not response.text:
            return

        try:
            if "xml" in content_type:
                return ET.fromstring(response.text)
            elif "json" in content_type:
                return response.json()
            else:
                self._log.error("API returned unexpected Content-Type!")
                raise ValueError(
                    f"API returned unexpected Content-Type: {content_type}"
                )
        except (
            ET.ParseError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.InvalidJSONError,
        ) as e:
            self._log.error("General response parsing error! Report this!")
            raise ValueError(f"Unable to parse response: {type(e).__name__}") from e

    def request(
        self, params: typing.Mapping[str, typing.Any]
    ) -> typing.Union[
        ET.Element, typing.Any, None
    ]:  # xml, json, malformed request / empty response
        """Make a generic request to the API.

        Usage is discouraged, as input validation and error handling is minimal.

        Parameters
        -----------
        params: :class:`Mapping[str, Any]`
            GET parameters for the API request.

        Returns
        -----------
        :class:`xml.etree.ElementTree.Element` or :class:`Any`
            XML parsed as an Element, or JSON parsed into Python objects.

        Notes
        -----------
            | Logs API request at INFO level.
            | Returns `None` for empty responses.
        """
        if not params:
            return

        self._log.info(
            f"Making the following API Request: &{"&".join([f"{k}={str(v)}" for k, v in params.items()])}"
        )

        return self._request(params)

    def search_posts(
        self,
        tags: typing.Union[Tag, str] = Tag(),
        *,
        limit: int = 1000,
        exclusions: typing.Union[list[Tag], list[str], None] = None,
        page: int = 0,
        suppress_log: bool = False,
    ) -> typing.Generator[Post, None, None]:
        """Search for posts via standard search tags.

        Parameters
        -----------
        tags: :class:`Tag` or :class:`str`, optional
            Tags to search for.

            If omitted, pull from the front page.
        limit: :class:`int`, optional
            Maximum number of posts to pull (keyword-only).

            If omitted, pull the maximum allowed (1000).
        exclusions: :class:`list[Tag]` or :class:`list[str]`, optional
            Tags to exclude from search (keyword-only).
        page: :class:`int`, optional
            Page of results to return (keyword-only).

            If omitted, return first page.
        suppress_log: :class:`bool`, optional
            Don't log search (keyword-only). Intended for internal use.

        Returns
        -----------
        Generator that yields fetched `Post`s.

        Notes
        -----------
            | Logs search at INFO level.
            | Excluding tags using `tags` is allowed, but discouraged due to API quirks.
        """
        if limit <= 0 or limit > 1000:
            self._log.error(f"Attempted to fetch {limit} posts - out of API bounds!")
            raise ValueError(f"Result limit must be in range 0-1000, got {limit}")

        if page < 0:
            self._log.error(f"Attempted to fetch page {page} - makes no sense!")
            raise ValueError(f"Requested page must be >= 0, got {page}")

        if isinstance(tags, Tag):
            tags = tags.content

        exclusions = exclusions or []
        new_exclusions: list[str] = []
        for i, exclusion in enumerate(exclusions):
            if isinstance(exclusion, Tag):
                new_exclusions.append(exclusion.content)
            else:
                new_exclusions.append(exclusion)

            if " " in new_exclusions[i]:
                raise ValueError(
                    "Excluding a group of tags is prohibited by search standards."
                )

        exclusions = new_exclusions

        if exclusions:
            tags = f"{tags} -{' -'.join(exclusions)}"

        if not suppress_log:
            self._log.info(
                f"Searching for {limit} post{"s" if limit > 1 else ""} with tags {repr(tags)}"
            )

        api_response = self._request(
            {
                "s": "post",
                "q": "index",
                "json": 1,
                "limit": limit,
                "tags": tags,
                "pid": page,
            }
        )

        if isinstance(api_response, ET.Element):
            self._log.error("API returned XML instead of JSON during post fetching!")
            raise ValueError("XML data was unexpected at this time.")

        if not api_response:
            return

        if not isinstance(api_response, list):
            self._log.error("General error while fetching post! Report this!")
            raise ValueError(f"Unexpected error while searching for posts")

        for raw_post in api_response:
            post_tags: typing.Sequence[Tag] = list(
                map(lambda x: Tag(x.strip()), raw_post["tags"].split(" "))
            )

            yield Post(
                self,
                raw_post,
                raw_post["id"],
                post_tags,
                raw_post["owner"],
                raw_post["source"],
                raw_post["score"],
                Rating.str_to_rating(raw_post["rating"]),
                datetime.fromtimestamp(raw_post["change"], tz=timezone.utc),
                raw_post["file_url"],
            )

    def get_post(self, id: int) -> Post:
        """Fetch a post by ID.

        Parameters
        -----------
        id: :class:`int`
            ID of the post to fetch.

        Returns
        -----------
        | :class:`Post`
        |   The fetched post.

        Notes
        -----------
            | Logs fetch at INFO level.
        """
        self._log.info(f"Fetching post with id {id}")

        post = next(self.search_posts(f"id:{id}", limit=1, suppress_log=True), None)

        if not post:
            self._log.error("Attempted to fetch non-existent post!")
            raise ValueError(f"Requested post does not exist: {id}")

        return post

    def get_comments(self, post: Post) -> list[Comment]:
        """Fetch the comments of a post.

        Parameters
        -----------
        post: :class:`Post`
            Post to fetch comments from.

        Returns
        -----------
        | :class:`list[Comment]`
        |   List of fetched comments.

        Notes
        -----------
            | Logs fetch at INFO level."""
        self._log.info(f"Fetching comments under post with id {post.id}")

        api_response = self._request({"s": "comment", "q": "index", "post_id": post.id})

        if not isinstance(api_response, ET.Element):
            self._log.error(
                "API returned JSON instead of XML data during comment fetching!"
            )
            raise ValueError("JSON data was unexpected at this time.")

        raw_comments = list(api_response)

        if not raw_comments:
            return []

        comments = []
        for raw_comment in raw_comments:
            attrs = raw_comment.attrib
            comments.append(
                Comment(
                    attrs,
                    datetime.strptime(attrs["created_at"], "%Y-%m-%d %H:%M").replace(
                        tzinfo=timezone.utc
                    ),
                    post,
                    attrs["body"][:-1],  # r34 puts an extra space?
                    attrs["creator"],
                    int(attrs["id"]),
                )
            )

        return comments
