# SolveMyDailySudoku
This project is a small personal experiment inspired by a statement I encountered in the “Discrete Optimization” course on Coursera. The instructor remarked, “That’s why for computers, it’s so easy to solve Sudoku.” Curious to test this claim myself, I set out to actually implement a Sudoku solver.

To make the project more interesting, I also built a scraper using Playwright to fetch the daily Sudoku puzzle from sudoku.com
. This way, the solver always has a fresh puzzle to work on. While developing it, I noticed how closely the logic resembles techniques I had already used for AI in games, but also how naturally it connects to Constraint Programming, a common approach in Operations Research for solving MIP/LP problems. Which thought me the similarities between both domains.

This project was developed in a single afternoon as a way to challenge myself with a mix of scraping, search algorithms, and problem-solving. Even though it is “just” an afternoon project, it provided me with valuable insights into both the simplicity and elegance of constraint-based problem solving. And I do have to admit, the instructor was right ;)

<p align="center" width="50%">
    <img src="images\SolveMyDailySudoku.gif" alt="Solving the Sudoku with Solver" width="70%">
</p>

# Implementation Details
The code is written in Python and relies on the packages described in the `pyproject.toml`. The most important packages used is:
* Playwright

# How to use
This project uses [uv](https://astral.sh/) as the package manager. Begin by installing the required dependencies:
```bash
uv sync
```

Next, simply run main.py to run the solver. It will automatically fill in the answer on Sudoku.com:
```bash
uv run ./main.py
```

# Disclaimer

This project is a personal experiment created for educational purposes only. It is not intended to provide players with a competitive advantage on [sudoku.com](www.sudoku.com) or any other platform. Please use it responsibly.

The scraping functionality included in this project interacts with sudoku.com solely to fetch daily puzzles as part of the experiment. If at any point sudoku.com objects to this usage, I will promptly remove or disable the scraping component from this repository.

By using this code, you agree that you are responsible for ensuring your usage complies with [sudoku.com](www.sudoku.com)’s terms of service and applicable laws. The author does not endorse or support using this tool to bypass fair play, gain unfair advantages, or violate third-party rights.