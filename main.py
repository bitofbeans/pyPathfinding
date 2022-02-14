from math import sqrt
import pygame

# Uses the A* pathfinding algorithm #

METHOD = "Manhattan"
'METHOD = "Euclidean"'


def calcDist(start, end):
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
                elif self.grid[y][x] == "X":
                    color = (255, 33, 107)
                # Render square
                pygame.draw.rect(screen, color, self.square, border_radius=2)

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
