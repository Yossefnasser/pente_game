import tkinter as tk
from tkinter import messagebox, ttk
import time
from game_logic  import PenteGame, BOARD_SIZE, WHITE, BLACK, EMPTY
from ai_engine   import PenteAI
from analysis_experiments import run_experiments, run_aggregated
import os
import json

class PenteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pente - AI Project")
        
        self.board_size = BOARD_SIZE
        self.cell_size = 30
        self.margin = 20
        
        self.game = PenteGame()
        self.ai_players = {} 
        self.game_over = False
        
        self._create_widgets()
        self._draw_board()

    def _create_widgets(self):
        # Control Panel
        control_frame = tk.LabelFrame(self.root, text="Settings", padx=10, pady=5)
        control_frame.pack(pady=10)
        
        # AI Mode Selection
        tk.Label(control_frame, text="AI Mode:").grid(row=0, column=0, padx=5)
        self.mode_var = tk.StringVar(value='alphabeta_h2')
        modes = [
            ('Minimax (H1)', 'minimax_h1'),
            ('Minimax (H2)', 'minimax_h2'),
            ('Alpha-Beta (H1)', 'alphabeta_h1'),
            ('Alpha-Beta (H2)', 'alphabeta_h2')
        ]
        
        row = 0
        col = 1
        for text, val in modes:
            tk.Radiobutton(control_frame, text=text, variable=self.mode_var, value=val).grid(row=row, column=col, sticky="w")
            col += 1
            if col > 2:
                col = 1
                row += 1
        
        # Depth
        tk.Label(control_frame, text="Depth:").grid(row=2, column=0, padx=5)
        self.depth_var = tk.IntVar(value=2)
        tk.Spinbox(control_frame, from_=1, to=3, textvariable=self.depth_var, width=5).grid(row=2, column=1, sticky="w")
        
        # AI vs AI Checkbox
        self.ai_vs_ai_var = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="AI vs AI", variable=self.ai_vs_ai_var).grid(row=2, column=3, padx=10)

        # Buttons
        tk.Button(control_frame, text="New Game", command=self.start_game, bg="#4CAF50", fg="white").grid(row=2, column=2, padx=10)
        tk.Button(control_frame, text="Run & Compare (Quick)", command=self.run_and_show_comparison, bg="#2196F3", fg="white").grid(row=2, column=4, padx=10)
        
        # Stats
        self.status_label = tk.Label(self.root, text="Select Mode and Start Game", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)
        
        self.capture_label = tk.Label(self.root, text="Captures - White: 0 | Black: 0")
        self.capture_label.pack()
        
        self.info_label = tk.Label(self.root, text="AI Stats: -")
        self.info_label.pack()
        
        # Board
        canvas_len = self.margin * 2 + (self.board_size - 1) * self.cell_size
        self.canvas = tk.Canvas(self.root, width=canvas_len, height=canvas_len, bg="#DEB887")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

    def start_game(self):
        self.game = PenteGame()
        self.game_over = False
        self.ai_players = {}
        
        # Setup Black AI (Standard AI opponent)
        self.ai_players[BLACK] = PenteAI(
            mode=self.mode_var.get(), 
            player_color=BLACK, 
            depth=self.depth_var.get()
        )
        
        # Setup White AI (If AI vs AI mode is on)
        if self.ai_vs_ai_var.get():
            self.ai_players[WHITE] = PenteAI(
                mode=self.mode_var.get(), 
                player_color=WHITE, 
                depth=self.depth_var.get()
            )
        else:
            self.ai_players[WHITE] = None # Human player
            
        self._draw_board()
        self.update_captures()
        
        if self.ai_vs_ai_var.get():
            self.update_status("AI vs AI Started...")
            self.root.after(500, self.make_ai_move)
        else:
            mode_str = self.mode_var.get().replace('_', ' + ').upper()
            self.update_status(f"Started: {mode_str}. Your Turn (White)")

    def _draw_board(self):
        self.canvas.delete("all")
        # Grid
        for i in range(self.board_size):
            start = self.margin + i * self.cell_size
            end = self.margin + (self.board_size - 1) * self.cell_size
            self.canvas.create_line(self.margin, start, end, start)
            self.canvas.create_line(start, self.margin, start, end)
            
        # Star Points
        stars = [3, 9, 15]
        for r in stars:
            for c in stars:
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")

        # Stones
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.game.grid[r][c] != EMPTY:
                    self.draw_stone(r, c, self.game.grid[r][c])
        
        # Winner
        if self.game.winner:
            for r, c in self.game.winning_sequence:
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                self.canvas.create_oval(x-5, y-5, x+5, y+5, outline="red", width=3)

    def draw_stone(self, r, c, player):
        x = self.margin + c * self.cell_size
        y = self.margin + r * self.cell_size
        rad = 12
        color = "white" if player == WHITE else "black"
        outline = "black" if player == WHITE else "white"
        self.canvas.create_oval(x-rad, y-rad, x+rad, y+rad, fill=color, outline=outline)

    def on_click(self, event):
        if self.game_over:
            return
            
        # Determine strict turn
        current_player = WHITE if self.game.move_count % 2 == 0 else BLACK
        
        # If it's currently an AI's turn, ignore human clicks
        if self.ai_players.get(current_player):
            return
            
        c = round((event.x - self.margin) / self.cell_size)
        r = round((event.y - self.margin) / self.cell_size)
        
        if self.game.is_valid_move(r, c, current_player):
            if self.game.make_move(r, c, current_player):
                self._draw_board()
                self.update_captures()
                
                if self.game.winner:
                    self.end_game(f"{'White' if current_player == WHITE else 'Black'} Wins!")
                    return
                
                # Check if next player is AI
                next_player = 3 - current_player
                if self.ai_players.get(next_player):
                    self.update_status(f"AI ({'Black' if next_player == BLACK else 'White'}) Thinking...")
                    self.root.update()
                    self.root.after(50, self.make_ai_move)

    def make_ai_move(self):
        if self.game_over:
            return

        current_player = WHITE if self.game.move_count % 2 == 0 else BLACK
        ai = self.ai_players.get(current_player)
        
        if not ai:
            return # Should not happen if logic is correct, or waiting for human
            
        start = time.time()
        move = ai.get_best_move(self.game)
        dur = time.time() - start
        
        if move:
            r, c = move
            self.game.make_move(r, c, current_player)
            self._draw_board()
            self.update_captures()
            
            p_name = "Black" if current_player == BLACK else "White"
            info = (f"{p_name} AI | Time: {dur:.2f}s | "
                    f"Nodes: {ai.nodes_explored} | "
                    f"Pruned: {ai.pruned_branches}")
            self.info_label.config(text=info)
            
            if self.game.winner:
                self.end_game(f"AI ({p_name}) Wins!")
                return
                
            # If next player is also AI (AI vs AI), schedule next move
            next_player = 3 - current_player
            if self.ai_players.get(next_player):
                self.update_status(f"AI ({'Black' if next_player == BLACK else 'White'}) Turn...")
                self.root.after(500, self.make_ai_move)
            else:
                self.update_status("Your Turn (White)")

    def update_status(self, msg):
        self.status_label.config(text=msg)

    def update_captures(self):
        self.capture_label.config(text=f"Captures - White: {self.game.captures[WHITE]} | Black: {self.game.captures[BLACK]}")

    def end_game(self, result):
        self.game_over = True
        self.status_label.config(text="GAME OVER: " + result, fg="red")
        messagebox.showinfo("Game Over", result)

    def run_and_show_comparison(self):
        self.update_status("Running quick analysis and showing comparison...")
        self.root.update()
        try:
            # Run aggregated analysis
            run_aggregated("gui")
            # Immediately show the latest aggregated table
            self.show_aggregated_table()
            self.update_status("Comparison ready.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run/show comparison: {e}")
            self.update_status("Comparison failed.")

    def show_aggregated_table(self):
        # Look for latest aggregated csv and display in a table
        try:
            os.makedirs("results", exist_ok=True)
            files = [f for f in os.listdir("results") if f.endswith('.csv') and 'aggregated' in f]
            if not files:
                messagebox.showinfo("No Aggregated Results", "Run 'Run & Compare (Quick)' first.")
                return
            files.sort(reverse=True)
            latest = os.path.join("results", files[0])

            # Read CSV
            rows = []
            with open(latest, 'r', encoding='utf-8') as f:
                import csv as _csv
                reader = _csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            # Build window with table
            win = tk.Toplevel(self.root)
            win.title(f"Aggregated Comparison: {os.path.basename(latest)}")
            cols = ['position', 'player', 'heuristic', 'depth', 'mm_time_sum', 'ab_time_sum', 'time_delta', 'mm_nodes_sum', 'ab_nodes_sum', 'nodes_delta']
            tree = ttk.Treeview(win, columns=cols, show='headings')
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=110 if c in ('position','player','heuristic','depth') else 140, anchor='center')
            for r in rows:
                tree.insert('', 'end', values=[r.get(c, '') for c in cols])
            tree.pack(fill='both', expand=True)

            # Add note
            tk.Label(win, text="Aggregated sums comparing Minimax vs Alpha-Beta within the same heuristic and depth.").pack(pady=6)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show comparison: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PenteGUI(root)
    root.mainloop()
