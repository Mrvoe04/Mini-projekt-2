import random
import pygame

VANDRET = 35
LODRET = 35
TILE_SIZE = 20

GRASS_COLOR = (120, 180, 90)
WATER_COLOR = (78, 122, 137)
MOUNTAIN_COLOR = (92, 102, 110)
PATH_COLOR = (255, 0, 0)


class Terrain:
    def __init__(self, color):
        self.color = color


class Grass(Terrain):
    def __init__(self):
        super().__init__(GRASS_COLOR)


class RandomTerrain(Terrain):
    def __init__(self, color, patch_count, radius_x, radius_y):
        super().__init__(color)
        self.patch_count = patch_count
        self.radius_x = radius_x
        self.radius_y = radius_y

    def generate(self, grid):
        for _ in range(self.patch_count):
            center_col = random.randrange(VANDRET)
            center_row = random.randrange(LODRET)

            for row in range(
                max(0, center_row - self.radius_y),
                min(LODRET, center_row + self.radius_y + 1),
            ):
                for col in range(
                    max(0, center_col - self.radius_x),
                    min(VANDRET, center_col + self.radius_x + 1),
                ):
                    dx = (col - center_col) / max(1, self.radius_x)
                    dy = (row - center_row) / max(1, self.radius_y)

                    if dx * dx + dy * dy <= 1:
                        grid[row][col] = self


class Water(RandomTerrain):
    def __init__(self):
        super().__init__(
            color=WATER_COLOR,
            patch_count=random.randint(9, 28),
            radius_x=3,
            radius_y=2,
        )


class Mountain(RandomTerrain):
    def __init__(self):
        super().__init__(
            color=MOUNTAIN_COLOR,
            patch_count=12,
            radius_x=2,
            radius_y=2,
        )


class World:
    """Fælles funktioner for tilfældige kort og sandkassekort."""

    def __init__(self):
        self.grass = Grass()
        self.water = Water()
        self.mountains = Mountain()

        # Alle felter starter som græs.
        self.grid = [
            [self.grass for _ in range(VANDRET)]
            for _ in range(LODRET)
        ]

    def set_terrain(self, position, terrain):
        col, row = position

        if not (0 <= col < VANDRET and 0 <= row < LODRET):
            return

        self.grid[row][col] = terrain

    def draw(self, screen):
        for row in range(LODRET):
            for col in range(VANDRET):
                terrain = self.grid[row][col]
                rect = pygame.Rect(
                    col * TILE_SIZE,
                    row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(screen, terrain.color, rect)

    def draw_path(self, screen, path):
        if len(path) < 2:
            return

        points = [
            (
                col * TILE_SIZE + TILE_SIZE // 2,
                row * TILE_SIZE + TILE_SIZE // 2,
            )
            for col, row in path
        ]

        pygame.draw.lines(screen, PATH_COLOR, False, points, 3)

    def neighbors(self, position):
        col, row = position
        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]

        result = []

        for dx, dy in directions:
            next_col = col + dx
            next_row = row + dy

            if not (0 <= next_col < VANDRET and 0 <= next_row < LODRET):
                continue

            # Forhindrer diagonale skridt gennem blokerede hjørner.
            if dx != 0 and dy != 0:
                side_a = (col + dx, row)
                side_b = (col, row + dy)

                if not (self.is_grass(side_a) and self.is_grass(side_b)):
                    continue

            result.append((next_col, next_row))

        return result

    def movement_cost(self, current, next_position):
        col, row = next_position
        terrain = self.grid[row][col]

        if terrain is self.water:
            terrain_cost = 5
        elif terrain is self.mountains:
            terrain_cost = 10
        else:
            terrain_cost = 1

        diagonal = (
            current[0] != next_position[0]
            and current[1] != next_position[1]
        )

        if diagonal:
            return terrain_cost * 1.414

        return terrain_cost

    def is_grass(self, position):
        col, row = position

        if not (0 <= col < VANDRET and 0 <= row < LODRET):
            return False

        return self.grid[row][col] is self.grass


class RandomWorld(World):
    """Et kort med tilfældigt placeret vand og bjerge."""

    def __init__(self):
        super().__init__()
        self.water.generate(self.grid)
        self.mountains.generate(self.grid)


class SandboxWorld(World):
    """Et tomt kort med græs, som spilleren kan redigere med tastaturet."""

    def __init__(self):
        super().__init__()