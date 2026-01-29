from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.help_center.article import Article
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class ArticleApiClient:
    """HTTP adapter for Zendesk Categories in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[Article]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/help_center/articles",
            base_url=self._http.base_url,
            items_key="articles",
        ):
            yield to_domain(data=obj, cls=Article)

    def list_all_by_locale(self, locale: str) -> Iterator[Article]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/{locale}/articles",
            base_url=self._http.base_url,
            items_key="articles",
        ):
            yield to_domain(data=obj, cls=Article)

    def list_incremental(self, start_time: int) -> Iterator[Article]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/articles/incremental?start_time={int(start_time)}",
            base_url=self._http.base_url,
            items_key="articles",
        ):
            yield to_domain(data=obj, cls=Article)
