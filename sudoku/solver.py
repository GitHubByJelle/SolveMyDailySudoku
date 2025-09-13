from collections import deque
from typing import Tuple, List

from .state import SudokuState
from .utils import num_ones

class SudokuSolver:
    def __init__(self, state: SudokuState):
        self.s = state
        self.units = self._units()

    @classmethod
    def from_string(cls, mission: str) -> "SudokuSolver":
        return cls(SudokuState.from_string(mission))

    # ------ Helpers ------
    def _allowed_mask(self, idx: int) -> int:
        if self.s.board[idx] != 0:
            return 0
        ban = 0
        for j in self.s.neigh[idx]:
            ban |= self.s.board[j]
        return self.s.all_mask & ~ban
    
    def _assign_and_enqueue(self, idx: int, mask: int, q: deque) -> None:
        self.s.assign(idx, mask)
        for j in self.s.neigh[idx]:
            if self.s.board[j] == 0:
                if j not in q:
                    q.append(j)

    def _units(self) -> Tuple[List[List[int]], List[List[int]], List[List[int]]]:
        n, box = self.s.n, self.s.box
        rows = [[r*n + c for c in range(n)] for r in range(n)]
        cols = [[r*n + c for r in range(n)] for c in range(n)]
        boxes = []
        for br in range(0, n, box):
            for bc in range(0, n, box):
                box_idxs = []
                for dr in range(box):
                    for dc in range(box):
                        box_idxs.append((br+dr)*n + (bc+dc))
                boxes.append(box_idxs)
        return rows, cols, boxes

    # ----- Core propagation loop -----
    def _deduce(self) -> Tuple[bool, bool]:
        """
        Do ONE pass of deduction.
        Returns (changed, contradiction_found).
        Applies: neighbor elimination, naked singles, hidden singles (once).
        Naked Single: Only has one option
        Hidden Single: In a given unit (one row, one column, or one box), if a digit can go in exactly one cell, that cell must take that digit
        """
        changed = False
        rows, cols, boxes = self.units
        q = deque()

        # Seed queue from already-fixed cells
        for i in range(self.s.N):
            if self.s.is_fixed(i):
                for j in self.s.neigh[i]:
                    if self.s.board[j] == 0:
                        q.append(j)

        # helper: tighten options from queue; assign naked singles
        def tighten_from_queue() -> Tuple[bool, bool]:
            nonlocal changed
            while q:
                j = q.popleft()
                if self.s.board[j] != 0:
                    continue
                new_mask = self._allowed_mask(j)
                if new_mask == 0:
                    return changed, True
                if new_mask != self.s.opts[j]:
                    self.s.opts[j] = new_mask
                    changed = True
                if num_ones(new_mask) == 1:
                    self._assign_and_enqueue(j, new_mask, q)
                    changed = True
            return changed, False

        # 1) neighbor eliminations + naked singles
        ch, bad = tighten_from_queue()
        if bad:
            return ch, True
        
        # 2) hidden singles (may enqueue and then tighten once more)
        for unit in (*rows, *cols, *boxes):
            # bit -> candidate indices
            pos = {}
            for idx in unit:
                if self.s.board[idx] == 0:
                    m = self.s.opts[idx]
                    b = m
                    while b:
                        bit = b & -b
                        pos.setdefault(bit, []).append(idx)
                        b &= b - 1

            for bit, where in pos.items():
                if len(where) == 1:
                    idx = where[0]
                    if self.s.board[idx] == 0:
                        self._assign_and_enqueue(idx, bit, q)
                        changed = True

            # Process consequences of any hidden-single assignments done in this unit
            if q:
                ch, bad = tighten_from_queue()
                if bad:
                    return ch, True

        return changed, False

    def _deduce_until_stable(self) -> Tuple[bool, bool]:
        """
        Keep calling `deduce()` until no more changes.
        Returns (progress_made, contradiction_found).
        """
        any_change = False
        while True:
            changed, bad = self._deduce()
            if bad:
                return any_change or changed, True
            if not changed:
                return any_change, False
            any_change = True

    def _search(self) -> bool:
        # run deduction first
        _, bad = self._deduce_until_stable()
        if bad:
            return False
        if self.is_solved():
            return True

        # choose cell with fewest options
        best_idx, best_mask, best_count = -1, 0, 999
        for i in range(self.s.N):
            if self.s.board[i] == 0:
                m = self.s.opts[i]
                c = num_ones(m)
                if c < best_count:
                    best_idx, best_mask, best_count = i, m, c
                    if c == 2:  # good heuristic: break early on 2
                        break

        # try each option (clone state for branch)
        b = best_mask
        while b:
            bit = b & -b
            b &= b - 1
            branch = self.s.clone()
            SudokuSolver(branch).s.assign(best_idx, bit)  # seed assignment
            solver = SudokuSolver(branch)
            if solver._search():
                # copy back winning board/opts
                self.s.board = branch.board
                self.s.opts = branch.opts
                return True
        return False
    
    # --- Convenience checks ---
    def is_solved(self) -> bool:
        s = self.s
        if any(s.board[i] == 0 for i in range(s.N)):
            return False
        rows, cols, boxes = self._units()
        for unit in (*rows, *cols, *boxes):
            seen = 0
            for idx in unit:
                m = s.board[idx]
                if m == 0 or (seen & m):
                    return False
                seen |= m
            if seen != s.all_mask:
                return False
        return True

    # ----- Public ------
    def solve_deductive(self) -> bool:
        _, bad = self._deduce_until_stable()
        if bad:
            raise ValueError("Contradiction during deduction.")
        return self.is_solved()
    
    def solve_search(self) -> bool:
        """Optional: deduction + DFS search. Keeps `SudokuState` clean."""
        ok = self._search()
        return ok