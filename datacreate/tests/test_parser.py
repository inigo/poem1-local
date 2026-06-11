import pytest
from parser import ParsedPoem, ParseError, parse_llm_response


SAMPLE_RESPONSE = """\
17:00: Five o'clock strikes, rain patters the glass
17:01: One past five, umbrellas bloom on the street
17:02: Two minutes in, the puddles deepen
17:03: Three past five, the grey sky sighs
17:04: Four minutes gone, petrichor fills the air
17:05: Five past five, damp coats and quiet halls
"""


def test_parse_basic():
    poems = parse_llm_response(SAMPLE_RESPONSE)
    assert len(poems) == 6
    assert poems[0] == ParsedPoem(time_str="17:00", poem="Five o'clock strikes, rain patters the glass")
    assert poems[-1].time_str == "17:05"


def test_parse_with_expected_times():
    times = [f"17:0{i}" for i in range(6)]
    poems = parse_llm_response(SAMPLE_RESPONSE, expected_times=times)
    assert len(poems) == 6


def test_parse_ignores_blank_lines_and_preamble():
    text = """
Here are your poems:

17:00: The hour begins in silence
17:01: One minute drifts by
"""
    poems = parse_llm_response(text)
    assert len(poems) == 2


def test_parse_zero_padded_output():
    text = "09:05: five past nine, the morning mist"
    poems = parse_llm_response(text)
    assert poems[0].time_str == "09:05"


def test_parse_single_digit_hour():
    text = "9:05: five past nine, the morning mist"
    poems = parse_llm_response(text)
    assert poems[0].time_str == "09:05"


def test_parse_empty_response_raises():
    with pytest.raises(ParseError, match="No valid poem lines"):
        parse_llm_response("")


def test_parse_only_preamble_raises():
    with pytest.raises(ParseError, match="No valid poem lines"):
        parse_llm_response("Here are some lovely poems for you!")


def test_parse_invalid_hour_raises():
    with pytest.raises(ParseError, match="Invalid time"):
        parse_llm_response("25:00: too late for poetry")


def test_parse_invalid_minute_raises():
    with pytest.raises(ParseError, match="Invalid time"):
        parse_llm_response("12:60: time out of bounds")


def test_parse_duplicate_time_raises():
    text = "17:00: first poem\n17:00: duplicate time"
    with pytest.raises(ParseError, match="Duplicate time"):
        parse_llm_response(text)


def test_parse_missing_expected_time_raises():
    text = "17:00: only one poem"
    with pytest.raises(ParseError, match="Missing expected times"):
        parse_llm_response(text, expected_times=["17:00", "17:01"])


def test_parse_extra_unexpected_time_raises():
    text = "17:00: poem\n17:01: extra poem"
    with pytest.raises(ParseError, match="Unexpected times"):
        parse_llm_response(text, expected_times=["17:00"])
