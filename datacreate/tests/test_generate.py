import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generate import BATCH_SIZE, batched, time_range


def test_time_range_single():
    assert time_range("17:00", "17:00") == ["17:00"]


def test_time_range_span():
    result = time_range("17:00", "17:05")
    assert result == ["17:00", "17:01", "17:02", "17:03", "17:04", "17:05"]


def test_time_range_end_before_start():
    assert time_range("17:05", "17:00") == []


def test_time_range_hour_boundary():
    result = time_range("12:59", "13:01")
    assert result == ["12:59", "13:00", "13:01"]


def test_batched_exact_multiple():
    times = [f"12:{i:02d}" for i in range(40)]
    result = batched(times, 20)
    assert len(result) == 2
    assert len(result[0]) == 20
    assert len(result[1]) == 20


def test_batched_with_remainder():
    times = [f"12:{i:02d}" for i in range(25)]
    result = batched(times, 20)
    assert len(result) == 2
    assert len(result[0]) == 20
    assert len(result[1]) == 5


def test_batched_smaller_than_batch_size():
    times = ["17:00", "17:01", "17:02"]
    result = batched(times, 20)
    assert len(result) == 1
    assert result[0] == times


def test_batched_preserves_order():
    times = [f"09:{i:02d}" for i in range(45)]
    flat = [t for batch in batched(times, 20) for t in batch]
    assert flat == times


def test_three_hour_range_gives_nine_batches():
    # 12:00 to 14:59 = 180 minutes = 9 batches of 20
    times = time_range("12:00", "14:59")
    assert len(times) == 180
    assert len(batched(times, 20)) == 9


def test_batch_size_constant_is_20():
    assert BATCH_SIZE == 20
