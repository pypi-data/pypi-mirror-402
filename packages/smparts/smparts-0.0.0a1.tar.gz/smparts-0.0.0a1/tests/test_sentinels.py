import pickle

import pytest

from smparts.sentinels import Sentinel, ABYSS, BOTTOM


def test_sentinels_are_distinct_singletons():
    assert ABYSS is not BOTTOM
    assert isinstance(ABYSS, Sentinel)
    assert isinstance(BOTTOM, Sentinel)


def test_repr_is_readable_and_stable():
    assert repr(ABYSS) == "ABYSS"
    assert repr(BOTTOM) == "BOTTOM"


def test_sentinel_is_not_equal_to_string():
    # important: sentinel should not silently equal "ABYSS"/"BOTTOM"
    assert ABYSS != "ABYSS"
    assert BOTTOM != "BOTTOM"


def test_sentinel_is_hashable_and_usable_as_dict_key():
    d = {ABYSS: 123, BOTTOM: 456}
    assert d[ABYSS] == 123
    assert d[BOTTOM] == 456


def test_user_defined_sentinel_has_expected_repr():
    x = Sentinel("X")
    assert repr(x) == "X"


def test_slot_prevents_random_attributes():
    x = Sentinel("X")
    with pytest.raises(AttributeError):
        x.foo = 1


def test_pickle_roundtrip_keeps_semantics():
    """
    This checks a subtle thing: if someone pickles a sentinel instance,
    at least it should not mutate / break repr.
    """
    y = pickle.loads(pickle.dumps(ABYSS))
    assert isinstance(y, Sentinel)
    assert repr(y) == "ABYSS"

