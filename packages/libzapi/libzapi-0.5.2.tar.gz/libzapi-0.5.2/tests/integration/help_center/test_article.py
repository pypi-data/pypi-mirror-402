from libzapi import HelpCenter


def test_list_articles(help_center: HelpCenter):
    articles = list(help_center.articles.list_all())
    assert len(articles) > 0, "Expected at least one group from the live API"
