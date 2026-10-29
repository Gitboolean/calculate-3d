import pytest

from calculate3d.core.text import contains, name_key, normalize_name, sort_key


def test_normalize_name_trims_surrounding_whitespace() -> None:
    assert normalize_name("  PETG чорний \t") == "PETG чорний"


def test_name_key_matches_names_that_differ_only_by_case_or_edge_spaces() -> None:
    assert name_key("PETG чорний ") == name_key("petg ЧОРНИЙ")


def test_name_key_keeps_distinct_ukrainian_letters_apart() -> None:
    assert name_key("Ґудзик") != name_key("Гудзик")


@pytest.mark.parametrize(
    ("name", "query", "expected"),
    [
        ("Брелок-тризуб", "тризуб", True),
        ("Брелок-тризуб", "ТРИЗУБ", True),
        ("Брелок-Тризуб", "  тризуб ", True),
        ("Підставка", "тризуб", False),
        ("Підставка", "", True),
    ],
)
def test_contains_is_a_case_insensitive_substring_match(
    name: str, query: str, expected: bool
) -> None:
    assert contains(name, query) is expected


def test_sort_key_orders_latin_first_then_ukrainian_alphabet_ignoring_case() -> None:
    expected = ["Benchy", "гачок", "ґудзик", "єдиноріг", "Іграшка", "Ялинка"]
    shuffled = ["Ялинка", "Іграшка", "ґудзик", "Benchy", "єдиноріг", "гачок"]

    assert sorted(shuffled, key=sort_key) == expected


def test_sort_key_follows_ukrainian_order_for_e_ye_y_i_yi_iy() -> None:
    words = ["йод", "їжак", "іній", "ирій", "єнот", "етер", "ґава", "гава"]

    assert sorted(words, key=sort_key) == [
        "гава",
        "ґава",
        "етер",
        "єнот",
        "ирій",
        "іній",
        "їжак",
        "йод",
    ]


def test_sort_key_puts_other_scripts_after_cyrillic() -> None:
    assert sorted(["42 деталі", "яблуко", "apple"], key=sort_key) == [
        "apple",
        "яблуко",
        "42 деталі",
    ]


def test_normalize_name_applies_nfc() -> None:
    assert normalize_name("é") == "é"
    assert normalize_name("й") == "й"


def test_name_key_matches_composed_and_decomposed_forms() -> None:
    assert name_key("Café") == name_key("Café")
    assert name_key("Йод") == name_key("Йод")


def test_normalize_name_drops_format_characters() -> None:
    assert normalize_name("​PETG‍") == "PETG"
    assert normalize_name("​‍") == ""
