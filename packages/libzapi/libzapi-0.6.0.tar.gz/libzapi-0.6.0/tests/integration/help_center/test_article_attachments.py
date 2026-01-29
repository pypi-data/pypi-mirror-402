from libzapi import HelpCenter


def test_list_article_attachments(help_center: HelpCenter):
    articles = list(help_center.articles_attachments.list_inline(35105185982100))
    assert len(articles) > 0, "Expected at least one group from the live API"
