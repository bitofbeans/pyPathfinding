from math import sqrt, inf
from copy import deepcopy
import pygame


# Uses the A* pathfinding algorithm #

METHOD = "Manhattan"
'METHOD = "Euclidean"'

# ----- CONSTANTS ------------------------ #
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
FPS = 60  # Frames per second

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LGREY = (200, 200, 200)
DGREY = (100, 100, 100)
FONT = (60, 80, 105)
FONT_ALT = (90, 160, 90)

ROWS = 50
COLS = 50
SPACE = int(1)  # Space between tiles
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

        self.grid = [[" " for col in range(COLS)] for row in range(ROWS)]  # Create grid

        self.phase = "START"

        # Fit whichever value is bigger to screen
        if ROWS > COLS:
            self.size = SCREEN_WIDTH / ROWS
        else:
            self.size = SCREEN_HEIGHT / COLS

        self.size = int(self.size - SPACE)  # Round and account for spacing

        self.clicked = False
        self.square = 0

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
                if self.grid[y][x] == " ":
                    color = DGREY
                elif self.grid[y][x] == "#":
                    color = LGREY
                elif self.grid[y][x] == "O":
                    color = (3, 252, 161)
                    start = (x,y)
                elif self.grid[y][x] == "X":
                    color = (255, 33, 107)
                    dest = (x,y)
                # Render square
                pygame.draw.rect(screen, color, self.square, border_radius=2)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            print(self.A_Star(start, dest))

    def updateTile(self, pos):

        """
        Usage: squareLogic((x,y), square, mouseClicked, mousePos)
        Handles inputs to each square

            " " = Empty space
            "#" = Wall/Barrier
            "O" = Start
            "X" = Destination
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
            if self.grid[y][x] == " ":  # And empty space

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
        """
        x_start, y_start = start
        x_end, y_end = end

        if METHOD == "Manhattan":
            h = abs(x_start - x_end) + abs(y_start - y_end)
        elif METHOD == "Euclidean":
            h = sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)
        else:
            raise SystemError("Not a valid method")
        return h

    def calcCost(self, start, end):
        sx, sy = start
        ex, ey = end
        if (sx is ex) or (sy is ey):
            return 1.0
        else:
            return 1.41

    def findNeighbors(self, node):
        def tryAdd(nx, ny):
            try:
                if self.grid[ny][nx]  != "#":  # If it is not a wall,
                    neighbors.append((nx, ny))  # add to neighbors list
            except:
                pass

        neighbors = []
        x, y = node
        if not x == 0:  # Account for left edge
            tryAdd(x - 1, y)  # Left
            # DIAGONALS
            if not y ==  0:  # Account for top edge
                tryAdd(x - 1, y - 1)  # Top
            if not y == 49:  # Account for bottom edge
                tryAdd(x - 1, y + 1)  # Bottom
        if not x ==  49:  # Account for right edge
            tryAdd(x + 1, y)  # Right
            # DIAGONALS
            if not y ==  0:  # Account for top edge
                tryAdd(x + 1, y - 1)  # Top
            if not y ==  49:  # Account for bottom edge
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

        while openSet: # While not empty
            # Find the node in the openSet with the lowest f value
            lowest = 99999
            i = 0  # Start at the end of the list
            for node in openSet:  # Reversed means it reversed the set
                if openSetFScores[i] < lowest:  # If it is the lowest value so far,
                    current = node  # Set the current node to it
                i += 1

            if current == dest:
                # We found the destination
                return self.reconstruct_path(
                    cameFrom, current
                )  # Recreate path to destination

            currentIDX = openSet.index(current)
            openSet.remove(current)
            openSetFScores.pop(currentIDX)
            # Go through all valid neighbors
            for neighbor in self.findNeighbors(current):
                
                currentX, currentY = current
                neighborX, neighborY = neighbor
                if self.grid[neighborY][neighborX] == "#": continue
                # Trial_gScore is the distance from the start to the neighbor, through current node
                trial_gScore = gScore[currentY][currentX] + self.calcCost(
                    current, neighbor
                )
                if trial_gScore < gScore[neighborY][neighborX]:
                    # This is the best path so far to the neighbor
                    cameFrom[neighbor] = current
                    gScore[neighborY][neighborX] = trial_gScore
                    trial_fScore = trial_gScore + self.calcDist(neighbor, dest)
                    fScore[neighborY][neighborX] = trial_fScore

                    if not neighbor in openSet:
                        openSet.append(neighbor)
                        openSetFScores.append(trial_fScore)
        return "Failure"


# ----- INITIALIZE ------------------------ #
game = GameState()
run = True

while run:
    # --- Escape condition --- #
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    # --- Game logic --- #
    game.render()

    # --- PyGame Display --- #
    pygame.display.update()
    clock.tick(FPS)  # Set frame rate

# ----- END ------------------------ #
pygame.quit()  # Close

"""function reconstruct_path(cameFrom, current)
    total_path := {current}
    while current in cameFrom.Keys:
        current := cameFrom[current]
        total_path.prepend(current)
    return total_path

// A* finds a path from start to goal.
// h is the heuristic function. h(n) estimates the cost to reach goal from node n.
function A_Star(start, goal, h)
    // The set of discovered nodes that may need to be (re-)expanded.
    // Initially, only the start node is known.
    // This is usually implemented as a min-heap or priority queue rather than a hash-set.
    openSet := {start}

    // For node n, cameFrom[n] is the node immediately preceding it on the cheapest path from start
    // to n currently known.
    cameFrom := an empty map

    // For node n, gScore[n] is the cost of the cheapest path from start to n currently known.
    gScore := map with default value of Infinity
    gScore[start] := 0

    // For node n, fScore[n] := gScore[n] + h(n). fScore[n] represents our current best guess as to
    // how short a path from start to finish can be if it goes through n.
    fScore := map with default value of Infinity
    fScore[start] := h(start)

    while openSet is not empty
        // This operation can occur in O(1) time if openSet is a min-heap or a priority queue
        current := the node in openSet having the lowest fScore[] value
        if current = goal
            return reconstruct_path(cameFrom, current)

        openSet.Remove(current)
        for each neighbor of current
            // d(current,neighbor) is the weight of the edge from current to neighbor
            // tentative_gScore is the distance from start to the neighbor through current
            tentative_gScore := gScore[current] + d(current, neighbor)
            if tentative_gScore < gScore[neighbor]
                // This path to neighbor is better than any previous one. Record it!
                cameFrom[neighbor] := current
                gScore[neighbor] := tentative_gScore
                fScore[neighbor] := tentative_gScore + h(neighbor)
                if neighbor not in openSet
                    openSet.add(neighbor)

    // Open set is empty but goal was never reached
    return failure"""
