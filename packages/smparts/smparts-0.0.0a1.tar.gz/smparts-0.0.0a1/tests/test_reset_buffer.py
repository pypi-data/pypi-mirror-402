import pytest

from smparts.reset_buffer import ResetBuffer, ABYSS, BOTTOM


def test_initial_state():
    b = ResetBuffer()
    assert b.items == []
    assert b.has_bottom is True


def test_buffers_in_bottom_mode():
    b = ResetBuffer()
    b.merge([1, 2, 3])
    assert b.items == [1, 2, 3]
    assert b.has_bottom is True


def test_abyss_flushes_and_switches_mode():
    flushed = []

    def on_flush(batch):
        flushed.append(batch)

    b = ResetBuffer(on_flush=on_flush)
    b.merge([1, 2, 3]).push(ABYSS)

    # flush happened
    assert flushed == [[1, 2, 3]]
    # items cleared
    assert b.items == []
    # mode switched
    assert b.has_bottom is False


def test_bottom_flushes_and_switches_mode():
    flushed = []

    def on_flush(batch):
        flushed.append(batch)

    b = ResetBuffer(on_flush=on_flush)
    b.merge([1, 2]).push(BOTTOM)

    assert flushed == [[1, 2]]
    assert b.items == []
    assert b.has_bottom is True


def test_abyss_routes_items_outside_buffer():
    flushed = []
    abyssed = []

    def on_flush(batch):
        flushed.append(batch)

    def on_abyss(x):
        abyssed.append(x)

    b = ResetBuffer(on_flush=on_flush, on_abyss=on_abyss)

    b.merge([1, 2]).push(ABYSS)
    b.merge([10, 20, 30])

    # after ABYSS, new items should not be buffered
    assert b.items == []
    assert abyssed == [10, 20, 30]

    # flush only happened once when switching to ABYSS
    assert flushed == [[1, 2]]


def test_switching_back_to_bottom_then_buffering_resumes():
    flushed = []
    abyssed = []

    def on_flush(batch):
        flushed.append(batch)

    def on_abyss(x):
        abyssed.append(x)

    b = ResetBuffer(on_flush=on_flush, on_abyss=on_abyss)

    b.merge([1]).push(ABYSS)          # flush [1], go abyss
    b.merge([10, 20])                 # routed
    b.push(BOTTOM)                    # flush empty batch, go bottom
    b.merge([7, 8])                   # buffered

    assert flushed == [[1], []]       # note empty flush is intentional per docstring
    assert abyssed == [10, 20]
    assert b.items == [7, 8]
    assert b.has_bottom is True


def test_consecutive_resets_are_idempotent_and_destructive():
    flushed = []

    def on_flush(batch):
        flushed.append(batch)

    b = ResetBuffer(on_flush=on_flush)

    b.merge([1, 2])
    b.push(ABYSS).push(ABYSS)         # second ABYSS should flush empty
    b.push(BOTTOM).push(BOTTOM)       # second BOTTOM should flush empty too

    assert flushed == [[1, 2], [], [], []]
    assert b.items == []
    assert b.has_bottom is True


def test_iadd_and_add_semantics():
    flushed = []

    def on_flush(batch):
        flushed.append(batch)

    b = ResetBuffer(on_flush=on_flush)
    b += [1, 2]
    assert b.items == [1, 2]

    c = b + [3]
    # b unchanged by +
    assert b.items == [1, 2]
    # c is a new buffer with merged items
    assert c.items == [1, 2, 3]
    # callbacks should be preserved on copy
    c.push(ABYSS)
    assert flushed == [[1, 2, 3]]

    print("flushed:", flushed)


