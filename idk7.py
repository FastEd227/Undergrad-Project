import random
import pygame
import math
from enum import Enum
from typing import List, Dict, Tuple

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000  # Increased width to add space for stats
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Catan Game Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
COLORS = {
    "wood": (34, 139, 34),  # Forest Green
    "brick": (178, 34, 34),  # Firebrick
    "sheep": (144, 238, 144),  # Light Green
    "wheat": (255, 223, 0),  # Gold
    "ore": (128, 128, 128),  # Gray
    "desert": (245, 222, 179),  # Wheat
}

# Hexagon constants
HEX_RADIUS = 50
HEX_HEIGHT = math.sqrt(3) * HEX_RADIUS
HEX_WIDTH = 2 * HEX_RADIUS
HEX_SPACING_X = HEX_WIDTH  # Increased horizontal spacing
HEX_SPACING_Y = HEX_HEIGHT  # Increased vertical spacing

# Enum to represent resources
class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"
    DESERT = "desert"

# Tile class to represent each hex tile
class Tile:
    def __init__(self, resource: Resource, number: int, position: int):
        self.resource = resource
        self.number = number
        self.position = position

# CatanBoard class to handle the board and game mechanics
class CatanBoard:
    def __init__(self, tiles: List[Tile], board_layout: List[List[int]]):
        self.tiles = {tile.position: tile for tile in tiles}
        self.players = []
        self.current_turn = 0
        self.board_layout = board_layout  # Store the board layout

    def add_player(self, player: "Player"):
        self.players.append(player)

    def roll_dice(self):
        return random.randint(1, 6) + random.randint(1, 6)

    def distribute_resources(self, roll: int):
        for tile in self.tiles.values():
            if tile.number == roll:
                for player in self.players:
                    for settlement in player.settlements:
                        if settlement in self.get_tile_vertices(tile.position):
                            player.resources[tile.resource] += 1

    def get_tile_vertices(self, tile_pos: int) -> List[Tuple[float, float]]:
        """
        Get the vertices of a tile based on its position.
        """
        for row_index, row in enumerate(self.board_layout):
            if tile_pos in row:
                col_index = row.index(tile_pos)
                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                center_x = col_index * HEX_SPACING_X + stagger_offset
                center_y = row_index * HEX_SPACING_Y
                return calculate_hexagon_vertices(center_x, center_y)
        return []

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def get_current_player(self):
        return self.players[self.current_turn]

# Updated Player class to include road-building logic
class Player:
    def __init__(self, name: str, game_board: CatanBoard, color):
        self.name = name
        self.color = color  # Player color for settlements, roads, and cities
        self.resources = {
            Resource.WOOD: 3,  # Starting resources for AI
            Resource.BRICK: 3,
            Resource.SHEEP: 3,
            Resource.WHEAT: 3,
            Resource.ORE: 3,
        }
        self.settlements = []
        self.roads = []
        self.cities = []  # New attribute for cities
        self.victory_points = 0
        self.game_board = game_board

    def build_settlement(self, position: Tuple[float, float]):
        self.settlements.append(position)
        self.resources[Resource.WOOD] -= 1
        self.resources[Resource.BRICK] -= 1
        self.resources[Resource.SHEEP] -= 1
        self.resources[Resource.WHEAT] -= 1
        self.calculate_victory_points()

    def build_road(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float]):
        if (start_pos, end_pos) not in self.roads and (end_pos, start_pos) not in self.roads:
            self.roads.append((start_pos, end_pos))
            self.resources[Resource.WOOD] -= 1
            self.resources[Resource.BRICK] -= 1

    def build_city(self, position: Tuple[float, float]):
        if position in self.settlements:
            self.settlements.remove(position)
            self.cities.append(position)
            self.resources[Resource.WHEAT] -= 2
            self.resources[Resource.ORE] -= 3
            self.calculate_victory_points()

    def calculate_victory_points(self):
        self.victory_points = len(self.settlements) + 2 * len(self.cities)  # 1 point per settlement, 2 per city

# Function to handle road placement
def handle_road_placement(player, start_pos, end_pos, board_layout):
    # Ensure the tiles are adjacent
    start_x, start_y = get_tile_center(start_pos, board_layout)
    end_x, end_y = get_tile_center(end_pos, board_layout)
    distance = math.sqrt((start_x - end_x) ** 2 + (start_y - end_y) ** 2)

    if distance <= HEX_SPACING_X:  # Tiles are adjacent
        # Ensure the road connects to an existing settlement or road
        if start_pos in player.settlements or end_pos in player.settlements or \
           any(start_pos in road or end_pos in road for road in player.roads):
            player.build_road(start_pos, end_pos)
            print(f"{player.name} built a road between {start_pos} and {end_pos}")
        else:
            print(f"{player.name} cannot build a road here. It must connect to a settlement or road.")
    else:
        print("The selected tiles are not adjacent.")

# Function to handle starting settlement placement
def handle_starting_settlement(player, position, board_layout):
    """
    Handles the placement of a starting settlement.
    """
    # Ensure the position is valid and not already occupied
    if position in player.settlements or any(position in p.settlements for p in board.players):
        print(f"Position {position} is already occupied by a settlement.")
        return False

    # Place the settlement
    player.build_settlement(position)
    print(f"{player.name} placed a starting settlement at position {position}.")
    return True

# Function to handle starting road placement
def handle_starting_road(player, start_vertex, end_vertex, board_layout):
    """
    Handles the placement of a starting road between two vertices.
    """
    # Ensure the vertices are valid and adjacent
    start_x, start_y = start_vertex
    end_x, end_y = end_vertex
    distance = math.sqrt((start_x - end_x) ** 2 + (start_y - end_y) ** 2)

    if distance <= HEX_SPACING_X:  # Vertices are adjacent
        # Ensure the road connects to the settlement just placed or an existing road
        if start_vertex in player.settlements or end_vertex in player.settlements or \
           any(start_vertex in road or end_vertex in road for road in player.roads):
            # Check if the road already exists
            if (start_vertex, end_vertex) in player.roads or (end_vertex, start_vertex) in player.roads:
                print(f"A road already exists between {start_vertex} and {end_vertex}.")
                return False

            player.build_road(start_vertex, end_vertex)
            print(f"{player.name} placed a starting road between {start_vertex} and {end_vertex}.")
            return True
        else:
            print(f"{player.name} cannot place a road here. It must connect to a settlement or road.")
    else:
        print("The selected vertices are not adjacent.")
    return False

# Function to roll the dice and distribute resources
def roll_dice_and_distribute(board):
    dice_roll = random.randint(1, 6) + random.randint(1, 6)
    print(f"Dice rolled: {dice_roll}")
    board.distribute_resources(dice_roll)
    return dice_roll

# Initialize the game board
tiles = [
    Tile(Resource.WOOD, 5, 1), Tile(Resource.BRICK, 9, 2), Tile(Resource.SHEEP, 11, 3),
    Tile(Resource.ORE, 8, 4), Tile(Resource.WHEAT, 10, 5), Tile(Resource.WOOD, 4, 6),
    Tile(Resource.BRICK, 7, 7), Tile(Resource.ORE, 6, 8), Tile(Resource.WHEAT, 12, 9),
    Tile(Resource.SHEEP, 3, 10), Tile(Resource.ORE, 2, 11), Tile(Resource.SHEEP, 6, 12),
    Tile(Resource.WOOD, 8, 13), Tile(Resource.BRICK, 4, 14), Tile(Resource.WHEAT, 3, 15),
    Tile(Resource.ORE, 9, 16), Tile(Resource.WOOD, 10, 17), Tile(Resource.BRICK, 2, 18),
    Tile(Resource.SHEEP, 5, 19),
]

board_layout = [
    [None, None, 1, 2, 3, None, None],
    [None, 4, 5, 6, 7, None, None],
    [None, 8, 9, 10, 11, 12, None],
    [None, 13, 14, 15, 16, None, None],
    [None, None, 17, 18, 19, None, None],
]

board = CatanBoard(tiles, board_layout)

# Add players to the game board
player1 = Player("Player 1", board, (255, 0, 0))  # Red
player2 = Player("AI 1", board, (0, 255, 0))  # Green
player3 = Player("AI 2", board, (0, 0, 255))  # Blue

board.add_player(player1)
board.add_player(player2)
board.add_player(player3)

# Helper function to calculate hexagon vertices
def calculate_hexagon_vertices(center_x, center_y):
    """
    Calculate the six vertices of a hexagon given its center coordinates.
    """
    vertices = []
    for i in range(6):
        angle_deg = 60 * i - 30  # Start at the top-right vertex
        angle_rad = math.radians(angle_deg)
        x = center_x + HEX_RADIUS * math.cos(angle_rad)
        y = center_y + HEX_RADIUS * math.sin(angle_rad)
        vertices.append((x, y))
    return vertices

# Function to calculate edge midpoints of a hexagon
def calculate_hexagon_edges(vertices):
    edges = []
    for i in range(len(vertices)):
        start = vertices[i]
        end = vertices[(i + 1) % len(vertices)]  # Wrap around to the first vertex
        midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        edges.append(midpoint)
    return edges

# Draw a hexagon
def draw_hexagon(surface, center_x, center_y, color, outline_color=BLACK):
    vertices = calculate_hexagon_vertices(center_x, center_y)
    pygame.draw.polygon(surface, color, vertices)
    pygame.draw.polygon(surface, outline_color, vertices, 2)

# Draw the board
def draw_board(surface, board_layout, tiles):
    board_width = len(board_layout[2]) * HEX_SPACING_X
    board_height = len(board_layout) * HEX_SPACING_Y
    offset_x = (SCREEN_WIDTH - 200 - board_width) // 2  # Adjusted for stats sidebar
    offset_y = (SCREEN_HEIGHT - board_height) // 2

    for row_index, row in enumerate(board_layout):
        for col_index, tile_pos in enumerate(row):
            if tile_pos is not None:
                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                center_x = offset_x + col_index * HEX_SPACING_X + stagger_offset
                center_y = offset_y + row_index * HEX_SPACING_Y
                if 1 <= tile_pos <= len(tiles):
                    tile = tiles[tile_pos - 1]
                    draw_hexagon(surface, center_x, center_y, COLORS[tile.resource.value])
                    font = pygame.font.Font(None, 24)
                    text = font.render(f"{tile.resource.name.capitalize()}", True, BLACK)
                    surface.blit(text, (center_x - text.get_width() // 2, center_y - 20))
                    number_text = font.render(f"{tile.number}", True, BLACK)
                    surface.blit(number_text, (center_x - number_text.get_width() // 2, center_y + 10))

# Draw player stats
def draw_stats(surface, players):
    font = pygame.font.Font(None, 24)
    x_offset = SCREEN_WIDTH - 200  # Sidebar position
    y_offset = 20

    pygame.draw.rect(surface, GRAY, (x_offset, 0, 200, SCREEN_HEIGHT))  # Sidebar background

    for player in players:
        text = font.render(f"{player.name}", True, BLACK)
        surface.blit(text, (x_offset + 10, y_offset))
        y_offset += 30

        for resource, amount in player.resources.items():
            resource_text = font.render(f"{resource.name.capitalize()}: {amount}", True, BLACK)
            surface.blit(resource_text, (x_offset + 10, y_offset))
            y_offset += 20

        vp_text = font.render(f"Victory Points: {player.victory_points}", True, BLACK)
        surface.blit(vp_text, (x_offset + 10, y_offset))
        y_offset += 40

# Adjusted get_tile_center function for staggered grid
def get_tile_center(pos, board_layout):
    # Calculate the offset to center the board
    board_width = len(board_layout[2]) * HEX_SPACING_X  # Center based on the widest row
    board_height = len(board_layout) * HEX_SPACING_Y
    offset_x = (SCREEN_WIDTH - board_width) // 2
    offset_y = (SCREEN_HEIGHT - board_height) // 2

    for row_index, row in enumerate(board_layout):
        if pos in row:
            col_index = row.index(pos)
            # Adjust the x-coordinate for staggered rows
            stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
            center_x = offset_x + col_index * HEX_SPACING_X + stagger_offset
            center_y = offset_y + row_index * HEX_SPACING_Y
            return center_x, center_y
    return None, None

# Draw settlements, roads, and cities on vertices and edges
def draw_game_elements(surface, players, board_layout):
    """
    Draw settlements, roads, and cities on the hexagon vertices and edges.
    """
    for player in players:
        # Draw settlements
        for settlement_pos in player.settlements:
            x, y = settlement_pos
            pygame.draw.circle(surface, BLACK, (int(x), int(y)), 10)  # Settlement as a small circle
            pygame.draw.circle(surface, player.color, (int(x), int(y)), 8)  # Player color inside

        # Draw roads
        for road in player.roads:
            start_pos, end_pos = road
            pygame.draw.line(surface, player.color, start_pos, end_pos, 5)  # Road as a thick line

        # Draw cities
        for city_pos in player.cities:
            x, y = city_pos
            pygame.draw.circle(surface, BLACK, (int(x), int(y)), 15)  # City as a larger circle
            pygame.draw.circle(surface, player.color, (int(x), int(y)), 13)  # Player color inside

# Function to draw the "Roll Dice" button
def draw_roll_dice_button(surface):
    button_rect = pygame.Rect(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 80, 160, 50)  # Button dimensions
    pygame.draw.rect(surface, GRAY, button_rect)  # Button background
    pygame.draw.rect(surface, BLACK, button_rect, 2)  # Button border

    font = pygame.font.Font(None, 30)
    text = font.render("Roll Dice", True, BLACK)
    surface.blit(text, (button_rect.x + (button_rect.width - text.get_width()) // 2,
                        button_rect.y + (button_rect.height - text.get_height()) // 2))
    return button_rect

# Function to draw the "Next Turn" button
def draw_next_turn_button(surface):
    button_rect = pygame.Rect(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 140, 160, 50)  # Button dimensions
    pygame.draw.rect(surface, GRAY, button_rect)  # Button background
    pygame.draw.rect(surface, BLACK, button_rect, 2)  # Button border

    font = pygame.font.Font(None, 30)
    text = font.render("Next Turn", True, BLACK)
    surface.blit(text, (button_rect.x + (button_rect.width - text.get_width()) // 2,
                        button_rect.y + (button_rect.height - text.get_height()) // 2))
    return button_rect

def player_can_build_settlement(player, position):
    """
    Check if the player can build a settlement at the given position.
    """
    # Required resources for a settlement
    required_resources = {Resource.WOOD: 1, Resource.BRICK: 1, Resource.SHEEP: 1, Resource.WHEAT: 1}

    # Check if the player has enough resources
    if all(player.resources[resource] >= amount for resource, amount in required_resources.items()):
        # Check if the position is valid (not already occupied)
        if position not in player.settlements and position not in player.cities and \
           all(position not in p.settlements for p in player.game_board.players):
            return True
    return False

def player_can_build_road(player, start_pos, end_pos):
    """
    Check if the player can build a road between the given positions.
    """
    # Required resources for a road
    required_resources = {Resource.WOOD: 1, Resource.BRICK: 1}

    # Check if the player has enough resources
    if all(player.resources[resource] >= amount for resource, amount in required_resources.items()):
        # Check if the road is valid (not already occupied)
        if (start_pos, end_pos) not in player.roads and (end_pos, start_pos) not in player.roads:
            # Ensure the road connects to the player's own settlements or roads
            if start_pos in player.settlements or end_pos in player.settlements or \
               any(start_pos in road or end_pos in road for road in player.roads):
                return True
    return False

def player_can_build_city(player, position):
    """
    Check if the player can build a city at the given position.
    """
    # Required resources for a city
    required_resources = {Resource.WHEAT: 2, Resource.ORE: 3}

    # Check if the player has enough resources
    if all(player.resources[resource] >= amount for resource, amount in required_resources.items()):
        # Check if the position already has a settlement
        if position in player.settlements:
            return True
    return False

def attempt_to_build_settlement(player, board_layout):
    """
    Attempt to build a settlement for the AI player.
    """
    for row_index, row in enumerate(board_layout):
        if row is None:
            continue
        for col_index, tile_pos in enumerate(row):
            if tile_pos is not None:  # Only consider valid tiles
                # Calculate hexagon center
                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                center_x = (col_index * HEX_SPACING_X) + stagger_offset + (SCREEN_WIDTH - len(board_layout[2]) * HEX_SPACING_X) // 2
                center_y = (row_index * HEX_SPACING_Y) + (SCREEN_HEIGHT - len(board_layout) * HEX_SPACING_Y) // 2

                # Get vertices of the hexagon
                vertices = calculate_hexagon_vertices(center_x, center_y)

                # Check for a valid settlement position
                for vertex in vertices:
                    if player_can_build_settlement(player, vertex):
                        player.build_settlement(vertex)
                        print(f"{player.name} built a settlement at {vertex}")
                        return True  # End turn after building a settlement
    return False

def attempt_to_build_road(player, board_layout):
    """
    Attempt to build a road for the AI player.
    """
    for row_index, row in enumerate(board_layout):
        if row is None:
            continue
        for col_index, tile_pos in enumerate(row):
            if tile_pos is not None:  # Only consider valid tiles
                # Calculate hexagon center
                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                center_x = (col_index * HEX_SPACING_X) + stagger_offset + (SCREEN_WIDTH - len(board_layout[2]) * HEX_SPACING_X) // 2
                center_y = (row_index * HEX_SPACING_Y) + (SCREEN_HEIGHT - len(board_layout) * HEX_SPACING_Y) // 2

                # Get vertices and edges of the hexagon
                vertices = calculate_hexagon_vertices(center_x, center_y)
                edges = [(vertices[i], vertices[(i + 1) % len(vertices)]) for i in range(len(vertices))]

                # Check for a valid road position
                for start_vertex, end_vertex in edges:
                    if (start_vertex in player.settlements or end_vertex in player.settlements) and \
                       player_can_build_road(player, start_vertex, end_vertex):
                        player.build_road(start_vertex, end_vertex)
                        print(f"{player.name} built a road between {start_vertex} and {end_vertex}")
                        return True  # End turn after building a road
    return False

def attempt_to_build_city(player):
    """
    Attempt to build a city for the AI player.
    """
    for settlement in player.settlements:
        if player_can_build_city(player, settlement):
            player.build_city(settlement)
            print(f"{player.name} upgraded a settlement to a city at {settlement}")
            return True  # End turn after building a city
    return False

def ai_take_turn(player, board_layout):
    """
    AI logic for taking a turn.
    """
    print(f"{player.name}'s turn (AI)")

    # Roll the dice
    dice_roll = roll_dice_and_distribute(board)
    print(f"{player.name} rolled a {dice_roll}")

    # Attempt to build a settlement
    if not attempt_to_build_settlement(player, board_layout):
        # Attempt to build a road
        if not attempt_to_build_road(player, board_layout):
            # Attempt to build a city
            if not attempt_to_build_city(player):
                print(f"{player.name} could not perform any actions this turn.")

# Updated main game loop with vertex-based settlements and edge-based roads
def main():
    running = True
    starting_phase = True  # Flag for the starting placement phase
    selected_vertex = None  # To track the first vertex clicked for road placement
    current_player_index = 0  # Track which player's turn it is
    last_dice_roll = None  # Store the last dice roll result
    wait_for_next_turn = True  # Flag to wait for "Next Turn" button click

    while running:
        screen.fill(WHITE)
        draw_board(screen, board_layout, tiles)
        draw_stats(screen, board.players)
        draw_game_elements(screen, board.players, board_layout)  # Draw settlements, roads, and cities

        # Draw the "Next Turn" button
        next_turn_button = draw_next_turn_button(screen)

        # Display the last dice roll result
        if last_dice_roll is not None:
            font = pygame.font.Font(None, 36)
            dice_text = font.render(f"Dice Roll: {last_dice_roll}", True, BLACK)
            screen.blit(dice_text, (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Check if the "Next Turn" button was clicked
                if next_turn_button.collidepoint(mouse_x, mouse_y):
                    wait_for_next_turn = False  # Allow the next turn to proceed

        # Handle AI turns
        if not wait_for_next_turn:
            player = board.players[current_player_index]
            if starting_phase:
                # Starting phase logic for AI
                if selected_vertex is None:
                    # Place starting settlement
                    for row_index, row in enumerate(board_layout):
                        if row is None:
                            continue
                        for col_index, tile_pos in enumerate(row):
                            if tile_pos is not None:
                                # Calculate hexagon center
                                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                                center_x = (col_index * HEX_SPACING_X) + stagger_offset + (SCREEN_WIDTH - len(board_layout[2]) * HEX_SPACING_X) // 2
                                center_y = (row_index * HEX_SPACING_Y) + (SCREEN_HEIGHT - len(board_layout) * HEX_SPACING_Y) // 2

                                # Get vertices of the hexagon
                                vertices = calculate_hexagon_vertices(center_x, center_y)

                                # Check for a valid settlement position
                                for vertex in vertices:
                                    if handle_starting_settlement(player, vertex, board_layout):
                                        selected_vertex = vertex  # Save the settlement position
                                        print(f"{player.name} placed a starting settlement at {vertex}")
                                        break
                            if selected_vertex is not None:
                                break
                        if selected_vertex is not None:
                            break
                else:
                    # Place starting road
                    for row_index, row in enumerate(board_layout):
                        if row is None:
                            continue
                        for col_index, tile_pos in enumerate(row):
                            if tile_pos is not None:
                                # Calculate hexagon center
                                stagger_offset = (row_index % 2) * (HEX_SPACING_X / 2)
                                center_x = (col_index * HEX_SPACING_X) + stagger_offset + (SCREEN_WIDTH - len(board_layout[2]) * HEX_SPACING_X) // 2
                                center_y = (row_index * HEX_SPACING_Y) + (SCREEN_HEIGHT - len(board_layout) * HEX_SPACING_Y) // 2

                                # Get vertices of the hexagon
                                vertices = calculate_hexagon_vertices(center_x, center_y)

                                # Check for a valid road position
                                for vertex in vertices:
                                    if handle_starting_road(player, selected_vertex, vertex, board_layout):
                                        selected_vertex = None  # Reset selection
                                        current_player_index = (current_player_index + 1) % len(board.players)
                                        if current_player_index == 0:
                                            starting_phase = False  # End starting phase after all players finish
                                        print(f"{player.name} placed a starting road.")
                                        break
                            if selected_vertex is None:
                                break
                        if selected_vertex is None:
                            break
            else:
                # Main gameplay logic for AI
                ai_take_turn(player, board_layout)
                current_player_index = (current_player_index + 1) % len(board.players)

            # Reset the flag to wait for the next turn
            wait_for_next_turn = True

        # Check for victory condition
        for player in board.players:
            if player.victory_points >= 10:
                print(f"{player.name} wins the game!")
                running = False

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()