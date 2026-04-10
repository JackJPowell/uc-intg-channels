"""
Channels App Media Browser.

Implements the UC Remote Two media browsing API against the Channels DVR Server API.

Browse hierarchy:
  ROOT (Channels)
  ├─ TV Shows                    (media_type="tv_shows",  media_id="tv_shows")
  │   └─ Show                    (media_type="show",      media_id=<show_id>)
  │       └─ Episode             (can_play=True,          media_id=<episode_id>)
  └─ Movies                      (media_type="movies",    media_id="movies")
      └─ Movie                   (can_play=True,          media_id=<movie_id>)

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import TYPE_CHECKING

from ucapi import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    Pagination,
)

if TYPE_CHECKING:
    from device import Device

_LOG = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pagination(items_returned: int, total: int | None, page: int) -> Pagination:
    """Build a Pagination block."""
    return Pagination(limit=items_returned, page=page, count=total)


def _make_item(
    media_id: str,
    title: str,
    *,
    subtitle: str | None = None,
    media_class: str = MediaClass.DIRECTORY,
    media_type: str = "",
    can_browse: bool = False,
    can_play: bool = False,
    thumbnail: str | None = None,
    artist: str | None = None,
    duration: int | None = None,
    children: list[BrowseMediaItem] | None = None,
) -> BrowseMediaItem:
    """Build a BrowseMediaItem instance."""
    return BrowseMediaItem(
        media_id=media_id,
        title=title,
        subtitle=subtitle,
        media_class=media_class,
        media_type=media_type,
        can_browse=can_browse,
        can_play=can_play,
        thumbnail=thumbnail,
        artist=artist,
        duration=duration,
        items=children,
    )


def _empty_response() -> BrowseResults:
    """Return a safe empty root response."""
    return BrowseResults(
        media=_make_item("root", "Channels", can_browse=True),
        pagination=Pagination(limit=0, page=1, count=None),
    )


# ---------------------------------------------------------------------------
# Browse levels
# ---------------------------------------------------------------------------


def _browse_root() -> BrowseResults:
    """Return top-level categories."""
    children = [
        _make_item(
            "tv_shows",
            "TV Shows",
            media_class=MediaClass.DIRECTORY,
            media_type="tv_shows",
            can_browse=True,
        ),
        _make_item(
            "movies",
            "Movies",
            media_class=MediaClass.DIRECTORY,
            media_type="movies",
            can_browse=True,
        ),
    ]
    root = _make_item(
        "root",
        "Channels",
        media_class=MediaClass.DIRECTORY,
        can_browse=True,
        children=children,
    )
    return BrowseResults(
        media=root,
        pagination=_pagination(len(children), len(children), 1),
    )


async def _browse_tv_shows(device: "Device", page: int, limit: int) -> BrowseResults:
    """List all TV shows."""
    all_shows = await device._client.get_shows()  # pylint: disable=protected-access
    total = len(all_shows)
    start = (page - 1) * limit
    page_shows = all_shows[start : start + limit]

    children = [
        _make_item(
            str(show["id"]),
            show.get("name", "Unknown Show"),
            subtitle=str(show["release_year"]) if show.get("release_year") else None,
            media_class=MediaClass.TV_SHOW,
            media_type=MediaContentType.TV_SHOW,
            can_browse=True,
            thumbnail=show.get("image_url"),
        )
        for show in page_shows
    ]
    parent = _make_item(
        "tv_shows",
        "TV Shows",
        media_class=MediaClass.DIRECTORY,
        media_type="tv_shows",
        can_browse=True,
        children=children,
    )
    return BrowseResults(
        media=parent,
        pagination=_pagination(len(children), total, page),
    )


async def _browse_show_episodes(device: "Device", show_id: str) -> BrowseResults:
    """List all episodes for a show."""
    episodes = await device._client.get_show_episodes(show_id)  # pylint: disable=protected-access

    children = [
        _make_item(
            str(ep["id"]),
            _episode_title(ep),
            subtitle=_episode_subtitle(ep),
            media_class=MediaClass.EPISODE,
            media_type=MediaContentType.EPISODE,
            can_play=True,
            thumbnail=ep.get("image_url"),
            duration=int(ep["duration"]) if ep.get("duration") else None,
        )
        for ep in episodes
    ]

    # Use the show title from the first episode if available
    show_title = episodes[0].get("title", "Show") if episodes else "Show"

    parent = _make_item(
        show_id,
        show_title,
        media_class=MediaClass.TV_SHOW,
        media_type=MediaContentType.TV_SHOW,
        can_browse=True,
        children=children,
    )
    return BrowseResults(
        media=parent,
        pagination=_pagination(len(children), len(children), 1),
    )


async def _browse_movies(device: "Device", page: int, limit: int) -> BrowseResults:
    """List all movies."""
    all_movies = await device._client.get_movies()  # pylint: disable=protected-access
    total = len(all_movies)
    start = (page - 1) * limit
    page_movies = all_movies[start : start + limit]

    children = [
        _make_item(
            str(movie["id"]),
            movie.get("title", "Unknown Movie"),
            subtitle=str(movie["release_year"]) if movie.get("release_year") else None,
            media_class=MediaClass.MOVIE,
            media_type=MediaContentType.MOVIE,
            can_play=True,
            thumbnail=movie.get("image_url"),
            duration=int(movie["duration"]) if movie.get("duration") else None,
        )
        for movie in page_movies
    ]
    parent = _make_item(
        "movies",
        "Movies",
        media_class=MediaClass.DIRECTORY,
        media_type="movies",
        can_browse=True,
        children=children,
    )
    return BrowseResults(
        media=parent,
        pagination=_pagination(len(children), total, page),
    )


# ---------------------------------------------------------------------------
# Title helpers
# ---------------------------------------------------------------------------


def _episode_title(ep: dict) -> str:
    """Build a display title for an episode."""
    season = ep.get("season_number")
    episode = ep.get("episode_number")
    episode_title = ep.get("episode_title") or ep.get("title", "Unknown Episode")
    if season is not None and episode is not None:
        return f"S{season:02d}E{episode:02d} - {episode_title}"
    return episode_title


def _episode_subtitle(ep: dict) -> str | None:
    """Build a subtitle for an episode (original air date)."""
    return ep.get("original_air_date")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def browse(device: "Device", options: BrowseOptions) -> BrowseResults:
    """
    Handle a browse_media request from the Remote.

    :param device: Connected Device instance
    :param options: Typed browse options from the remote
    :return: BrowseResults dataclass
    """
    media_id: str | None = options.media_id
    media_type: str | None = options.media_type
    paging = options.paging
    limit = int(
        (paging.limit if paging and paging.limit else None) or DEFAULT_PAGE_SIZE
    )
    page = int((paging.page if paging and paging.page else None) or 1)

    try:
        # Root
        if not media_id or media_type in (None, "root"):
            return _browse_root()

        # TV Shows list
        if media_type == "tv_shows":
            return await _browse_tv_shows(device, page, limit)

        # Individual show -> episodes
        if media_type == MediaContentType.TV_SHOW or media_type == "show":
            return await _browse_show_episodes(device, media_id)

        # Movies list
        if media_type == "movies":
            return await _browse_movies(device, page, limit)

        _LOG.warning(
            "Unknown media_type for browse: %s (media_id=%s)", media_type, media_id
        )
        return _browse_root()

    except Exception as ex:  # pylint: disable=broad-exception-caught
        _LOG.error(
            "Error browsing media (media_id=%s media_type=%s): %s",
            media_id,
            media_type,
            ex,
            exc_info=True,
        )
        return _empty_response()
