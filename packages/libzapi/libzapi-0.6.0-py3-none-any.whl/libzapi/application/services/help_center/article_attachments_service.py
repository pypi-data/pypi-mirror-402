from typing import Iterable

from libzapi.domain.models.help_center.article_attachment import ArticleAttachment
from libzapi.infrastructure.api_clients.help_center import ArticleAttachmentApiClient


class ArticleAttachmentsService:
    """High-level service using the API client."""

    def __init__(self, client: ArticleAttachmentApiClient) -> None:
        self._client = client

    def list_inline(self, article_id: int) -> Iterable[ArticleAttachment]:
        return self._client.list_inline(article_id)
