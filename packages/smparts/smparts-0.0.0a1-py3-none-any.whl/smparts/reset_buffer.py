from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Optional

from .sentinels import ABYSS, BOTTOM


_OP = {ABYSS: False, BOTTOM: True}
@dataclass
class ResetBuffer:
    """
    ResetBuffer: a minimal 2-mode buffer with destructive, idempotent reset tokens.

    This is not "an array with magic"; it is a tiny stream transducer:
    it buffers normal items while in bottom mode, and routes items elsewhere
    while in abyss mode. Two sentinel tokens act as *control operators*.

    ------------------------------------------------------------
    State
    ------------------------------------------------------------
    A buffer is a pair (items, has_bottom):

        items       : List[Any]   (the current buffered batch)
        has_bottom  : bool        (mode bit)

    Interpretation:
        has_bottom = True   => bottom mode: normal items are appended to items
        has_bottom = False  => abyss mode : normal items are not buffered

    ------------------------------------------------------------
    Control tokens (operators)
    ------------------------------------------------------------
    Two sentinels: ABYSS and BOTTOM.

        ABYSS  : flush current batch, then switch to abyss mode
        BOTTOM : flush current batch, then switch to bottom mode

    Formally, define operators on states:

        A(items, b) = ([], False)     # ABYSS
        B(items, b) = ([], True)      # BOTTOM

    Algebra:
        A∘A = A,  B∘B = B        (idempotent)
        A∘B = A,  B∘A = B        (last reset wins)
        Both A and B are destructive: they clear items.

    ------------------------------------------------------------
    Data token handling (routing)
    ------------------------------------------------------------
    For a normal token x (x not in {ABYSS, BOTTOM}):

        if has_bottom=True  : buffer it   (items := items + [x])
        if has_bottom=False : route it out via on_abyss(x)

    Default routing:
        - on_flush(batch): no-op
        - on_abyss(x): no-op

    Notes:
        - flush can be empty ([]). This is intentional: it lets you treat
          consecutive reset tokens as producing an "empty batch shell".
        - No time/size semantics exist here. Only tokens drive transitions.
    """

    items: List[Any] = field(default_factory=list)
    has_bottom: bool = True

    # sinks (optional). Keep them pure and composable.
    on_flush: Optional[Callable[[List[Any]], None]] = None
    on_abyss: Optional[Callable[[Any], None]] = None

    def _emit_flush(self) -> None:
        cb = self.on_flush
        cb is not None and cb(self.items.copy())
        self.items.clear()

    def push(self, x: Any) -> "ResetBuffer":
        op = _OP.get(x, None)
        if op is not None:
            self._emit_flush()          # “拉屎”：把当前 batch 交出去（可为空）
            self.has_bottom = op        # 切换 mode
            return self

        if self.has_bottom:
            self.items.append(x)
        else:
            cb = self.on_abyss
            cb is not None and cb(x)    # “窜稀”：不进 buffer，直接丢到 abyss 通道
        return self

    def merge(self, xs: Iterable[Any] | "ResetBuffer") -> "ResetBuffer":
        seq = xs.items if isinstance(xs, ResetBuffer) else xs
        for x in seq:
            self.push(x)
        return self

    def __iadd__(self, xs): return self.merge(xs)
    def __add__(self, xs):
        y = ResetBuffer(self.items.copy(), self.has_bottom, self.on_flush, self.on_abyss)
        return y.merge(xs)

    def __repr__(self) -> str:
        return f"ResetBuffer({self.items!r}) ({'bottom' if self.has_bottom else 'abyss'})"

