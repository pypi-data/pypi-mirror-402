from typing import Iterable

from libzapi.domain.models.help_center.article import Article
from libzapi.infrastructure.api_clients.help_center import ArticleApiClient


class ArticlesService:
    """High-level service using the API client."""

    def __init__(self, client: ArticleApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Article]:
        return self._client.list_all()

    def list_all_by_locale(self, locale: str) -> Iterable[Article]:
        return self._client.list_all_by_locale(locale=locale)

    def list_incremental(self, start_time: int) -> Iterable[Article]:
        return self._client.list_incremental(start_time=start_time)
