import math
import random
import time
from typing import Tuple, List, Optional
from game_logic import BOARD_SIZE, EMPTY, WHITE, BLACK

# =============================================================
# SCORING CONSTANTS
# =============================================================
WIN_SCORE = 10000000
OPEN_FOUR = 100000
CLOSED_FOUR = 50000 # 4 in a row but one end blocked
OPEN_THREE = 10000
CLOSED_THREE = 1000 # Less valuable because it needs 2 moves to become open 4
OPEN_TWO = 100
CAPTURE_SCORE = 50000 # High priority to capture

class PenteAI:
    """
    AI Engine for Pente Game.
    Implements:
    1. Two distinct Heuristic Functions.
    2. Minimax Algorithm (applied with H1 and H2).
    3. Alpha-Beta Pruning (applied with H1 and H2).
    """

    def __init__(self, mode: str = 'alphabeta_h2', player_color: int = BLACK, depth: int = 2):
        self.mode               = mode
        self.player_color       = player_color
        self.opponent_color     = 3 - player_color
        self.depth              = depth
        self.nodes_explored     = 0
        self.pruned_branches    = 0
        self.start_time         = 0
        self.time_limit         = 5.0 

    def get_best_move(self, board) -> Tuple[int, int]:
        """
        Main entry point for the GUI.
        Dispatches the search based on self.mode.
        """
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.start_time = time.time()

        # SUPER CRITICAL: First check for immediate wins or loss preventions (1-ply lookahead)
        # This makes the AI "not stupid" by ensuring it doesn't miss obvious moves while thinking deeply.
        forced_move = self._find_immediate_forced_move(board)
        if forced_move:
            print(f"AI found forced move: {forced_move}")
            return forced_move

        # If no immediate forced move, proceed with deep search
        if self.mode == 'minimax_h1':
            return self.minimax_h1(board, self.depth)
        elif self.mode == 'minimax_h2':
            return self.minimax_h2(board, self.depth)
        elif self.mode == 'alphabeta_h1':
            return self.alphabeta_h1(board, self.depth)
        elif self.mode == 'alphabeta_h2':
            return self.alphabeta_h2(board, self.depth)
        else:
            # Default fallback
            return self.alphabeta_h2(board, self.depth)

    # =============================================================
    # 1. DESIGN OF 2 HEURISTIC FUNCTIONS
    # =============================================================

    def heuristic_1(self, board, player: int) -> int:
        """
        Heuristic 1: Aggressive / Materialistic
        Focuses heavily on:
        - Number of Captures (Highest priority)
        - Creating Open Threes and Fours
        - Less concern for positional play or blocking unless critical
        """
        score = 0
        opponent = 3 - player
        
        # 1. Material Score (Captures)
        # Big bonus for having more captures
        score += (board.captures[player] - board.captures[opponent]) * CAPTURE_SCORE

        # 2. Pattern Scoring (Aggressive)
        # We only scan for our own offensive patterns mostly
        my_patterns  = self._evaluate_patterns(board, player)
        opp_patterns = self._evaluate_patterns(board, opponent)

        # In H1, we weigh our offense much higher than defense
        score += my_patterns * 1.5 
        score -= opp_patterns * 0.8

        return score

    def heuristic_2(self, board, player: int) -> int:
        """
        Heuristic 2: Strategic / Defensive
        Focuses on:
        - Board Control (Center control)
        - Blocking opponent's potential threats
        - Creating complex shapes
        - Safety (avoiding being captured)
        """
        score = 0
        opponent = 3 - player
        center = BOARD_SIZE // 2

        # 1. Win Check (Highest Priority)
        if board.winner == player:
            return WIN_SCORE
        if board.winner == opponent:
            return -WIN_SCORE

        # 2. Captures (Important but balanced)
        score += (board.captures[player] - board.captures[opponent]) * (CAPTURE_SCORE // 2)

        # 3. Positional / Center Control
        # Stones closer to center are worth slightly more
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    dist = abs(r - center) + abs(c - center)
                    score += (20 - dist) # Small bonus for centrality

        # 4. Pattern Scoring (Strategic)
        my_patterns = self._evaluate_patterns(board, player)
        opp_patterns = self._evaluate_patterns(board, opponent)

        # In H2, we weigh blocking opponent very highly
        score += my_patterns * 1.0
        score -= opp_patterns * 1.2 # Defend!

        # 5. Capture Risk (Avoid placing stones where they can be captured)
        # (Simplified check for this example)
        # Not fully implemented to save performance, but H2 concept includes safety.

        return score

    def _evaluate_patterns(self, board, player: int) -> int:
        """Helper to scan board for patterns like 3-in-a-row, 4-in-a-row."""
        score = 0
        opponent = 3 - player
        
        # Directions: Horizontal, Vertical, Diagonal 1, Diagonal 2
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    for dr, dc in directions:
                        # Check if this stone is the start of a sequence (to avoid double counting)
                        prev_r, prev_c = r - dr, c - dc
                        if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE and board.grid[prev_r][prev_c] == player:
                            continue # Not the start

                        score += self._score_sequence(board, r, c, dr, dc, player, opponent)
        return score

    def _score_sequence(self, board, r, c, dr, dc, player, opponent) -> int:
        """Scoring logic for a specific line direction."""
        length = 0
        gaps = 0
        
        # Look ahead up to 5 spaces
        for i in range(5):
            nr, nc = r + dr*i, c + dc*i
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break # Off board
            
            cell = board.grid[nr][nc]
            if cell == player:
                length += 1
            elif cell == EMPTY:
                gaps += 1 # Allow one gap for broken lines? For now strict lines
                break 
            else: # Opponent
                break

        # Check endpoints for openness
        # Start point (r, c) - 1 step back
        open_start = False
        pr, pc = r - dr, c - dc
        if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board.grid[pr][pc] == EMPTY:
            open_start = True

        # End point
        open_end = False
        er, ec = r + dr*length, c + dc*length
        if 0 <= er < BOARD_SIZE and 0 <= ec < BOARD_SIZE and board.grid[er][ec] == EMPTY:
            open_end = True

        if length == 5:
            return WIN_SCORE # 5 in a row!
        
        if length == 4:
            if open_start and open_end: return OPEN_FOUR
            if open_start or open_end: return CLOSED_FOUR
        
        if length == 3:
            if open_start and open_end: return OPEN_THREE
            if open_start or open_end: return CLOSED_THREE # Blocked 3 is not very scary

        if length == 2:
            if open_start and open_end: return OPEN_TWO

        return 0

    # =============================================================
    # 2 & 3. APPLICATION OF MINIMAX ALGORITHM
    # =============================================================

    def minimax_h1(self, board, depth: int) -> Tuple[int, int]:
        """Application of MiniMax Algorithm using Heuristic 1"""
        _, move = self._minimax_recursive(board, depth, True, self.heuristic_1)
        return move

    def minimax_h2(self, board, depth: int) -> Tuple[int, int]:
        """Application of MiniMax Algorithm using Heuristic 2"""
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

    # =============================================================
    # 4. PRUNING THE MINIMAX SEARCH USING ALPHA-BETA
    # =============================================================

    def alphabeta_h1(self, board, depth: int) -> Tuple[int, int]:
        """Pruning the MiniMax Search using Alpha-Beta Approach (Heuristic 1)"""
        _, move = self._alphabeta_recursive(board, depth, -math.inf, math.inf, True, self.heuristic_1)
        return move

    def alphabeta_h2(self, board, depth: int) -> Tuple[int, int]:
        """Pruning the MiniMax Search using Alpha-Beta Approach (Heuristic 2)"""
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

    # =============================================================
    # HELPERS
    # =============================================================

    def _get_smart_candidates(self, board) -> List[Tuple[int, int]]:
        """
        Get candidate moves, but optimized.
        Only consider cells within 2 distance of existing stones.
        If board is empty, return center.
        """
        if board.move_count == 0:
            return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
        
        # Use a set for fast lookup
        candidates = set()
        rad = 2
        
        # Iterate only cells with stones to find neighbors
        # This is strictly faster than iterating the whole board if the board is sparse
        # But for simpler implementation, we can iterate whole board if board_size is small.
        # Pente is 19x19, so iterating whole board (361) is fine.
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] != EMPTY:
                    # found a stone, add its empty neighbors
                    for dr in range(-rad, rad+1):
                        for dc in range(-rad, rad+1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        
        return list(candidates)

    def _find_immediate_forced_move(self, board) -> Optional[Tuple[int, int]]:

        candidates = self._get_smart_candidates(board)
        opponent = self.opponent_color

        # 1. Check for Immediate WIN for US
        for r, c in candidates:
            board.make_move(r, c, self.player_color)
            if board.winner == self.player_color:
                board.undo_move(r, c)
                return (r, c)
            board.undo_move(r, c)
            
        # 2. Check for Immediate WIN for OPPONENT (Must Block)
        for r, c in candidates:
            # Simulate opponent moving there
            board.make_move(r, c, opponent)
            if board.winner == opponent:
                board.undo_move(r, c)
                return (r, c)
            board.undo_move(r, c)

        return None