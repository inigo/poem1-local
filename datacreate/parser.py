import re
from dataclasses import dataclass

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2}):\s+(.+)$")


@dataclass
class ParsedPoem:
    time_str: str   # "HH:MM" zero-padded
    poem: str


class ParseError(Exception):
    pass


def parse_llm_response(text: str, expected_times: list[str] | None = None) -> list[ParsedPoem]:
    """
    Parse LLM output into a list of ParsedPoem.

    Expected line format:  HH:MM: poem text
    expected_times, if given, is a list of "HH:MM" strings to validate against.
    Raises ParseError if nothing could be parsed or a time is out of range.
    """
    poems: list[ParsedPoem] = []
    seen_times: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = TIME_RE.match(line)
        if not m:
            continue
        hour, minute, poem_text = int(m.group(1)), int(m.group(2)), m.group(3).strip()
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ParseError(f"Invalid time value in line: {line!r}")
        time_str = f"{hour:02d}:{minute:02d}"
        if time_str in seen_times:
            raise ParseError(f"Duplicate time {time_str!r} in LLM response")
        seen_times.add(time_str)
        if not poem_text:
            raise ParseError(f"Empty poem text for time {time_str!r}")
        poems.append(ParsedPoem(time_str=time_str, poem=poem_text))

    if not poems:
        raise ParseError("No valid poem lines found in LLM response")

    if expected_times:
        expected_set = set(expected_times)
        missing = expected_set - seen_times
        extra = seen_times - expected_set
        if missing:
            raise ParseError(f"Missing expected times: {sorted(missing)}")
        if extra:
            raise ParseError(f"Unexpected times in response: {sorted(extra)}")

    return poems
