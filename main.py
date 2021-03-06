from math import sqrt
import tkinter as tk  # Gui
from tkinter import ttk  # Gui
import pygame  # Main Window
import clipboard  # Copy and Paste
from tktooltip import ToolTip  # Tool tips
import colorsys as colors

DYNAMIC_WEIGHT = False
OPTIMALITY_BOUND = 10
METHOD = "Manhattan"

"""
A great help from:
    https://www.movingai.com/SAS/SUB/
    https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html#S7
    https://en.wikipedia.org/wiki/A*_search_algorithm
"""


# ----- CONSTANTS ------------------------ #
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FPS = 120  # Frames per second
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
    (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 10)
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


# ----- CLASSES -------------------------- #


class GameState:
    """
    Object that stores the current state of the game, including the grid,
    and functions for rendering, and inputs.
    """

    def __init__(self):

        self.grid = [
            [0 for col in range(COLS)] for row in range(ROWS)
        ]  # Create empty grid

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

        for y in range(COLS):
            for x in range(ROWS):
                # pos= position---margin---offset------
                posx = x * self.size + x * SPACE + 5  # Position X
                posy = y * self.size + y * SPACE + 5  # Position Y
                tile = Tile((posx, posy), (x, y), self.size, self)
                self.grid[y][x] = tile

    def render(self):
        """
        Draws screen and handles inputs
        """
        self.flatGrid = self.flatten(self.grid)
        self.hasPath = "@" in self.flatGrid
        self.mousePos = pygame.mouse.get_pos()
        self.mouseClicked = pygame.mouse.get_pressed()

        if self.phase == "BUSY":
            return

        for row in self.grid:
            for tile in row:
                tile.update()  # Update tile

                if tile.get_val() == "O":
                    self.start = tile.get_coords()
                if tile.get_val() == "X":
                    self.dest = tile.get_coords()

                tile.draw()

    def pathfinder(self):
        self.remove_all_of("@")  # Clear path that was there
        temp = self.phase
        # Verify a start and end has been chosen
        try:
            if len(self.start) > 0 and len(self.dest) > 0:
                pass
        except AttributeError:
            gui.log("")
            gui.log("have not been chosen.")
            gui.log("Start and end points")
            return

        self.phase = "BUSY"
        path = self.A_Star(self.start, self.dest)  # Returns a path to destination
        self.phase = temp
        self.visual = False
        if path == "Failure":
            return  # If failed, stop

        self.remove_all_of("@")  # Clear path if was visualized
        self.apply_path_to_grid(path, "@")  # Show path on screen

    def flatten(self, array):
        """Flatten a 2D array"""
        return [item.get_val() for row in array for item in row]

    def save_to_clip(self):
        """
        Turns a grid to a string and copies it to the clipboard
        """
        code = self.grid  # Copy
        code = self.flatten(code)  # Flatten
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
                self.grid[y][x].set_val(code[i])
        self.remove_all_of("@")  # Incase it contains the path

    def heuristic(self, start, end):
        """
        Usage: Tuple inputs for start and end coords.
        Calculate distance from point to point.
        Used to calculate "H" in A* algorithm.

        METHODS: ---------------------------------

        Manhattan Method:
            h= |xstart - xdestination| + |ystart - ydestination|

        Euclidean Method:
            h= sqrt of ( xstart - xdestination )^2+( ystart - ydestination )^2

        Chebyshev Method:
            D = 1 and D2 = 1:
                dx = abs(node.x - goal.x)
                dy = abs(node.y - goal.y)
                h = D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

        Octile Method:
            D = 1 and D2 = sqrt(2):
                dx = abs(node.x - goal.x)
                dy = abs(node.y - goal.y)
                h = D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)
        WEIGHTING: -------------------------------
        USES:

        Weighted A* (pwXD)
            [h > g]: f = g+h; [h ??? g]: f = (g+(2w-1)h)/w
        """
        x_start, y_start = start
        x_end, y_end = end

        if METHOD == "Manhattan":
            h = abs(x_start - x_end) + abs(y_start - y_end)
        elif METHOD == "Euclidean":
            h = sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)
        elif METHOD == "Chebyshev":
            dx = abs(x_start - x_end)
            dy = abs(y_start - y_end)
            D = 1
            D2 = 1
            h = D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)
        elif METHOD == "Octile Dist":
            dx = abs(x_start - x_end)
            dy = abs(y_start - y_end)
            D = 1
            D2 = sqrt(2)
            h = D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)
            # h = D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)
        elif METHOD == "Dijkstra":
            h = 0
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
            return sqrt(2)

    def findNeighbors(self, node):
        def tryAdd(nx, ny):
            if self.grid[ny][nx].get_val() != "#":  # If it is not a wall,
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

        ## heuristic() is used as h() ##
        ## Inspired by https://en.wikipedia.org/wiki/A*_search_algorithm
        # Tuples unpacked to coordinates
        startX, startY = start
        # The set of discovered nodes that may need to be (re-)expanded.
        # Initially, only the start node is known.
        # This is usually implemented as a min-heap or priority queue rather than a hash-set.
        openSet = [start]
        openSetFScores = [self.heuristic(start, dest)]

        # For node n, cameFrom[n] is the node immediately preceding it
        # on the cheapest path from start to n currently known.
        cameFrom = {}

        # The set of discovered nodes
        closedSet = [start]

        # For node n, gScore[n] is the cost of the cheapest path from
        # start to n currently known.
        gScore = [[99999 for col in range(COLS)] for row in range(ROWS)]
        gScore[startY][startX] = 0

        # For node n, fScore[n] := gScore[n] + h(n). fScore[n] represents our
        # current best guess as to how short a path from start to finish can
        # be if it goes through n.
        fScore = [[99999 for col in range(COLS)] for row in range(ROWS)]
        fScore[startY][startX] = self.heuristic(start, dest)

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
                path = self.reconstruct_path(cameFrom, current)

                gui.log("")
                gui.log(f"{pygame.time.get_ticks()-oldtime} ms, {cycles} cycles")
                gui.log(f"Path is {self.get_length_of_path(path)} blocks long.")
                return path  # Recreate path to destination

            currentIDX = openSet.index(current)
            openSet.remove(current)  # Remove current from open set
            openSetFScores.pop(currentIDX)  # And remove its fScore value
            # Go through all valid neighbors
            for neighbor in self.findNeighbors(current):
                if neighbor in closedSet:
                    continue
                closedSet.append(neighbor)

                currentX, currentY = current
                neighborX, neighborY = neighbor
                if self.grid[neighborY][neighborX].get_val() == "#":
                    continue  # if it is a wall, stop
                # tempG is the distance from the start to the neighbor, through current node
                tempG = gScore[currentY][currentX] + self.calcCost(current, neighbor)
                if tempG < gScore[neighborY][neighborX]:
                    # This is the best path so far to the neighbor
                    # Record values
                    cameFrom[neighbor] = current
                    gScore[neighborY][neighborX] = tempG
                    if not DYNAMIC_WEIGHT:
                        tempF = tempG + self.heuristic(neighbor, dest)
                    else:
                        """
                        (A* pwXD)
                        [h > g]: f = g+h;
                        [h ??? g]: f = (g+(2w-1)h)/w
                        """
                        tempH = self.heuristic(neighbor, dest)
                        if tempH > tempG:
                            tempF = tempG + tempH
                        else:
                            w = OPTIMALITY_BOUND
                            tempF = (tempG + (2 * w - 1) * tempH) / w

                    fScore[neighborY][neighborX] = tempF

                    if not neighbor in openSet:
                        openSet.append(neighbor)  # Add to set
                        openSetFScores.append(tempF)  # and add value

            cycles += 1
            if cycles > ROWS * COLS * 10:
                gui.log("")
                gui.log("(blocked off?)")
                gui.log("Path took too long.")

                return "Failure"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    global run
                    run = False
                    pygame.quit()
                    raise SystemExit()

            # ___----*** VISUALIZE ***----___ #
            if self.visual == False:
                continue

            clock.tick(30)  # Render half speed

            self.apply_path_to_grid(
                self.reconstruct_path(cameFrom, current), "@"
            )  # Show changes
            self.render()

            # --- PyGame Display --- #
            pygame.display.update()
            gui.update()

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
            if self.grid[y][x].get_val() != "X" and self.grid[y][x].get_val() != "O":
                self.grid[y][x].set_val(value)

    def remove_all_of(self, value):
        """
        Removes all instances of a value in the grid.

        Usage: remove_all_of("@")
        """
        for row in self.grid:
            for tile in row:
                if tile.get_val() == value:
                    tile.set_val(".")

    def get_length_of_path(self, path):
        length = 0
        oldnode = path[0]
        for node in path:
            if node == path[0]:
                continue
            length += self.calcCost(oldnode, node)
            oldnode = node

        return round(length * 1000) / 1000  # Round to nearest 100


class Tile:

    BORDER_RADIUS = 2

    def __init__(self, screenPos, gridPos, size, game):
        self.game = game

        self.xpos, self.ypos = screenPos
        self.gridx, self.gridy = gridPos
        self.size = size
        self.value = "."

        self.square = pygame.rect.Rect(self.xpos, self.ypos, self.size, self.size)

    def update(self):
        """
        Usage: tile.update((mouseClicked, mousePos), gamePhase, gridValues, hasPath, clicked)
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

        if (
            self.square.collidepoint(self.game.mousePos) and self.game.mouseClicked[0]
        ):  # If clicked
            if self.game.hasPath:
                self.game.remove_all_of("@")
            if self.value != "X" and self.value != "O":  # And empty space

                if not self.game.clicked:
                    if not "O" in self.game.flatGrid:
                        self.value = "O"
                        self.game.phase = "DEST"
                        gui.log("")
                        gui.log("")
                        gui.log("Click a tile as an end point.")
                    elif not "X" in self.game.flatGrid:
                        self.value = "X"
                        self.game.phase = "WALLS"
                        gui.log("")
                        gui.log("Right click to delete barriers.")
                        gui.log("Left click to add barriers.")

                elif self.game.phase == "WALLS":
                    self.value = "#"

                self.game.clicked = True
        elif self.square.collidepoint(self.game.mousePos) and self.game.mouseClicked[2]:
            self.value = "."

        if self.game.mouseClicked[0] == False:
            self.game.clicked = False

    def draw(self):
        if self.value == ".":
            color = DGREY
        elif self.value == "#":
            color = LGREY
        elif self.value == "O":
            color = (3, 252, 161)
        elif self.value == "X":
            color = (255, 33, 107)
        elif self.value == "@":
            dist = self.game.heuristic(self.get_coords(), self.game.dest)

            if self.game.visual == True:
                h = (dist) / 360
                s = 0.84
                v = 1
                r, g, b = colors.hsv_to_rgb(h, s, v)
                r *= 255
                g *= 255
                b *= 255
                color = (r, g, b)
            else:
                color = (90, 150, 255)
        # Render square
        pygame.draw.rect(
            screen,
            color,
            self.square,
            border_radius=2 if self.value != "@" else 10,
        )

    def set_val(self, value):
        self.value = value

    def get_val(self):
        return self.value

    def get_coords(self):
        return (self.gridx, self.gridy)


class GuiState:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pathfinder GUI")
        frame = ttk.Frame(self.root, padding=10)
        frame.grid()

        bigStyle = ttk.Style()
        bigStyle.configure("Options.TLabel", font=("Sans", "10", "bold"))

        # Text
        ttk.Label(frame, text="Configure options:", style="Options.TLabel").grid(
            column=0, row=0
        )
        ttk.Label(frame, text="Algorithm:").grid(column=0, row=1)

        # Select heuristic
        self.heuristic = tk.StringVar()
        self.heuristic.set("A*: Manhattan")
        self.heur_box = ttk.Combobox(
            frame,
            textvariable=self.heuristic,
            values=(
                "A*: Manhattan",
                "A*: Octile Dist",
                "A*: Euclidean",
                "A*: Chebyshev",
                "Dijkstra",
            ),
        )
        self.heur_box.grid(column=0, row=2)
        ToolTip(
            self.heur_box,
            msg="Select a pathfinding algorithm to use. \n\nManhattan and Octile are usually the most efficient.",
        )

        # Visualize check box
        self.visualize = tk.StringVar()
        self.visual_box = ttk.Checkbutton(
            frame, text="Visualize?", onvalue=True, offvalue="", variable=self.visualize
        )
        self.visual_box.grid(column=0, row=3)
        ToolTip(self.visual_box, msg="Visualize the pathfinding process step-by-step.")

        # Bounded relaxation/Dynamic weighting
        self.dyn_weight = tk.StringVar()
        self.dyn_weight_box = ttk.Checkbutton(
            frame, text="A* Dynamic Weighting?", offvalue="", variable=self.dyn_weight
        )
        self.dyn_weight_box.grid(column=0, row=4)
        ToolTip(
            self.dyn_weight_box,
            msg="Enable weighted A* (using pwXD) \nUsually always speeds up process, but may lead to a suboptimal path.",
        )

        # Console log
        ttk.Label(frame, text="Console Log:", style="Options.TLabel").grid(
            column=0, row=5
        )
        self.console = tk.Listbox(frame, height=3, width=25)
        self.console.grid(column=0, row=6)  # MUST BE ON DIFFERENT LINE
        ToolTip(self.console, msg="Events will be shown here.")

        # White space
        ttk.Label(frame, text="      ").grid(column=2, row=0)

        # Text
        ttk.Label(frame, text="Functions:", style="Options.TLabel").grid(
            column=3, row=0
        )

        # Remove walls button
        self.wall_button = ttk.Button(
            frame, text="Remove All Walls", command=lambda: game.remove_all_of("#")
        )
        self.wall_button.grid(column=3, row=1)

        # Function for removing start/end points
        def remove_start_and_end():
            game.remove_all_of("X")
            game.remove_all_of("O")
            game.remove_all_of("@")
            game.phase = "START"
            if hasattr(game, "start"):
                del game.start
            if hasattr(game, "dest"):
                del game.dest

        # Remove target points
        self.start_end_button = ttk.Button(
            frame, text="Remove Start and End", command=remove_start_and_end
        )
        self.start_end_button.grid(column=3, row=2)

        # Clipboard copy
        self.save_button = ttk.Button(
            frame, text="Save to Clipboard", command=game.save_to_clip
        )
        self.save_button.grid(column=3, row=3)

        # Clipboard paste
        self.load_button = ttk.Button(
            frame, text="Load from Clipboard", command=game.load_from_clip
        )
        self.load_button.grid(column=3, row=4)

        # PATHFIND BUTTON
        boldStyle = ttk.Style()
        boldStyle.configure("Bold.TButton", font=("Sans", "12", "bold"))
        self.path_button = ttk.Button(
            frame,
            text="PATHFIND",
            command=game.pathfinder,
            padding=3,
            style="Bold.TButton",
        )
        self.path_button.grid(column=3, row=6)
        ToolTip(self.path_button, msg="Start pathfinding process.")

        self.widgets = [
            self.wall_button,
            self.start_end_button,
            self.save_button,
            self.load_button,
            self.path_button,
            self.dyn_weight_box,
            self.visual_box,
            self.heur_box,
        ]
        self.log("")
        self.log("")
        self.log("Click a tile as an start point.")

        self.disabled = False

    def update(self):
        """Update GUI"""
        if game.phase == "BUSY":  # If currently pathfinding
            # Disable all widgets
            for widget in self.widgets:
                self._config_widget_state(widget, tk.DISABLED)
            self.disabled = True
            self.root.update()
            return  # Stop

        if self.disabled:  # If widgets are disabled, enable them
            for widget in self.widgets:
                self._config_widget_state(widget, "")

        global METHOD
        global VISUALIZE
        global DYNAMIC_WEIGHT
        method = self.heuristic.get().replace(" ", "")
        if "Manhattan" in method:
            METHOD = "Manhattan"

        if "Euclidean" in method:
            METHOD = "Euclidean"

        if "OctileDist" in method:
            METHOD = "Octile Dist"

        if "Chebyshev" in method:
            METHOD = "Chebyshev"

        if "Dijkstra" in method:
            METHOD = "Dijkstra"
            self.dyn_weight.set("")  # Set it to blank
            self._config_widget_state(
                self.dyn_weight_box, tk.DISABLED
            )  # Disable check box
        else:
            self._config_widget_state(self.dyn_weight_box, "")

        VISUALIZE = self.visualize.get()
        DYNAMIC_WEIGHT = self.dyn_weight.get()

        self.root.update()

    def log(self, value):
        """Log a value to the GUI console"""
        self.console.insert(0, value)

    def _config_widget_state(self, widget, state):

        try:
            widget.config(state=state)
        except tk.TclError:
            raise SystemExit()  # If gui window is closed


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
