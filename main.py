from sudoku.scraper import SudokoScraper, SudokuInfo
from sudoku.solver import SudokuSolver
from sudoku.utils import logger

if __name__ == "__main__":
    # Extract
    scraper: SudokoScraper = SudokoScraper(headless=False)
    info: SudokuInfo = scraper.fetch_daily()

    # Solve
    solver = SudokuSolver.from_string(info.mission)

    # Try deductive
    solved = solver.solve_deductive()

    if solved:
        logger.info("Solved the sudoku deductive")
    else:
        ok = solver.solve_search()

        if not ok:
            logger.info("The puzzle is infeasible")

    solution = solver.s.to_string()

    assert solution == info.solution, "The solution found, and received are not similar"

    scraper.fill_in_answer(solution=solution, keep_open=True)

