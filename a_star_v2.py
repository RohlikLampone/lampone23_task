import heapq
import turtle as t
from pprint import pprint
import sys

def generate_path(mode: str, draw_result: bool):
    def get_neighbors(current: tuple, maze: list):
        # Calculate the valid neighbors of the current location
        neighbors = []
        # Define possible movement directions (up, down, left, right)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            new_x = current[0] + dx
            new_y = current[1] + dy

            if 0 <= new_x < len(maze) and 0 <= new_y < len(maze[0]) and maze[new_x][new_y] != 0:
                neighbors.append((new_x, new_y))

        return neighbors

    def a_star(start: tuple, end: tuple, maze: list):
        open_list = [(0, start)]
        closed_set = set()
        g_scores = {start: 0}
        came_from = {}

        while open_list:
            _, current = heapq.heappop(open_list)

            if current == end:
                return reconstruct_path(current, start, came_from)

            closed_set.add(current)

            for neighbor in get_neighbors(current, maze):
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_scores[current] + int(maze[neighbor[0]][neighbor[1]])

                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, end)
                    heapq.heappush(open_list, (f_score, neighbor))
                    came_from[neighbor] = current

        return []  # No path found

    def heuristic(node: tuple, end: tuple):
        # Calculate a heuristic value (e.g., Manhattan distance)
        return abs(node[0] - end[0]) + abs(node[1] - end[1])

    def reconstruct_path(current: tuple, start: tuple, came_from: dict):
        path = [current]
        while current != start:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def find_optimal_path(start: tuple, end: tuple, maze: list):
        return a_star(start, end, maze)


    maze = [
        [0, 0, 4, 0, 0, 1, 1, 1],
        [4, 1, 1, 1, 0, 1, 0, 4],
        [4, 0, 0, 5, 0, 5, 0, 4],
        [1, 1, 0, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 0, 1, 1, 1],
        [1, 0, 0, 4, 0, 0, 0, 1],
        [1, 1, 0, 0, 0, 5, 0, 1],
        [1, 2, 0, 3, 1, 1, 1, 1]
    ]


    grid = maze.copy()

    # convert maze to grid with cell values
    def maze_to_grid(maze: list):
        for i in range(len(maze)):
            for j in range(len(maze[i])):
                # wall
                if (maze[i][j] == 0):
                    grid[i][j] = sys.maxsize
                # destination
                elif(maze[i][j] == 3):
                    grid[i][j] = -10
                # blue square (+3)
                elif (maze[i][j] == 4):
                    grid[i][j] = -3
                # red star (+6)
                elif(maze[i][j] == 5):
                    grid[i][j] = -6
                # empty cell, source (2) and the rest
                else:
                    grid[i][j] = 1
        
        return maze

    # convert grid back to maze because of a bug in Python
    def grid_to_maze(grid: list):
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                # wall
                if (grid[i][j] == sys.maxsize):
                    maze[i][j] = 0
                # destination
                elif(grid[i][j] == -10):
                    maze[i][j] = 3
                # blue square (+3)
                elif (grid[i][j] == -3):
                    maze[i][j] = 4
                # red star (+6)
                elif(grid[i][j] == -6):
                    maze[i][j] = 5
                # empty cell, source (2) and the rest
                else:
                    maze[i][j] = 1
        return grid

    def find_start_and_end(maze: list):
        start = ()
        end = ()

        for i in range(len(maze)):
            for j in range(len(maze[i])):
                if (maze[i][j] == 2):
                    start = (i, j)
                elif (maze[i][j] == 3):
                    end = (i, j)
        
        return start, end

    def convert_to_instructions(path: list):
        instructions = []
        for i in range(len(path)):
            if (i + 1 < len(path)):
                if path[i][1] - path[i + 1][1] == 1:
                    instructions.append("L")
                elif path[i][1] - path[i + 1][1] == -1:
                    instructions.append("R")
                elif path[i][0] - path[i + 1][0] == 1:
                    instructions.append("F")
                else:
                    instructions.append("B")

        return instructions

    def draw_maze(size: tuple):
        screen = t.Screen()
        screen.setup(width=800, height=800)
        screen.setworldcoordinates(0, 0, 8.1, 8.1)
        t.speed(20)
        
        t.penup()
        t.goto(0, 0)

        for y in range(size[1] + 1):
            t.pendown()
            t.goto(size[1], y)
            t.penup()
            t.goto(0, y + 1)
        
        t.penup()
        t.goto(0, size[1])
        t.right(90)

        for x in range(size[0] + 1):
            t.pendown()
            t.goto(x, 0)
            t.penup()
            t.goto(x + 1, size[0])

    def draw_path(path: list):
        t.penup()
        t.goto(path[0][1] + 0.5, 8 - path[0][0] - 0.5) # (y,x) -> (x,y)
        t.color("red")
        t.pendown()

        for node in path[1:]:
            t.goto(node[1] + 0.5, 8 - node[0] - 0.5)

    optimal_path = []
    points = 0
    instructions = []
    dist = 0

    start, end = find_start_and_end(maze)
    grid = maze_to_grid(maze)
    pprint(grid)

    maze = grid_to_maze(grid)

    if(draw_result): draw_maze((8, 8))
    
    if (mode == "optimal"):
        optimal_path = a_star(start, end, grid)
        dist = len(optimal_path)
        if (draw_result): draw_path(optimal_path)

        instructions = convert_to_instructions(optimal_path)

        # calculate points
        for i in range(len(optimal_path)):
            if (maze[optimal_path[i][0]][optimal_path[i][1]] == 4):
                points += 3
            elif (maze[optimal_path[i][0]][optimal_path[i][1]] == 5):
                points += 6
    
    elif (mode == "all_bonus_points"):
        cells = [start]
        paths = []

        for i in range(len(maze)):
            for j in range(len(maze[i])):
                if (maze[i][j] == 4 or maze[i][j] == 5):
                    cells.append((i, j))

        # sort cells by distance from end
        for i in range(1, len(cells) - 1):
            if (heuristic(cells[i], end) < heuristic(cells[i + 1], end)):
                cells[i], cells[i + 1] = cells[i + 1], cells[i]

        cells.append(end)

        # calculate paths from bonus points
        for i in range(len(cells) - 1):
            optimal_path = find_optimal_path(cells[i], cells[i + 1], grid)
            paths.append(optimal_path)

        # calculate points
        for i in range(len(paths)):
            for j in range(len(paths[i])):
                if (maze[paths[i][j][0]][paths[i][j][1]] == 4):
                    points += 3
                elif (maze[paths[i][j][0]][paths[i][j][1]] == 5):
                    points += 6

            instructions.append(convert_to_instructions(paths[i]))

        for i in range(len(paths)):
            if (draw_result): draw_path(paths[i])

            for j in range(len(paths[i])):
                dist += maze[paths[i][j][0]][paths[i][j][1]]
    

    print(f"Distance: {dist}")
    print(f"Path value (dist - points): {dist} - {points} = {dist - points}")
    print(instructions)
    
    if(draw_result): t.mainloop()

generate_path("optimal", True)
