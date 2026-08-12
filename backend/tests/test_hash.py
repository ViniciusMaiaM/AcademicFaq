from services.hash import get_question_hash, normalize_question


def test_normalize_question_lowercases_and_collapses_whitespace():
    assert normalize_question("  Quando   é a   Prova?  ") == "quando é a prova"


def test_normalize_question_strips_trailing_punctuation():
    assert normalize_question("Quando é a prova???") == "quando é a prova"
    assert normalize_question("Quando é a prova.") == "quando é a prova"


def test_get_question_hash_same_for_trivial_variations():
    variations = [
        "Quando é a prova?",
        "quando é a prova",
        "  Quando   é a prova?  ",
        "QUANDO É A PROVA",
    ]
    hashes = {get_question_hash(v) for v in variations}
    assert len(hashes) == 1


def test_get_question_hash_different_for_different_questions():
    assert get_question_hash("Quando é a prova?") != get_question_hash("Onde é a prova?")
