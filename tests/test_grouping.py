from narra.grouping import ArticleRecord, group_articles


def test_groups_segments_and_calculates_completeness():
    articles = [
        ArticleRecord(100, 'one@example', '[1/3] "Book.m4b" yEnc', 10),
        ArticleRecord(101, 'two@example', '[2/3] "Book.m4b" yEnc', 20),
    ]
    grouped = group_articles(articles)
    assert len(grouped) == 1
    assert grouped[0].title == 'Book.m4b'
    assert grouped[0].completion == 2 / 3
