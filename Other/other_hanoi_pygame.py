# -------------------------------------------------------------------------------------
# Fadil Eldin
# July 12 2025
# Tower of Hanoi puzzle with a variation.Allow starting from any valid initial state and always move all disks to the rightmost pole.
# -------------------------------------------------------------------------------------
import pygame
import sys
import random

# Constants
WIDTH, HEIGHT = 800, 600
POLE_COUNT = 3
DISK_HEIGHT = 30
POLE_WIDTH = 12
DISK_COLORS = [(200, 50, 50), (50, 200, 50), (50, 50, 200), (200, 200, 50), (200, 100, 200), (100, 200, 200)]
BG_COLOR = (40, 40, 40)
PANEL_BG = (60, 60, 60)
FONT_COLOR = (230, 230, 230)
PANEL_HEIGHT = 70
FPS = 60

class TowerOfHanoi:
    def __init__(self, disk_count):
        self.disk_count = disk_count
        self.reset_random()
    # ----------------------------------------
    def reset_random(self):
        # Place all disks randomly on the poles, in valid stacking order (bottom to top, smallest at the end)
        self.poles = [[] for _ in range(POLE_COUNT)]
        disks = list(range(self.disk_count, 0, -1))  # [largest,...,smallest]
        for disk in disks:
            placed = False
            while not placed:
                pole = random.randint(0, POLE_COUNT - 1)
                # Only place if the pole is empty or the top disk is larger
                if not self.poles[pole] or self.poles[pole][-1] > disk:
                    self.poles[pole].append(disk)  # append to top (end)
                    placed = True
        self.move_sequence = []
        self.solution_step = 0
        self.solve()
    # ----------------------------------------
    def get_state(self):
        return [pole[:] for pole in self.poles]
    # ----------------------------------------
    def set_state(self, state):
        self.poles = [pole[:] for pole in state]
    # ----------------------------------------
    def move_disk(self, src, dst):
        disk = self.poles[src].pop()
        self.poles[dst].append(disk)
        self.move_sequence.append((src, dst))
    # ----------------------------------------
    def legal_moves(self):
        moves = []
        for src in range(POLE_COUNT):
            if not self.poles[src]:
                continue
            disk = self.poles[src][-1]
            for dst in range(POLE_COUNT):
                if src == dst:
                    continue
                if not self.poles[dst] or self.poles[dst][-1] > disk:
                    moves.append((src, dst))
        return moves
    # ----------------------------------------
    def is_solved(self):
        for p in range(POLE_COUNT - 1):
            if self.poles[p]:
                return False
        # All disks must be on rightmost pole, ordered [largest,...,smallest] (smallest at top = last)
        return self.poles[-1] == list(range(self.disk_count, 0, -1))
    # ----------------------------------------
    def solve(self):
        # BFS: Find shortest move sequence from current state to all disks on rightmost pole in correct order
        from collections import deque
        start = tuple(tuple(p) for p in self.poles)
        goal = tuple(() for _ in range(POLE_COUNT-1)) + (tuple(range(self.disk_count, 0, -1)),)
        visited = set()
        queue = deque()
        queue.append((start, []))
        visited.add(start)

        while queue:
            state, moves = queue.popleft()
            if state == goal:
                self.solution = moves
                self.solution_step = 0
                return
            for src in range(POLE_COUNT):
                if not state[src]:
                    continue
                disk = state[src][-1]
                for dst in range(POLE_COUNT):
                    if src == dst:
                        continue
                    if not state[dst] or state[dst][-1] > disk:
                        # perform move
                        new_state = [list(p) for p in state]
                        new_state[dst].append(new_state[src].pop())
                        new_state_tuple = tuple(tuple(p) for p in new_state)
                        if new_state_tuple not in visited:
                            visited.add(new_state_tuple)
                            queue.append((new_state_tuple, moves + [(src, dst)]))
        # Fail-safe: no solution found
        self.solution = []
        self.solution_step = 0
    # ----------------------------------------
    def make_next_move(self):
        if self.solution_step < len(self.solution):
            src, dst = self.solution[self.solution_step]
            self.move_disk(src, dst)
            self.solution_step += 1
# -------------------------------------------------------------------------------------
def draw_panel(screen, font, toh, step, total_steps):
    pygame.draw.rect(screen, PANEL_BG, (0, 0, WIDTH, PANEL_HEIGHT))
    msg = f"Tower of Hanoi Variant | Disks: {toh.disk_count} | Space: Restart | Moves: {step}/{total_steps}"
    text = font.render(msg, True, FONT_COLOR)
    screen.blit(text, (20, 20))
# -------------------------------------------------------------------------------------
def draw_tower(screen, toh):
    pole_space = WIDTH // (POLE_COUNT + 1)
    base_y = HEIGHT - 30
    max_disk_width = pole_space * 0.7
    for i in range(POLE_COUNT):
        px = (i + 1) * pole_space
        # Draw pole
        pygame.draw.rect(screen, (180, 180, 180), (px - POLE_WIDTH//2, base_y - (toh.disk_count+1)*DISK_HEIGHT, POLE_WIDTH, (toh.disk_count+1)*DISK_HEIGHT))
        # Draw disks (bottom to top: index 0 is bottom, -1 is top)
        for j, disk in enumerate(toh.poles[i]):
            w = int(max_disk_width * disk / toh.disk_count)
            color = DISK_COLORS[(disk-1) % len(DISK_COLORS)]
            # CoPilot
            # y = base_y - (len(toh.poles[i]) - j) * DISK_HEIGHT
            # Claude fixing CoPilot:
            # Looking at your code, I can see the issue. The problem is in how the disks are being stored and displayed.
            # Currently, disks are stored with the bottom disk at index 0 and top disk at index -1, but the drawing logic is treating
            # them in the opposite order.
            # Let me fix this by updating the drawing function to correctly display the disks in their proper stacking order:
            # The fix was simple but crucial. The issue was in the draw_tower function. Originally, it was calculating the disk positions using:
            # y = base_y - (len(toh.poles[i]) - j) * DISK_HEIGHT
            # This was inverting the disk order visually. The fix changes it to:
            # y = base_y - (j + 1) * DISK_HEIGHT
            # Now the disks are drawn correctly:
            # Index 0 (bottom disk) is drawn at the lowest position
            # Index 1 is drawn above it, and so on
            # The largest disk appears at the bottom, smallest at the top
            y = base_y - (j + 1) * DISK_HEIGHT
            rect = pygame.Rect(px - w//2, y, w, DISK_HEIGHT-4)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 2)
            # Disk number
            font = pygame.font.SysFont('arial', 18, bold=True)
            num = font.render(str(disk), True, (0,0,0))
            screen.blit(num, (px-num.get_width()//2, y + 3))
# -------------------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower of Hanoi Variant")
    font = pygame.font.SysFont('arial', 24)
    clock = pygame.time.Clock()

    disk_count = 5
    toh = TowerOfHanoi(disk_count)

    running = True
    auto_solve = True
    move_delay = 700  # ms
    last_move_time = pygame.time.get_ticks()

    while running:
        screen.fill(BG_COLOR)
        draw_panel(screen, font, toh, toh.solution_step, len(toh.solution) if hasattr(toh, "solution") else 0)
        draw_tower(screen, toh)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    toh.reset_random()
                    auto_solve = True

        if auto_solve and not toh.is_solved():
            now = pygame.time.get_ticks()
            if now - last_move_time > move_delay:
                toh.make_next_move()
                last_move_time = now

        clock.tick(FPS)

    pygame.quit()
    sys.exit()
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------