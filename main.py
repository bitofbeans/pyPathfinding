from math import sqrt
import tkinter as tk
from tkinter import ttk
from turtle import bgcolor, width
import pygame
import clipboard


# Uses the A* pathfinding algorithm #

METHOD = "Manhattan"  # Better for grids
# METHOD = "Euclidean" # Better for other
# METHOD = "Diagonal" # ???

# ----- CONSTANTS ------------------------ #
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
FPS = 60  # Frames per second
VISUALIZE = True

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LGREY = (200, 200, 200)
DGREY = (100, 100, 100)
FONT = (60, 80, 105)
FONT_ALT = (90, 160, 90)

ROWS = 50
COLS = 50
SPACE = int(0)  # Space between tiles
# ----- PYGAME --------------------------- #
pygame.init()  # Start up pygame
screen = pygame.display.set_mode(
    (SCREEN_WIDTH + 30, SCREEN_HEIGHT + 30)
)  # Create window
pygame.display.set_caption("Pathfinder")
clock = pygame.time.Clock()  # Get clock object for FPS

font = pygame.font.SysFont("segoeuibanner", 10)

# ----- FUNCTIONS ------------------------- #


def drawText(text, font, color, x, y, align="c"):
    """
    Renders text to the screen
    Usage: drawText("Text", font, color, x, y)
    """
    # render text to a surface
    img = font.render(text, True, color)
    # position text to center
    rect = img.get_rect()
    if align == "c":
        rect.center = x - 2, y - 2
    elif align == "lc":
        rect.x = x
        rect.centery = y
    # render surface to screen
    screen.blit(img, rect)


# ----- GAME CLASS ------------------------ #


class GameState:
    """
    Object that stores the current state of the game, including the grid,
    and functions for rendering, and inputs.
    """

    def __init__(self):

        self.grid = [["." for col in range(COLS)] for row in range(ROWS)]  # Create grid

        self.phase = "START"

        # Fit whichever value is bigger to screen
        if ROWS > COLS:
            self.size = SCREEN_WIDTH / ROWS
        else:
            self.size = SCREEN_HEIGHT / COLS

        self.size = int(self.size - SPACE)  # Round and account for spacing

        self.clicked = False
        self.square = 0
        self.pressed = False

    def render(self):
        """
        Draws screen and handles inputs
        """

        self.mousePos = pygame.mouse.get_pos()
        self.mouseClicked = pygame.mouse.get_pressed()
        for y in range(COLS):
            for x in range(ROWS):
                # pos= position---margin---offset------
                posx = x * self.size + x * SPACE + 15  # Position X
                posy = y * self.size + y * SPACE + 15  # Position Y
                self.square = pygame.rect.Rect(
                    posx, posy, self.size, self.size
                )  # Create square object
                # Logic
                self.updateTile((x, y))
                # Visualize colors
                if self.grid[y][x] == ".":
                    color = DGREY
                elif self.grid[y][x] == "#":
                    color = LGREY
                elif self.grid[y][x] == "O":
                    color = (3, 252, 161)
                    self.start = (x, y)
                elif self.grid[y][x] == "X":
                    color = (255, 33, 107)
                    self.dest = (x, y)
                elif self.grid[y][x] == "@":
                    dist = self.calcDist((x, y), self.dest)

                    if self.visual == True:
                        if dist < 50:
                            r = 255
                            g = round(dist / 50 * 209)
                            b = 166
                        else:
                            r = round((100 - dist) / 50 * 209)
                            g = 255
                            b = 166
                        color = (r, g, b)
                    else:
                        color = (70, 130, 255)
                # Render square
                pygame.draw.rect(screen, color, self.square, border_radius=2)

    def pathfinder(self):
        self.remove_all_of("@")  # Clear path that was there

        # Verify a start and end has been chosen
        try:
            if len(self.start) > 0 and len(self.dest) > 0:
                pass
        except AttributeError:
            gui.log("")
            gui.log("have not been chosen.")
            gui.log("Start and end points")
            return

        path = self.A_Star(self.start, self.dest)  # Returns a path to destination

        if path == "Failure":
            return  # If failed, stop

        self.remove_all_of("@")  # Clear path if was visualized
        self.apply_path_to_grid(path, "@")  # Show path on screen

    def save_to_clip(self):
        """
        Turns a grid to a string and copies it to the clipboard
        """
        code = self.grid  # Copy
        code = [item for row in code for item in row]  # Flatten
        code = "".join(code)  # Turn to string
        code.replace(" ", "")  # Remove white space
        clipboard.copy(code)  # Copy to clipboard

    def load_from_clip(self):
        """
        Load a grid from the clipboard.
        """
        code = clipboard.paste()
        size = ROWS * COLS
        if "X" in code and "O" in code:
            self.phase = "WALLS"
        else:
            return
        if len(code) == size:
            for i in range(len(code)):
                x = i % ROWS  # Solve for x
                y = int(i / ROWS)  # and y
                self.grid[y][x] = code[i]
        self.remove_all_of("@")  # Incase it contains the path

    def updateTile(self, pos):

        """
        Usage: squareLogic((x,y), square, mouseClicked, mousePos)
        Handles inputs to each square

            "." = Empty space
            "#" = Wall/Barrier
            "O" = Start
            "X" = Destination
            "@" = Path
        """
        """
                If a tile is clicked, check if it is open.
                    If it is open, check if we have already clicked last frame.
                        Place the corresponding square for each phase.
                    If we have already clicked last frame, check if we are placing a wall
                        Place the wall
        """
        x, y = pos
        if (
            self.square.collidepoint(self.mousePos) and self.mouseClicked[0]
        ):  # If clicked
            if self.grid[y][x] != "X" and self.grid[y][x] != "O":  # And empty space

                if not self.clicked:
                    if self.phase == "START":
                        self.grid[y][x] = "O"
                        self.phase = "DEST"
                    elif self.phase == "DEST":
                        self.grid[y][x] = "X"
                        self.phase = "WALLS"

                elif self.phase == "WALLS":
                    self.grid[y][x] = "#"

                self.clicked = True
        elif self.square.collidepoint(self.mousePos) and self.mouseClicked[2]:
            if self.phase == "WALLS":
                if self.grid[y][x] == "#":
                    self.grid[y][x] = "."

        if self.mouseClicked[0] == False:
            self.clicked = False

    def calcDist(self, start, end):
        """
        Usage: Tuple inputs for start and end coords.
        Calculate distance from point to point.
        Used to calculate "H" in A* algorithm.

        METHODS:

        Manhattan Method:
        h= |xstart - xdestination| + |ystart - ydestination|

        Euclidean Method:
        h= sqrt of ( xstart - xdestination )^2+( ystart - ydestination )^2

        Diagonal Method:
        see https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html#S7
        """
        x_start, y_start = start
        x_end, y_end = end

        if METHOD == "Manhattan":
            h = abs(x_start - x_end) + abs(y_start - y_end)
        elif METHOD == "Euclidean":
            h = sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)
        elif METHOD == "Diagonal":
            dx = abs(x_start - x_end)
            dy = abs(y_start - y_end)
            h = (dx + dy) + (1.4 - 2) * min(dx, dy)
        else:
            gui.log("")
            gui.log("(none selected?)")
            gui.log("Method error")
        return h

    def calcCost(self, start, end):
        sx, sy = start
        ex, ey = end
        if (sx == ex) or (sy == ey):
            return 1.0
        else:
            return 1.41

    def findNeighbors(self, node):
        def tryAdd(nx, ny):
            if self.grid[ny][nx] != "#":  # If it is not a wall,
                neighbors.append((nx, ny))  # add to neighbors list

        neighbors = []
        x, y = node
        if not x == 0:  # Account for left edge
            tryAdd(x - 1, y)  # Left
            # DIAGONALS
            if not y == 0:  # Account for top edge
                tryAdd(x - 1, y - 1)  # Top
            if not y == 49:  # Account for bottom edge
                tryAdd(x - 1, y + 1)  # Bottom
        if not x == 49:  # Account for right edge
            tryAdd(x + 1, y)  # Right
            # DIAGONALS
            if not y == 0:  # Account for top edge
                tryAdd(x + 1, y - 1)  # Top
            if not y == 49:  # Account for bottom edge
                tryAdd(x + 1, y + 1)  # Bottom
        if not y == 0:  # Account for top edge
            tryAdd(x, y - 1)  # Top
        if not y == 49:  # Account for bottom edge
            tryAdd(x, y + 1)  # Bottom

        return neighbors

    def reconstruct_path(self, cameFrom, current):
        """
        Reconstructs the path to the current node.

        Requires a dict that contains the node before it on the fastest path.
        """
        totalPath = [current]
        while current in cameFrom.keys():
            current = cameFrom[current]
            totalPath.insert(0, current)
        return totalPath

    def A_Star(self, start, dest):
        """
        The A* pathfinding algorithm.

        Takes a starting point and ending point and calculates the fastest path between them
        """

        ## calcDist() is used as h() ##
        ## Inspired by https://en.wikipedia.org/wiki/A*_search_algorithm
        # Tuples unpacked to coordinates
        startX, startY = start
        # The set of discovered nodes that may need to be (re-)expanded.
        # Initially, only the start node is known.
        # This is usually implemented as a min-heap or priority queue rather than a hash-set.
        openSet = [start]
        openSetFScores = [self.calcDist(start, dest)]

        # For node n, cameFrom[n] is the node immediately preceding it
        # on the cheapest path from start to n currently known.
        cameFrom = {}

        # For node n, gScore[n] is the cost of the cheapest path from
        # start to n currently known.
        gScore = [[99999 for col in range(COLS)] for row in range(ROWS)]
        gScore[startY][startX] = 0

        # For node n, fScore[n] := gScore[n] + h(n). fScore[n] represents our
        # current best guess as to how short a path from start to finish can
        # be if it goes through n.
        fScore = [[99999 for col in range(COLS)] for row in range(ROWS)]
        fScore[startY][startX] = self.calcDist(start, dest)

        # To record the loop cycles
        cycles = 0

        if VISUALIZE:
            self.visual = True
        else:
            self.visual = False

        oldtime = pygame.time.get_ticks()
        while openSet:  # While not empty
            # Find the node in the openSet with the lowest f value
            lowest = 99999
            i = 0  # Start at the end of the list
            for node in openSet:  # Reversed means it reversed the set
                temp_fScore = openSetFScores[i]
                if temp_fScore < lowest:  # If it is the lowest value so far,
                    current = node  # Set the current node to it
                    lowest = temp_fScore
                i += 1

            if current == dest:
                # We found the destination
                gui.log("")
                gui.log(f"Finished in: {pygame.time.get_ticks()-oldtime} ms.")
                gui.log(f"Took {cycles} cycles to complete.")
                return self.reconstruct_path(
                    cameFrom, current
                )  # Recreate path to destination

            currentIDX = openSet.index(current)
            openSet.remove(current)  # Remove current from open set
            openSetFScores.pop(currentIDX)  # And remove its fScore value
            # Go through all valid neighbors
            for neighbor in self.findNeighbors(current):

                currentX, currentY = current
                neighborX, neighborY = neighbor
                if self.grid[neighborY][neighborX] == "#":
                    continue  # if it is a wall, stop
                # Trial_gScore is the distance from the start to the neighbor, through current node
                trial_gScore = gScore[currentY][currentX] + self.calcCost(
                    current, neighbor
                )
                if trial_gScore < gScore[neighborY][neighborX]:
                    # This is the best path so far to the neighbor
                    # Record values
                    cameFrom[neighbor] = current
                    gScore[neighborY][neighborX] = trial_gScore
                    trial_fScore = trial_gScore + self.calcDist(neighbor, dest)
                    fScore[neighborY][neighborX] = trial_fScore

                    if not neighbor in openSet:
                        openSet.append(neighbor)  # Add to set
                        openSetFScores.append(trial_fScore)  # and add value

            cycles += 1
            if cycles > 2500:
                gui.log("")
                gui.log("(blocked off?)")
                gui.log("Path not found.")

                return "Failure"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    global run
                    run = False
                    pygame.quit()
                    return

            # ___----*** VISUALIZE ***----___ #
            if self.visual == False:
                continue

            clock.tick(FPS / 2)  # Render half speed

            self.apply_path_to_grid(
                self.reconstruct_path(cameFrom, current), "@"
            )  # Show changes
            self.render()

            # --- PyGame Display --- #
            pygame.display.update()

        gui.log("")
        gui.log("(blocked off?)")
        gui.log("Path not found.")
        return "Failure"

    def apply_path_to_grid(self, path, value):
        """
        Takes in a list of nodes and applies changes to the grid according to the input.

        Usage: apply_path_to_grid(path, "@")
        """
        if not path:
            return
        for node in path:
            x, y = node
            if self.grid[y][x] != "X" and self.grid[y][x] != "O":
                self.grid[y][x] = value

    def remove_all_of(self, value):
        """
        Removes all instances of a value in the grid.

        Usage: remove_all_of("@")
        """
        rowCount = 0
        for row in self.grid:
            self.grid[rowCount] = [
                x if x != value else "." for x in self.grid[rowCount]
            ]  # removes all of an instance
            rowCount += 1


class GuiState:
    def __init__(self):
        self.root = tk.Tk()
        frame = ttk.Frame(self.root, padding=10)
        frame.grid()

        # Text
        ttk.Label(frame, text="Configure options:").grid(column=0, row=0)
        ttk.Label(frame, text="Heuristic").grid(column=0, row=1)

        # Select heuristic
        self.heuristic = tk.StringVar()
        self.heuristic.set("Manhattan")
        ttk.Combobox(
            frame,
            textvariable=self.heuristic,
            values=("Manhattan", "Euclidean", "Diagonal"),
        ).grid(column=0, row=2)

        # Visualize check box
        self.visualize = tk.StringVar()
        ttk.Checkbutton(
            frame, text="Visualize?", onvalue=True, offvalue="", variable=self.visualize
        ).grid(column=0, row=3)

        # Bounded relaxation/Dynamic weighting

        # Console log
        ttk.Label(frame, text="Console Log:").grid(column=0, row=5)
        self.console = tk.Listbox(frame, height=3, width=25)
        self.console.grid(column=0, row=6)  # MUST BE ON DIFFERENT LINE

        # White space
        ttk.Label(frame, text="             ").grid(column=2, row=0)

        # Text
        ttk.Label(frame, text="Functions:").grid(column=3, row=0)

        # Remove walls button
        ttk.Button(
            frame, text="Remove All Walls", command=lambda: game.remove_all_of("#")
        ).grid(column=3, row=1)

        # Function for removing start/end points
        def remove_start_and_end():
            game.remove_all_of("X")
            game.remove_all_of("O")
            game.remove_all_of("@")
            game.phase = "START"

        # Remove target points
        ttk.Button(
            frame, text="Remove Start and End", command=remove_start_and_end
        ).grid(column=3, row=2)

        # Clipboard copy
        ttk.Button(frame, text="Save to Clipboard", command=game.save_to_clip).grid(
            column=3, row=3
        )

        # Clipboard paste
        ttk.Button(frame, text="Load from Clipboard", command=game.load_from_clip).grid(
            column=3, row=4
        )

        # PATHFIND BUTTON
        boldStyle = ttk.Style()
        boldStyle.configure("Bold.TButton", font=("Sans", "12", "bold"))
        ttk.Button(
            frame,
            text="PATHFIND",
            command=game.pathfinder,
            padding=3,
            style="Bold.TButton",
        ).grid(column=3, row=6)

    def update(self):
        """Update GUI"""
        global METHOD
        global VISUALIZE
        METHOD = self.heuristic.get().replace(" ", "")
        VISUALIZE = self.visualize.get()

        self.root.update()

    def log(self, value):
        """Log a value to the GUI console"""
        self.console.insert(0, value)


# ----- INITIALIZE ------------------------ #


def main():
    """
    Event loop for program.

    Usage: main()
    """
    global run
    if not run:
        return
    # --- Escape condition --- #
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    # --- Game logic --- #
    game.render()

    # --- PyGame Display --- #
    pygame.display.update()
    clock.tick(FPS)  # Set frame rate


game = GameState()
gui = GuiState()
run = True

while run:
    gui.update()  # Update gui
    main()

# ----- END ------------------------ #
pygame.quit()  # Close
