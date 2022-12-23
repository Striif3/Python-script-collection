# Import necessary modules
import numpy as np
import matplotlib.pyplot as plt

# Set the size of the grid and the number of generations
n = 100
generations = 50

# Create a grid of zeros
grid = np.zeros((n, n))

# Set the initial conditions
grid[n//2, n//2] = 1
grid[n//2+1, n//2] = 1
grid[n//2+1, n//2+1] = 1
grid[n//2, n//2+1] = 1

# Define the function that counts the number of neighbors of a cell
def count_neighbors(i, j):
    count = 0
    if i > 0 and grid[i-1, j] == 1:
        count += 1
    if i < n-1 and grid[i+1, j] == 1:
        count += 1
    if j > 0 and grid[i, j-1] == 1:
        count += 1
    if j < n-1 and grid[i, j+1] == 1:
        count += 1
    if i > 0 and j > 0 and grid[i-1, j-1] == 1:
        count += 1
    if i < n-1 and j < n-1 and grid[i+1, j+1] == 1:
        count += 1
    if i > 0 and j < n-1 and grid[i-1, j+1] == 1:
        count += 1
    if i < n-1 and j > 0 and grid[i+1, j-1] == 1:
        count += 1
    return count

# Define the function that simulates one generation
def simulate_generation():
    global grid
    new_grid = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            neighbors = count_neighbors(i, j)
            if grid[i, j] == 1:
                if neighbors == 2 or neighbors == 3:
                    new_grid[i, j] = 1
            else:
                if neighbors == 3:
                    new_grid[i, j] = 1
    grid = new_grid

# Simulate the specified number of generations
for i in range(generations):
    simulate_generation()

# Plot the final grid
plt.imshow(grid, cmap='binary')
plt.show()