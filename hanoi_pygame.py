# -------------------------------------------------------------------------------------
# Fadil Eldin
# July 12 2025
# Tower of Hanoi puzzle with a variation.Allow starting from any valid initial state and always move all disks to the rightmost pole.
# Two modes:
# 1) Manual: Play and solve the puzzle yourself by moving disks.
# 2) Auto: Watch the shortest solution found for the current state.
# Optimal Moves Calculation: Shows the minimal number of moves required from the current state (using BFS).
# Scoring: Get a score based on how close you are to the optimal solution.
# Interactive GUI: Click to select and move disks, or use buttons to switch modes or start a new game.
# Customizable Disk Count: Easily modify the number of disks between 3 and 8.
# -------------------------------------------------------------------------------------
import pygame
import sys
import random
import time
from typing import List, Tuple, Optional
import collections
import math

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
POLE_COUNT = 3
POLE_COLOR = (200, 200, 200)  # Light gray poles
DISK_COLORS = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (173, 216, 230),  # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
    (255, 128, 0),  # Orange
    (128, 0, 128),  # Purple
]
BACKGROUND_COLOR = (50, 50, 50)  # Dark gray background
TEXT_COLOR = (255, 255, 255)  # White text
PANEL_COLOR = (80, 80, 80)  # Darker gray panel
BUTTON_COLOR = (100, 100, 100)  # Gray for buttons
BUTTON_HOVER_COLOR = (120, 120, 120)  # Lighter gray for button hover

# Auto-solve speed control
MIN_AUTO_DELAY = 0.1   # Fastest speed (100ms between moves)
MAX_AUTO_DELAY = 2.0   # Slowest speed (2 seconds between moves)
AUTO_DELAY_STEP = 0.1  # Speed adjustment increment

# Disk settings
MAX_DISKS = 8
MIN_DISKS = 3
DISK_HEIGHT = 30
MIN_DISK_WIDTH = 40
DISK_WIDTH_INCREMENT = 20
# -------------------------------------------------------------------------------------
class Disk:
    def __init__(self, size: int, color: Tuple[int, int, int]):
        self.size = size
        self.color = color
        self.width = MIN_DISK_WIDTH + (size - 1) * DISK_WIDTH_INCREMENT
        self.selected = False
        self.auto_move_delay = 0.5  # Default speed (medium)
    # ----------------------------------------
    def draw(self, screen, x: int, y: int, font):
        # Draw disk rectangle
        pygame.draw.rect(screen, self.color, (x, y, self.width, DISK_HEIGHT))

        # Draw disk border
        pygame.draw.rect(screen, (0, 0, 0), (x, y, self.width, DISK_HEIGHT), 1)

        # Draw number on disk
        number_text = font.render(str(self.size), True, (0, 0, 0))  # Black numbers for contrast
        text_rect = number_text.get_rect(center=(x + self.width // 2, y + DISK_HEIGHT // 2))
        screen.blit(number_text, text_rect)

        # Draw selection highlight
        if self.selected:
            pygame.draw.rect(screen, (255, 255, 0), (x - 2, y - 2, self.width + 4, DISK_HEIGHT + 4), 2)
# -------------------------------------------------------------------------------------
class Pole:
    def __init__(self, x: int):
        self.x = x
        self.disks: List[Disk] = []
    # ----------------------------------------
    def add_disk(self, disk: Disk):
        self.disks.append(disk)
    # ----------------------------------------
    def remove_disk(self) -> Disk:
        if self.disks:
            return self.disks.pop()
        return None
    # ----------------------------------------
    def top_disk(self) -> Optional[Disk]:
        if self.disks:
            return self.disks[-1]
        return None
    # ----------------------------------------
    def is_valid(self) -> bool:
        # Check if disks are in correct order (smallest on top)
        for i in range(1, len(self.disks)):
            if self.disks[i].size < self.disks[i - 1].size:
                return False
        return True
# -------------------------------------------------------------------------------------
class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
    # ----------------------------------------
    def draw(self, screen, font):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)  # Border

        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    # ----------------------------------------
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    # ----------------------------------------
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False
# -------------------------------------------------------------------------------------
class HanoiGame:
    def __init__(self, disk_count: int = 5):
        self.disk_count = disk_count
        self.poles = [Pole((i + 1) * SCREEN_WIDTH // (POLE_COUNT + 1)) for i in range(POLE_COUNT)]
        self.selected_pole = None
        self.moves = 0
        self.font = pygame.font.SysFont('Arial', 20)
        self.disk_font = pygame.font.SysFont('Arial', 16)
        self.mode = "manual"  # "manual" or "auto"
        self.auto_solving = False
        self.auto_move_delay = 0.5  # seconds between auto moves
        self.last_auto_move_time = 0
        self.move_sequence = []
        self.optimal_moves = 0
        self.user_score = 0
        self.solved = False
        
        # Win message display control
        self.show_win_message_flag = False
        self.win_message_start_time = 0
        self.win_message_duration = 3.0  # seconds

        # Buttons
        button_width = 120
        button_height = 30
        self.auto_solve_button = Button(20, 80, button_width, button_height, "Auto Solve")
        self.manual_solve_button = Button(160, 80, button_width, button_height, "Manual Solve")
        self.new_game_button = Button(300, 80, button_width, button_height, "New Game")

        self.generate_random_initial_state()
    # ----------------------------------------
    def adjust_speed(self, increase: bool):
        """Adjust auto-solve speed using arrow keys"""
        if increase:
            self.auto_move_delay = max(MIN_AUTO_DELAY, self.auto_move_delay - AUTO_DELAY_STEP)
        else:
            self.auto_move_delay = min(MAX_AUTO_DELAY, self.auto_move_delay + AUTO_DELAY_STEP)

        # Show speed change feedback
        speed_multiplier = 1 / self.auto_move_delay
        print(f"Auto-solve speed: {speed_multiplier:.1f}x speed ({self.auto_move_delay:.1f}s delay)")
    # ----------------------------------------
    def generate_random_initial_state(self):
        # Clear all poles
        for pole in self.poles:
            pole.disks = []

        # Create disks
        disks = [Disk(size + 1, DISK_COLORS[size % len(DISK_COLORS)]) for size in range(self.disk_count)]

        # Distribute disks randomly across poles while maintaining valid state
        for disk in reversed(disks):  # Start with largest disk
            valid_poles = []
            for pole in self.poles:
                if not pole.disks or pole.top_disk().size > disk.size:
                    valid_poles.append(pole)

            if valid_poles:
                random.choice(valid_poles).add_disk(disk)

        # Make sure at least one disk is not on the rightmost pole
        if len(self.poles[-1].disks) == self.disk_count:
            # Move one disk to another pole
            disk_to_move = self.poles[-1].remove_disk()
            self.poles[0].add_disk(disk_to_move)

        self.moves = 0
        self.selected_pole = None
        self.auto_solving = False
        self.move_sequence = []
        self.optimal_moves = self.calculate_optimal_moves()
        self.user_score = 0
        self.solved = False
        self.show_win_message_flag = False
        self.win_message_start_time = 0
    # ----------------------------------------
    def calculate_optimal_moves(self) -> int:
        """
        Calculate the minimal moves needed to solve from current state using BFS.
        Returns the number of moves in the optimal solution.
        """
        # Represent the state as a tuple of tuples (for hashing)
        initial_state = tuple(tuple(disk.size for disk in pole.disks) for pole in self.poles)
        goal_state = ((), (), tuple(range(self.disk_count, 0, -1)))

        # If already in goal state, no moves needed
        if initial_state == goal_state:
            return 0

        # BFS setup
        queue = collections.deque([(initial_state, 0)])
        visited = {initial_state}

        while queue:
            current_state, moves = queue.popleft()

            # Check if we've reached the goal
            if current_state == goal_state:
                return moves

            # Generate all possible next states
            for src in range(3):
                if not current_state[src]:  # No disks to move from this pole
                    continue

                # We can only move the top disk
                disk_size = current_state[src][-1]

                for dst in range(3):
                    if src == dst:
                        continue  # Can't move to same pole

                    # Check if move is valid (empty destination or larger disk)
                    if not current_state[dst] or current_state[dst][-1] > disk_size:
                        # Create new state
                        new_state = list(list(pole) for pole in current_state)
                        disk = new_state[src].pop()
                        new_state[dst].append(disk)
                        new_state_tuple = tuple(tuple(pole) for pole in new_state)

                        # If we haven't seen this state before
                        if new_state_tuple not in visited:
                            visited.add(new_state_tuple)
                            queue.append((new_state_tuple, moves + 1))

        return -1  # Should never happen for valid initial states
    # ----------------------------------------
    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        # Draw panel
        pygame.draw.rect(screen, PANEL_COLOR, (10, 10, 780, 110))

        # Prepare mode-specific instructions
        mode_instructions = ""
        if self.mode == "auto" and self.auto_solving:
            mode_instructions = "↑/↓: Change speed"
        elif self.mode == "manual":
            mode_instructions = "Click poles to move disks"

        # Draw game info (two lines)
        mode_text = "Auto" if self.mode == "auto" else "Manual"
        info_line1 = self.font.render(
            f"Moves: {self.moves} | Disks: {self.disk_count} | Mode: {mode_text} | "
            f"Optimal: {self.optimal_moves} | Score: {self.user_score}%",
            True, TEXT_COLOR
        )

        info_line2 = self.font.render(
            f"Speed: {1 / self.auto_move_delay:.1f}x | {mode_instructions} | "
            f"Goal: Move all disks to rightmost pole",
            True, TEXT_COLOR
        )

        screen.blit(info_line1, (20, 20))
        screen.blit(info_line2, (20, 45))

        # Draw buttons
        self.auto_solve_button.draw(screen, self.font)
        self.manual_solve_button.draw(screen, self.font)
        self.new_game_button.draw(screen, self.font)

        # Draw poles (without bases)
        pole_height = SCREEN_HEIGHT - 350
        pole_width = 10
        pole_y_start = SCREEN_HEIGHT - 100 - pole_height

        for pole in self.poles:
            # Draw pole stand only (vertical line)
            pygame.draw.rect(screen, POLE_COLOR,
                             (pole.x - pole_width // 2, pole_y_start,
                              pole_width, pole_height))

            # Draw disks
            for i, disk in enumerate(pole.disks):
                disk_y = SCREEN_HEIGHT - 100 - (i + 1) * DISK_HEIGHT
                disk_x = pole.x - disk.width // 2
                disk.draw(screen, disk_x, disk_y, self.disk_font)

        # Draw win message if needed
        if self.show_win_message_flag:
            self.draw_win_message(screen)
    # ----------------------------------------
    def draw_win_message(self, screen):
        """Draw the win message overlay"""
        # Calculate performance rating
        rating = ""
        if self.moves == self.optimal_moves:
            rating = "Perfect! You matched the optimal solution!"
        elif self.moves <= self.optimal_moves * 1.2:
            rating = "Excellent! Very close to optimal!"
        elif self.moves <= self.optimal_moves * 1.5:
            rating = "Good! You can still improve."
        else:
            rating = "Keep practicing! Try to find more efficient solutions."

        # Create a surface for the win message
        msg_surface = pygame.Surface((600, 100))
        msg_surface.fill(PANEL_COLOR)
        pygame.draw.rect(msg_surface, TEXT_COLOR, msg_surface.get_rect(), 2)

        # Render text lines
        line1 = self.font.render(f"Solved in {self.moves} moves (optimal: {self.optimal_moves})", True, TEXT_COLOR)
        line2 = self.font.render(f"Score: {self.user_score}% - {rating}", True, TEXT_COLOR)

        # Center the message on screen
        msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        # Blit everything
        screen.blit(msg_surface, msg_rect)
        screen.blit(line1, (msg_rect.x + 20, msg_rect.y + 20))
        screen.blit(line2, (msg_rect.x + 20, msg_rect.y + 50))
    # ----------------------------------------
    def handle_click(self, pos, event):
        # Check buttons first
        if self.auto_solve_button.is_clicked(pos, event):
            self.set_mode("auto")
            return
        elif self.manual_solve_button.is_clicked(pos, event):
            self.set_mode("manual")
            return
        elif self.new_game_button.is_clicked(pos, event):
            self.generate_random_initial_state()
            return

        # Handle pole clicks only in manual mode
        if self.mode != "manual" or self.auto_solving:
            return

        x, y = pos

        # Check if click is on a pole
        for i, pole in enumerate(self.poles):
            if abs(x - pole.x) < 50 and y > SCREEN_HEIGHT - 400:
                if self.selected_pole is None:
                    # Select the pole if it has disks
                    if pole.disks:
                        self.selected_pole = i
                        pole.top_disk().selected = True
                else:
                    # Try to move disk from selected pole to this pole
                    if self.selected_pole != i:
                        self.move_disk(self.selected_pole, i)

                    # Deselect in any case
                    if self.selected_pole is not None and self.poles[self.selected_pole].disks:
                        self.poles[self.selected_pole].top_disk().selected = False
                    self.selected_pole = None
                break
    # ----------------------------------------
    def set_mode(self, mode: str):
        self.mode = mode
        if mode == "auto":
            self.prepare_auto_solve()
    # ----------------------------------------
    def prepare_auto_solve(self):
        """
        Use BFS to find the shortest sequence of moves from the current state to the goal.
        """
        self.move_sequence = []
        self.auto_solving = True
        self.last_auto_move_time = time.time()

        # Represent the state as a tuple of tuples (for hashing)
        initial_state = tuple(tuple(disk.size for disk in pole.disks) for pole in self.poles)
        goal_state = ((), (), tuple(range(self.disk_count, 0, -1)))

        # If already in goal state, do nothing
        if initial_state == goal_state:
            return

        # BFS setup
        queue = collections.deque([initial_state])
        visited = {initial_state: None}  # state -> (prev_state, move)
        found = False

        while queue:
            current_state = queue.popleft()

            # Check if we've reached the goal
            if current_state == goal_state:
                found = True
                break

            # Generate all possible next states
            for src in range(3):
                if not current_state[src]:  # No disks to move from this pole
                    continue

                # We can only move the top disk
                disk_size = current_state[src][-1]

                for dst in range(3):
                    if src == dst:
                        continue  # Can't move to same pole

                    # Check if move is valid (empty destination or larger disk)
                    if not current_state[dst] or current_state[dst][-1] > disk_size:
                        # Create new state
                        new_state = list(list(pole) for pole in current_state)
                        disk = new_state[src].pop()
                        new_state[dst].append(disk)
                        new_state_tuple = tuple(tuple(pole) for pole in new_state)

                        # If we haven't seen this state before
                        if new_state_tuple not in visited:
                            visited[new_state_tuple] = (current_state, (src, dst))
                            queue.append(new_state_tuple)

        if found:
            # Reconstruct the path
            path = []
            state = goal_state
            while visited[state] is not None:
                prev_state, move = visited[state]
                path.append(move)
                state = prev_state

            # Reverse to get from initial to goal
            self.move_sequence = list(reversed(path))
        else:
            print("No solution found!")
            self.auto_solving = False
    # ----------------------------------------
    def update(self):
        # Handle win message timing
        if self.show_win_message_flag:
            current_time = time.time()
            if current_time - self.win_message_start_time >= self.win_message_duration:
                self.show_win_message_flag = False

        # Handle auto-solving
        if self.mode == "auto" and self.auto_solving and self.move_sequence:
            current_time = time.time()
            if current_time - self.last_auto_move_time >= self.auto_move_delay:
                source, target = self.move_sequence.pop(0)
                self.move_disk(source, target)
                self.last_auto_move_time = current_time

                # Check if we're done
                if not self.move_sequence:
                    self.auto_solving = False
    # ----------------------------------------
    def move_disk(self, from_pole_idx: int, to_pole_idx: int):
        from_pole = self.poles[from_pole_idx]
        to_pole = self.poles[to_pole_idx]

        if not from_pole.disks:
            return False

        disk_to_move = from_pole.top_disk()

        # Check if move is valid
        if to_pole.disks and to_pole.top_disk().size < disk_to_move.size:
            return False

        # Perform the move
        from_pole.remove_disk()
        to_pole.add_disk(disk_to_move)
        self.moves += 1

        # Check for win condition (all disks on rightmost pole)
        if len(self.poles[-1].disks) == self.disk_count and not self.solved:
            self.solved = True
            self.calculate_user_score()
            # Start showing win message (non-blocking)
            self.show_win_message_flag = True
            self.win_message_start_time = time.time()

        return True
    # ----------------------------------------
    def calculate_user_score(self):
        """Calculate user's score based on moves taken vs optimal moves"""
        if self.optimal_moves > 0:
            # Score is percentage where optimal moves = 100%
            # Minimum score is 100% (if user matches optimal)
            # Higher moves give lower percentage
            self.user_score = min(100, int((self.optimal_moves / max(1, self.moves)) * 100))
        else:
            self.user_score = 100  # If optimal is 0 (already solved)
    # ----------------------------------------
    def is_valid_state(self) -> bool:
        for pole in self.poles:
            if not pole.is_valid():
                return False
        return True
# -------------------------------------------------------------------------------------
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower of Hanoi with Random Initial State")

    clock = pygame.time.Clock()

    disk_count = 5  # Default number of disks
    game = HanoiGame(disk_count)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        game.auto_solve_button.check_hover(mouse_pos)
        game.manual_solve_button.check_hover(mouse_pos)
        game.new_game_button.check_hover(mouse_pos)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.generate_random_initial_state()
                elif event.key == pygame.K_UP:  # Speed up
                    game.adjust_speed(True)
                elif event.key == pygame.K_DOWN:  # Slow down
                    game.adjust_speed(False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(mouse_pos, event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.generate_random_initial_state()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(mouse_pos, event)

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ---------------------------------END-------------------------------------------------