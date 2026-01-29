from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.help_center.article_attachment import ArticleAttachment
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class ArticleAttachmentApiClient:
    """HTTP adapter for Zendesk Categories in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_inline(self, article_id) -> Iterator[ArticleAttachment]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/articles/{article_id}/attachments/inline",
            base_url=self._http.base_url,
            items_key="article_attachments",
        ):
            yield to_domain(data=obj, cls=ArticleAttachment)
