import math
import random
import time
from typing import Tuple, List, Optional
from game_logic import BOARD_SIZE, EMPTY, WHITE, BLACK

WIN_SCORE       = 10000000
OPEN_FOUR       = 100000
CLOSED_FOUR     = 50000 
OPEN_THREE      = 10000
CLOSED_THREE    = 1000 
OPEN_TWO        = 100
CAPTURE_SCORE   = 50000 

class PenteAI:
    def __init__(self, mode: str = 'alphabeta_h2', player_color: int = BLACK, depth: int = 2):
        self.mode = mode
        self.player_color = player_color
        self.opponent_color = 3 - player_color
        self.depth = depth
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.start_time = 0
        self.time_limit = 5.0 

    def get_best_move(self, board) -> Tuple[int, int]:
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.start_time = time.time()

        forced_move = self._find_immediate_forced_move(board)
        if forced_move:
            print(f"AI found forced move: {forced_move}")
            return forced_move

        if self.mode == 'minimax_h1':
            return self.minimax_h1(board, self.depth)
        elif self.mode == 'minimax_h2':
            return self.minimax_h2(board, self.depth)
        elif self.mode == 'alphabeta_h1':
            return self.alphabeta_h1(board, self.depth)
        elif self.mode == 'alphabeta_h2':
            return self.alphabeta_h2(board, self.depth)
        else:
            return self.alphabeta_h2(board, self.depth)

    def heuristic_1(self, board, player: int) -> int:
        score = 0
        opponent = 3 - player
        score += (board.captures[player] - board.captures[opponent]) * CAPTURE_SCORE
        my_patterns  = self._evaluate_patterns(board, player)
        opp_patterns = self._evaluate_patterns(board, opponent)
        score += my_patterns * 1.5 
        score -= opp_patterns * 0.8
        return score

    def heuristic_2(self, board, player: int) -> int:
        score = 0
        opponent = 3 - player
        center = BOARD_SIZE // 2

        if board.winner == player:
            return WIN_SCORE
        if board.winner == opponent:
            return -WIN_SCORE

        score += (board.captures[player] - board.captures[opponent]) * (CAPTURE_SCORE // 2)

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    dist = abs(r - center) + abs(c - center)
                    score += (20 - dist) 

        my_patterns = self._evaluate_patterns(board, player)
        opp_patterns = self._evaluate_patterns(board, opponent)

        score += my_patterns * 1.0
        score -= opp_patterns * 1.2 

        return score

    def _evaluate_patterns(self, board, player: int) -> int:
        score = 0
        opponent = 3 - player
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    for dr, dc in directions:
                        prev_r, prev_c = r - dr, c - dc
                        if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE and board.grid[prev_r][prev_c] == player:
                            continue
                        score += self._score_sequence(board, r, c, dr, dc, player, opponent)
        return score

    def _score_sequence(self, board, r, c, dr, dc, player, opponent) -> int:
        length = 0
        gaps = 0
        
        for i in range(5):
            nr, nc = r + dr*i, c + dc*i
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break 
            
            cell = board.grid[nr][nc]
            if cell == player:
                length += 1
            elif cell == EMPTY:
                gaps += 1 
                break 
            else: 
                break

        open_start = False
        pr, pc = r - dr, c - dc
        if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board.grid[pr][pc] == EMPTY:
            open_start = True

        open_end = False
        er, ec = r + dr*length, c + dc*length
        if 0 <= er < BOARD_SIZE and 0 <= ec < BOARD_SIZE and board.grid[er][ec] == EMPTY:
            open_end = True

        if length == 5:
            return WIN_SCORE 
        
        if length == 4:
            if open_start and open_end: return OPEN_FOUR
            if open_start or open_end: return CLOSED_FOUR
        
        if length == 3:
            if open_start and open_end: return OPEN_THREE
            if open_start or open_end: return CLOSED_THREE

        if length == 2:
            if open_start and open_end: return OPEN_TWO

        return 0

    def minimax_h1(self, board, depth: int) -> Tuple[int, int]:
        _, move = self._minimax_recursive(board, depth, True, self.heuristic_1)
        return move

    def minimax_h2(self, board, depth: int) -> Tuple[int, int]:
        _, move = self._minimax_recursive(board, depth, True, self.heuristic_2)
        return move

    def _minimax_recursive(self, board, depth, maximizing, h_func):
        self.nodes_explored += 1
        
        winner = board.winner
        if winner == self.player_color: return WIN_SCORE, None
        if winner == self.opponent_color: return -WIN_SCORE, None
        if depth == 0:
            return h_func(board, self.player_color), None

        candidates = self._get_smart_candidates(board)
        if not candidates:
            return 0, None

        best_move = candidates[0]

        if maximizing:
            max_eval = -math.inf
            for r, c in candidates:
                board.make_move(r, c, self.player_color)
                eval_val, _ = self._minimax_recursive(board, depth-1, False, h_func)
                board.undo_move(r, c)
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = (r, c)
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in candidates:
                board.make_move(r, c, self.opponent_color)
                eval_val, _ = self._minimax_recursive(board, depth-1, True, h_func)
                board.undo_move(r, c)
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = (r, c)
            return min_eval, best_move

    def alphabeta_h1(self, board, depth: int) -> Tuple[int, int]:
        _, move = self._alphabeta_recursive(board, depth, -math.inf, math.inf, True, self.heuristic_1)
        return move

    def alphabeta_h2(self, board, depth: int) -> Tuple[int, int]:
        _, move = self._alphabeta_recursive(board, depth, -math.inf, math.inf, True, self.heuristic_2)
        return move

    def _alphabeta_recursive(self, board, depth, alpha, beta, maximizing, h_func):
        self.nodes_explored += 1
        
        winner = board.winner
        if winner == self.player_color: return WIN_SCORE, None
        if winner == self.opponent_color: return -WIN_SCORE, None
        if depth == 0:
            return h_func(board, self.player_color), None

        candidates = self._get_smart_candidates(board)
        if not candidates:
            return 0, None

        best_move = candidates[0]

        if maximizing:
            max_eval = -math.inf
            for r, c in candidates:
                board.make_move(r, c, self.player_color)
                eval_val, _ = self._alphabeta_recursive(board, depth-1, alpha, beta, False, h_func)
                board.undo_move(r, c)
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = (r, c)
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in candidates:
                board.make_move(r, c, self.opponent_color)
                eval_val, _ = self._alphabeta_recursive(board, depth-1, alpha, beta, True, h_func)
                board.undo_move(r, c)
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = (r, c)
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return min_eval, best_move

    def _get_smart_candidates(self, board) -> List[Tuple[int, int]]:
        if board.move_count == 0:
            return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
        
        candidates = set()
        rad = 2
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] != EMPTY:
                    for dr in range(-rad, rad+1):
                        for dc in range(-rad, rad+1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        return list(candidates)

    def _find_immediate_forced_move(self, board) -> Optional[Tuple[int, int]]:
        candidates = self._get_smart_candidates(board)
        opponent = self.opponent_color

        for r, c in candidates:
            board.make_move(r, c, self.player_color)
            if board.winner == self.player_color:
                board.undo_move(r, c)
                return (r, c)
            board.undo_move(r, c)
            
        for r, c in candidates:
            board.make_move(r, c, opponent)
            if board.winner == opponent:
                board.undo_move(r, c)
                return (r, c)
            board.undo_move(r, c)

        return None