from perception.benchmark import percentile


def test_percentile_uses_nearest_rank():
    values = [1.0, 2.0, 3.0, 4.0, 100.0]
    assert percentile(values, 50) == 3.0
    assert percentile(values, 95) == 100.0


def test_percentile_empty():
    assert percentile([], 95) == 0.0
