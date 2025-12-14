from typing import List, Tuple, Optional

# Constants
BOARD_SIZE = 19
EMPTY = 0
WHITE = 1  # Player 1 (Starts)
BLACK = 2  # Player 2

class PenteGame:
    def __init__(self, tournament_rule: bool = False):
        self.grid = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.move_count = 0
        self.captures = {WHITE: 0, BLACK: 0} 
        self.capture_history = [] 
        self.tournament_rule = tournament_rule 
        self.last_move = None
        self.winner = None
        self.winning_sequence = []

    def is_valid_move(self, row: int, col: int, player: int) -> bool:
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.grid[row][col] == EMPTY):
            return False

        if self.tournament_rule and self.move_count == 2: 
             pass
        return True

    def make_move(self, row: int, col: int, player: int) -> bool:
        if self.is_valid_move(row, col, player):
            self.grid[row][col] = player
            self.last_move = (row, col)
            self.move_count += 1
            
            self.check_and_capture(row, col, player)
            self.update_winner(player)
            return True
        return False

    def undo_move(self, row: int, col: int):
        self.grid[row][col] = EMPTY
        self.move_count -= 1
        self.winner = None
        self.winning_sequence = []
        
        if self.capture_history:
            capture_info = self.capture_history.pop()
            if capture_info:
                opponent = capture_info['opponent']
                for r, c in capture_info['stones']:
                    self.grid[r][c] = opponent
                self.captures[capture_info['player']] -= capture_info['count']

    def get_candidate_moves(self, radius: int = 2) -> List[Tuple[int, int]]:
        if self.move_count == 0:
            return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
        
        candidates = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] != EMPTY:
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < BOARD_SIZE and 
                                0 <= nc < BOARD_SIZE and 
                                self.grid[nr][nc] == EMPTY):
                                candidates.add((nr, nc))
        return list(candidates)

    def check_and_capture(self, r: int, c: int, player: int):
        opponent        = 3 - player 
        captured_count  = 0
        captured_stones = [] 
        directions      = [(0, 1), (1, 0), (1, 1), (1, -1)] 
        
        for dr, dc in directions:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            r3, c3 = r + 3 * dr, c + 3 * dc
            
            if self._is_on_board(r3, c3):
                if (self.grid[r1][c1] == opponent and 
                    self.grid[r2][c2] == opponent and 
                    self.grid[r3][c3] == player):
                    
                    self.grid[r1][c1] = EMPTY
                    self.grid[r2][c2] = EMPTY
                    captured_stones.append((r1, c1))
                    captured_stones.append((r2, c2))
                    captured_count += 1

            r1, c1 = r - dr, c - dc
            r2, c2 = r - 2 * dr, c - 2 * dc
            r3, c3 = r - 3 * dr, c - 3 * dc
            
            if self._is_on_board(r3, c3):
                if (self.grid[r1][c1] == opponent and 
                    self.grid[r2][c2] == opponent and 
                    self.grid[r3][c3] == player):
                    
                    self.grid[r1][c1] = EMPTY
                    self.grid[r2][c2] = EMPTY
                    captured_stones.append((r1, c1))
                    captured_stones.append((r2, c2))
                    captured_count += 1
        
        if captured_count > 0:
            self.captures[player] += captured_count
            self.capture_history.append({
                'player'        : player,
                'opponent'      : opponent,
                'count'         : captured_count,
                'stones'        : captured_stones
            })
        else:
            self.capture_history.append(None)

    def _is_on_board(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def update_winner(self, player):
        if self.captures[player] >= 5: 
            self.winner = player
            return
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] == player:
                    for dr, dc in directions:
                        sequence = [(r, c)]
                        for i in range(1, 5):
                            nr, nc = r + dr * i, c + dc * i
                            if self._is_on_board(nr, nc) and self.grid[nr][nc] == player:
                                sequence.append((nr, nc))
                            else:
                                break
                        
                        if len(sequence) >= 5:
                            self.winner = player
                            self.winning_sequence = sequence
                            return

    def is_full(self):
        return self.move_count >= BOARD_SIZE * BOARD_SIZE

    def reset(self):
        self.__init__(self.tournament_rule)
