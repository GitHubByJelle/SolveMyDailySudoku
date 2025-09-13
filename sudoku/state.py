from dataclasses import dataclass, field
from typing import List
from .utils import bit_of, val_of, bits_iter, num_ones

@dataclass(slots=True)
class SudokuState:
    """
    Immutable-size Sudoku state that tracks:
      - board: list[int] with 0 for empty, or fixed value 1..n
      - opts:  list[int] of n-bit masks (bit k => value k+1 allowed)
    """
    n: int                             # side length (e.g., 9)
    N: int                             # total cells (n*n)
    box: int                           # box side (e.g., 3 for 9×9)
    all_mask: int                      # (1<<n)-1
    board: List[int] = field(default_factory=list)
    opts: List[int] = field(default_factory=list)
    # Neighbours: indices that share row/col/box with a cell (excluding itself)
    neigh: List[frozenset[int]] = field(default_factory=list)

    @classmethod
    def from_string(cls, mission: str) -> "SudokuState":
        N = len(mission)
        n = int(N**.5)
        assert n * n == N, "The sudoku must be a square for this solver to work"

        box = int(n**.5)
        assert n * n == N, "Side length must be a perfect square (e.g. 9)"

        all_mask = (1 << n) - 1
        board: List[int] = [bit_of(int(c)) for c in mission]
        opts: List[int] = [all_mask if board[i] == 0 else 0 for i in range(N)]

        neigh = cls._build_neigh(N, n, box)

        return cls(
            n = n,
            N = N,
            box = box,
            all_mask = all_mask,
            board = board,
            opts = opts,
            neigh = neigh
        )
    
    @staticmethod
    def _build_neigh(N: int, n: int, box: int) -> List[frozenset[int]]:
        neigh: List[frozenset[int]] = []
        for i in range(N):
            # Determine the row and index for i (given the number of columns n)
            r, c = divmod(i, n)

            # Calculate the rows and columns every n steps (for the row and col constraint, respectively)
            row = {j * n + c for j in range(n)}
            col = {k + r * n for k in range(n)}

            # Calculate the box indices (for the box constraint)
            br, bc = (r // box) * box, (c // box) * box
            box_ids = {
                (br + dr) * n + (bc + dc)
                for dr in range(box) for dc in range(box)
            }

            # Add all except the index itself
            ngh = (row | col | box_ids) - {i}
            neigh.append(frozenset(ngh))

        return neigh
    
    # Inspection classes

    def options_mask(self, idx: int) -> int:
        """Raw options bitmask for a cell index."""
        return self.opts[idx]

    def options(self, idx: int) -> List[int]:
        """Concrete options for a cell index."""
        return list(bits_iter(self.opts[idx]))
    
    def is_fixed(self, idx: int) -> bool:
        """True if cell has a no options and a board value."""
        return self.opts[idx] == 0 and self.board[idx] != 0
    
    # Mutations (local, not solving)

    def assign(self, idx: int, mask: int) -> None:
        if num_ones(mask) != 1:
            raise ValueError("The mask contains none or more then 1 ones")
        
        # Update the board and remove all options for this cell
        self.board[idx] = mask
        self.opts[idx] = 0

    def eliminate(self, idx: int, mask: int) -> None:
        self.opts[idx] &= ~mask

    def clone(self) -> "SudokuState":
        "Creates a deep copy of the state"
        return SudokuState(
            n=self.n,
            N=self.N,
            box=self.box,
            all_mask=self.all_mask,
            board=self.board.copy(),
            opts=self.opts.copy(),
            neigh=self.neigh,
        )
    
    # Convenience
    def to_string(self) -> str:
        s = ""
        for i in range(self.N):
            s += str(val_of(self.board[i]))
        return s

    def to_board_string(self) -> str:
        """Serialize the current board to a pretty string with box separators."""
        rows = []
        for i in range(self.n):
            # Build one row with vertical separators
            row_parts = []
            for j in range(self.n):
                row_parts.append(str(val_of(self.board[i * self.n + j])))
                # Add vertical line if we're at the end of a box
                if (j + 1) % self.box == 0 and j + 1 < self.n:
                    row_parts.append("|")
            rows.append(" ".join(row_parts))

            # Add horizontal line if we're at the end of a box
            if (i + 1) % self.box == 0 and i + 1 < self.n:
                rows.append("-" * (2 * self.n + self.box - 1))  # adjust length
        return "\n".join(rows)

    def to_board_with_opts(self) -> str:
        def bits_to_digits(mask: int) -> List[int]:
            return [i + 1 for i in range(self.n) if (mask >> i) & 1]

        def render_cell(idx: int) -> str:
            val = val_of(self.board[idx])
            if val:
                return str(val).center(self.n)
            digs = bits_to_digits(self.opts[idx])
            s = "".join(str(d) for d in digs) or "."
            return s.center(self.n)

        rows = []
        for i in range(self.n):
            row_parts = []
            for j in range(self.n):
                idx = i * self.n + j
                row_parts.append(render_cell(idx))
                if (j + 1) % self.box == 0 and j + 1 < self.n:
                    row_parts.append("|")
            rows.append(" ".join(row_parts))
            if (i + 1) % self.box == 0 and i + 1 < self.n:
                rows.append("-" * (self.n * 2))
        return "\n".join(rows)