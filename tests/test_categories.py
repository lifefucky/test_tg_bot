"""Categories callback_data must match bot.CATEGORY_CALLBACK_IDS."""

from utils.categories import onlc_text_and_data


def test_category_callback_ids_match_bot():
    import bot

    expected = frozenset(data for _, data in onlc_text_and_data)
    assert bot.CATEGORY_CALLBACK_IDS == expected
