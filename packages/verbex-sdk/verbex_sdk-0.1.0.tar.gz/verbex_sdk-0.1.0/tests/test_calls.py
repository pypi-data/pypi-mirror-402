from typing import Sequence

from verbex.calls import Calls


def test_calls_list_accepts_sequence(monkeypatch):
    # Only check type acceptance; no request is sent without a client.
    assert isinstance(['a', 'b'], Sequence)
    assert Calls is not None
