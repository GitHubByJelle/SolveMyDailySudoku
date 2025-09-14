# SolveMyDailySudoku
This project is a small personal experiment inspired by a statement I encountered in the “Discrete Optimization” course on Coursera. The instructor remarked, “That’s why for computers, it’s so easy to solve Sudoku.” Curious to test this claim myself, I set out to actually implement a Sudoku solver.

To make the project more interesting, I also built a scraper using Playwright to fetch the daily Sudoku puzzle from sudoku.com
. This way, the solver always has a fresh puzzle to work on. While developing it, I noticed how closely the logic resembles techniques I had already used for AI in games, but also how naturally it connects to Constraint Programming, a common approach in Operations Research for solving MIP/LP problems. Which thought me the similarities between both domains.

This project was developed in a single afternoon as a way to challenge myself with a mix of scraping, search algorithms, and problem-solving. Even though it is “just” an afternoon project, it provided me with valuable insights into both the simplicity and elegance of constraint-based problem solving. And I do have to admit, the instructor was right ;)