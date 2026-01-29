from peyo import safe_eyo, not_safe_eyo, Eyo


def test_restore_basic():
    assert safe_eyo.restore("Корабль") == "Корабль"
    assert safe_eyo.restore("Ежик") == "Ёжик"
    assert safe_eyo.restore("Емко") == "Ёмко"
    assert safe_eyo.restore("ПЕТР") == "ПЕТР"  # all-caps shouldn't match regex


def test_lint_counts():
    text = "«Лед тронулся, господа присяжные заседатели!»"
    assert len(safe_eyo.lint(text)) == 1
    assert len(not_safe_eyo.lint(text)) == 0


def test_dictionary_remove():
    e = Eyo()
    e.dictionary.add_word("ёлка")
    assert e.restore("Елка, елка") == "Ёлка, ёлка"
    e.dictionary.remove_word("ёлка")
    assert e.restore("Елка, елка") == "Елка, елка"
