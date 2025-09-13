from sudoku.scraper import SudokoScraper, SudokuInfo
from sudoku.solver import SudokuSolver

if __name__ == "__main__":
    # Extract
    scraper: SudokoScraper = SudokoScraper()
    info: SudokuInfo = scraper.fetch_daily()

    # Solve
    solver = SudokuSolver.from_string(info.mission)

    # Try deductive
    solved = solver.solve_deductive()

    if solved:
        print("Solved the sudoku deductive")
    else:
        ok = solver.solve_search()

        if not ok:
            print("The puzzle is infeasible")

    solution = solver.s.to_string()

    assert solution == info.solution, "The solution found, and received are not similar"

    print(solver.s.to_board_string())

