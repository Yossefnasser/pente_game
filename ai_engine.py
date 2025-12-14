import math
import random
from typing import Tuple, List
from game_logic import BOARD_SIZE, EMPTY, WHITE, BLACK

# Heuristic Weights
PATTERNS = {
    'five'              : 1000000,   
    'capture_win'       : 500000,     
    'open_four'         : 100000,     
    'four'              : 50000,      
    'open_three'        : 10000, 
    'three'             : 1000,      
    'open_two'          : 500,    
    'two'               : 100,         
}

class PenteAI:
    def __init__(self, mode: str = 'alphabeta_h2', player_color: int = BLACK, depth: int = 2):
        self.mode = mode  # Options: 'minimax_h1', 'minimax_h2', 'alphabeta_h1', 'alphabeta_h2'
        self.player_color = player_color
        self.opponent_color = 3 - player_color
        self.depth = depth
        self.nodes_explored = 0
        self.pruned_branches = 0

    def get_best_move(self, board) -> Tuple[int, int]:
        self.nodes_explored = 0
        self.pruned_branches = 0
        
        # Decide Strategy based on mode
        use_pruning = 'alphabeta' in self.mode
        heuristic_ver = 2 if 'h2' in self.mode else 1
        

        # Dispatch
        if use_pruning:
             return self._alphabeta_search(board, self.depth, heuristic_ver)
        else:
             return self._minimax_search(board, self.depth, heuristic_ver)

    def _minimax_search(self, board, depth, h_version) -> Tuple[int, int]:
        candidates = board.get_candidate_moves(radius=1)
        if not candidates: return BOARD_SIZE//2, BOARD_SIZE//2
        
        best_score = -math.inf
        if len(candidates) > 8: candidates = candidates[:8] 
        
        best_move = candidates[0]
        
        for move in candidates:
            r, c = move
            board.make_move(r, c, self.player_color)
            if board.winner == self.player_color:
                board.undo_move(r, c)
                return move
            
            score = self._minimax_node(board, depth-1, False, h_version)
            board.undo_move(r, c)
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

    def _minimax_node(self, board, depth, is_maximizing, h_version):
        self.nodes_explored += 1
        
        if board.winner == self.player_color: return PATTERNS['five']
        if board.winner == self.opponent_color: return -PATTERNS['five']
        
        if depth == 0 or board.is_full():
            return self._evaluate(board, self.player_color, h_version)
            
        candidates = board.get_candidate_moves(radius=1)
        if len(candidates) > 5: candidates = candidates[:5] 
        
        if is_maximizing:
            max_eval = -math.inf
            for move in candidates:
                board.make_move(move[0], move[1], self.player_color)
                eval = self._minimax_node(board, depth-1, False, h_version)
                board.undo_move(move[0], move[1])
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = math.inf
            for move in candidates:
                board.make_move(move[0], move[1], self.opponent_color)
                eval = self._minimax_node(board, depth-1, True, h_version)
                board.undo_move(move[0], move[1])
                min_eval = min(min_eval, eval)
            return min_eval

    def _alphabeta_search(self, board, depth, h_version) -> Tuple[int, int]:
        candidates = board.get_candidate_moves()
        ordered = self._order_moves(board, candidates, self.player_color, h_version)
        if len(ordered) > 15: ordered = ordered[:15]
        
        best_score = -math.inf
        best_move = ordered[0]
        alpha = -math.inf
        beta = math.inf
        
        for move in ordered:
            r, c = move
            board.make_move(r, c, self.player_color)
            if board.winner == self.player_color:
                board.undo_move(r, c)
                return move
                
            score = self._alphabeta_node(board, depth-1, alpha, beta, False, h_version)
            board.undo_move(r, c)
            
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        return best_move

    def _alphabeta_node(self, board, depth, alpha, beta, is_maximizing, h_version):
        self.nodes_explored += 1
        if board.winner == self.player_color: return PATTERNS['five']
        if board.winner == self.opponent_color: return -PATTERNS['five']
        
        if depth == 0 or board.is_full():
            return self._evaluate(board, self.player_color, h_version)

        candidates = board.get_candidate_moves()
        player = self.player_color if is_maximizing else self.opponent_color
        if len(candidates) > 10: candidates = candidates[:10]

        if is_maximizing:
            max_eval = -math.inf
            for move in candidates:
                board.make_move(move[0], move[1], self.player_color)
                eval = self._alphabeta_node(board, depth-1, alpha, beta, False, h_version)
                board.undo_move(move[0], move[1])
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in candidates:
                board.make_move(move[0], move[1], self.opponent_color)
                eval = self._alphabeta_node(board, depth-1, alpha, beta, True, h_version)
                board.undo_move(move[0], move[1])
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return min_eval

    def _order_moves(self, board, moves, player, h_version):
        scores = []
        for m in moves:
            board.make_move(m[0], m[1], player)
            scores.append((self._evaluate(board, player, h_version), m))
            board.undo_move(m[0], m[1])
        scores.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scores]

    def _evaluate(self, board, player, h_version):
        if h_version == 1:
            return self._heuristic_1_basic(board, player)
        else:
            return self._heuristic_2_strategic(board, player)

    # --- Heuristic 1: Basic Evaluation (Material/Captures + Threats) ---
    def _heuristic_1_basic(self, board, player):
        score = 0
        opp = 3 - player
        
        # 1. Captures (Heavy Weight)
        score += (board.captures[player] - board.captures[opp]) * 1000
        
        # 2. Simple Threats (Count 3s and 4s only)
        score += self._scan_lines_simple(board, player)
        return score

    def _scan_lines_simple(self, board, player):
        # A lighter scanner for H1
        s = 0
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    for dr, dc in directions:
                        if self._check_line(board, r, c, dr, dc, 3, player): s += 100
        return s

    def _check_line(self, board, r, c, dr, dc, length, player):
        # Helper for H1
        for i in range(length):
            nr, nc = r + dr*i, c + dc*i
            if not(0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE) or board.grid[nr][nc] != player:
                return False
        return True

    # --- Heuristic 2: Strategic Evaluation (Patterns + Center Control) ---
    def _heuristic_2_strategic(self, board, player):
        score = 0
        opp = 3 - player
        
        # 1. Captures
        score += (board.captures[player] - board.captures[opp]) * 5000 
        
        # 2. Center Control
        center = BOARD_SIZE // 2
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == player:
                    score += (20 - (abs(r-center) + abs(c-center)))
        
        # 3. Patterns
        score += self._evaluate_patterns_robust(board, player)
        return score

    def _evaluate_patterns_robust(self, board, player):
        # The robust evaluator from previous iteration
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        visited = set() # To avoid double counting? Or just scan starts.
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == EMPTY: continue
                stone = board.grid[r][c]
                
                for dr, dc in directions:
                    pr, pc = r-dr, c-dc
                    if 0<=pr<BOARD_SIZE and 0<=pc<BOARD_SIZE and board.grid[pr][pc] == stone:
                        continue 
                    
                    count = 0
                    curr_r, curr_c = r, c
                    while 0<=curr_r<BOARD_SIZE and 0<=curr_c<BOARD_SIZE and board.grid[curr_r][curr_c] == stone:
                        count += 1
                        curr_r += dr
                        curr_c += dc
                        
                    if count < 2: continue
                    
                    # Check ends
                    open_ends = 0
                    # Start side (pr, pc)
                    if 0<=pr<BOARD_SIZE and 0<=pc<BOARD_SIZE and board.grid[pr][pc] == EMPTY:
                        open_ends += 1
                    # End side (curr_r, curr_c)
                    if 0<=curr_r<BOARD_SIZE and 0<=curr_c<BOARD_SIZE and board.grid[curr_r][curr_c] == EMPTY:
                        open_ends += 1
                        
                    val = 0
                    if count >= 5: val   = PATTERNS['five']
                    elif count == 4: val = PATTERNS['open_four'] if open_ends==2 else PATTERNS['four']
                    elif count == 3: val = PATTERNS['open_three'] if open_ends==2 else PATTERNS['three']
                    elif count == 2: val = PATTERNS['open_two'] if open_ends==2 else 10
                    
                    if stone == player: score += val
                    else: score -= val * 1.5 # Block opponent!

        return score
