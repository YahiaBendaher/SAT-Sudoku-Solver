# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 14:14:42 2024

@author: TriPykx
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 14:18:51 2024

@author: yahia
"""

import random

import itertools as it
import pycosat as sat
import numpy as np

import tkinter as tk

# # # # # # # # # # # #
#     SAT SOLVER      #
# # # # # # # # # # # #
def solve(cnf):
    return sat.solve([[int(a) for a in clause] for clause in cnf])


def itersolve(cnf):
    return sat.itersolve([[int(a) for a in clause] for clause in cnf])

""" Helper functions to create constraints for the SAT solver """


def no_more_than_one(lst):
    return [[-i, -j] for (i, j) in it.combinations(lst, 2)]

def at_least_one(lst):
    return [lst]

def exactly_one(lst):
    return no_more_than_one(lst) + at_least_one(lst)

n = 3 * 3

A = np.arange(1, n**3+1).reshape((n, n, n))

"""Add all the constrints"""

def check_prefilled(sudoku_grid):
    cnf = []
    for i in range(n):  
        for j in range(n):  
            if sudoku_grid[i, j] != 0:  
                digit = sudoku_grid[i, j]
                cnf.append([A[i, j, digit - 1]])
    return cnf

def check_cell():
    cnf = []
    for i in range(n):  
        for j in range(n):  
            cnf += at_least_one([A[i, j, k] for k in range(n)])
    return cnf

def check_row_or_column(digit):
    cnf = []
    for i in range(9):
        cnf += exactly_one(A[i, :, digit - 1])
        cnf += exactly_one(A[:, i, digit - 1])
    return cnf

def check_3x3_grid(digit):
    cnf = []
    grid_3x3_size = 3
    for subgrid_row in range(0, n, grid_3x3_size):
        for subgrid_col in range(0, n, grid_3x3_size):
            subgrid_vars = [
                A[subgrid_row + i, subgrid_col + j, digit - 1]
                for i in range(grid_3x3_size)
                for j in range(grid_3x3_size)
            ]
            cnf += exactly_one(subgrid_vars)
    return cnf

def sudoku_cnf(sudoku_grid):
    cnf = []
    cnf += check_prefilled(sudoku_grid)
    cnf += check_cell()
    for digit in range(1, 10):
        cnf += check_row_or_column(digit)
        cnf += check_3x3_grid(digit)
    return cnf

""" Convert the SAT solver's 3D solution into a 2D Sudoku grid """

def bin3D_to_dec2D(sol):
    grid3D = (np.array(sol).reshape((9, 9, 9)) > 0).astype(int)
    grid2D = np.zeros((9, 9), dtype=int)
    for i in range(1, 10):
        grid2D += i * grid3D[:, :, i - 1]
    return grid2D


""" Solve a Sudoku puzzle using a SAT solver """

def solve_sudoku(sudoku_grid):
    cnf = sudoku_cnf(sudoku_grid)
    sol = solve(cnf)
    if sol == 'UNSAT':
        return None
    return bin3D_to_dec2D(sol)

def nb_solutions(grid):
    cnf = sudoku_cnf(grid)
    nb_solutions = 0
    for sol in itersolve(cnf):
        nb_solutions += 1
        if nb_solutions > 1:
            return nb_solutions
    return nb_solutions


# # # # # # # # # # # #
#   GRID GENERATOR    #
# # # # # # # # # # # #

"""generate a grid based on the difficulty """

def transform_grid(grid):
    # Randomly rotate the grid 0, 90, 180, or 270 degrees
    rotations = random.randint(0, 3)
    grid = np.rot90(grid, rotations)
    
    # Randomly transpose the grid
    if random.random() < 0.5:
        grid = grid.T
        
    return grid

def generate_grid(difficulty):
    nb_empty_cells = int(81 * ((difficulty) / 100))
    cnf = sudoku_cnf(np.zeros((9, 9)))
    random.shuffle(cnf)
    grid = bin3D_to_dec2D(solve(cnf))
    
    positions = list(it.product(range(9), range(9)))
    random.shuffle(positions)
    
    for i in range(nb_empty_cells):
        x, y = positions[i]
        temp = grid[x, y]
        grid[x, y] = 0
        if nb_solutions(grid) !=1:
            grid[x, y] = temp          
    return grid


# # # # # # # # # # # #
#   GUI WITH TKINTER  #
# # # # # # # # # # # #

root = tk.Tk()
root.title("Sudoku Solver")
grid_size = 9
entries = np.array([None] * 9 * 9, dtype=tk.Entry).reshape((9, 9))

difficulty_var = tk.StringVar(value="Medium")  
def draw_grid():
    for i in range(grid_size):
        for j in range(grid_size):
            entry = tk.Entry(root, width=2, font=("Arial", 18), justify="center", bg="white")
            entry.grid(row=i, column=j, ipadx=5, ipady=5, padx=1, pady=1)
            entries[i][j] = entry

"""Get the grid from the GUI"""
def get_grid():
    grid = np.zeros((grid_size, grid_size), dtype=int)
    for i in range(grid_size):
        for j in range(grid_size):
            value = entries[i][j].get()
            grid[i, j] = int(value) if value.isdigit() else 0
    return grid

"""Set a given grid to the GUI with optional coloring"""
def set_grid(grid, color_solution=False):
    for i in range(grid_size):
        for j in range(grid_size):
            entries[i][j].delete(0, tk.END)  
            if grid[i, j] != 0:
                entries[i][j].insert(0, str(grid[i, j]))
                if color_solution: 
                    entries[i][j].config(fg="red")
                else: 
                    entries[i][j].config(fg="black", state="disabled")

"""Show the solution in the GUI"""
def print_solution():
    grid = get_grid()
    sol = solve_sudoku(grid)
    set_grid(sol, color_solution=True)

"""Empty the grid"""
def clear_grid():
    for i in range(grid_size):
        for j in range(grid_size):
            entries[i][j].config(state="normal", fg="black")  
    set_grid(np.zeros((grid_size, grid_size)))

"""Generate a new Sudoku grid based on the selected difficulty"""
def generate_new_grid():
    difficulty_map = {"Easy": 50, "Medium": 70, "Hard": 83}  
    difficulty = difficulty_map[difficulty_var.get()]
    grid = generate_grid(difficulty)
    clear_grid()  
    set_grid(grid)

#Drawing
draw_grid()


difficulty_label = tk.Label(root, text="Difficulty 🎮 :", font=("Arial", 12))
difficulty_label.grid(row=grid_size + 1 , column=1, columnspan=3, pady=10, sticky="e")

difficulty_menu = tk.OptionMenu(root, difficulty_var, "Easy", "Medium", "Hard")
difficulty_menu.config(width=8)
difficulty_menu.grid(row=grid_size + 1, column=4, columnspan=3, pady=10, sticky="w")

#buttons
button_clear = tk.Button(root, text="Clear🗑️", command=clear_grid)
button_clear.grid(row=grid_size + 2, column=0, columnspan=3, pady=0)

button_generate = tk.Button(root, text="Generate🖋️", command=generate_new_grid)
button_generate.grid(row=grid_size + 2, column=3, columnspan=3, pady=0)

button_solve = tk.Button(root, text="Solve🧠", command=print_solution)
button_solve.grid(row=grid_size + 2, column=6, columnspan=3, pady=10)


root.mainloop()