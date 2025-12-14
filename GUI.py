import tkinter as tk
from tkinter import messagebox, ttk
import time
from game_logic import PenteGame, BOARD_SIZE, WHITE, BLACK, EMPTY
from ai_engine import PenteAI

class PenteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pente - AI Project")
        
        self.board_size = BOARD_SIZE
        self.cell_size = 30
        self.margin = 20
        
        self.game = PenteGame()
        self.ai = None
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
        
        # Buttons
        tk.Button(control_frame, text="New Game", command=self.start_game, bg="#4CAF50", fg="white").grid(row=2, column=2, padx=10)
        
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
        self.ai = PenteAI(
            mode=self.mode_var.get(), 
            player_color=BLACK, 
            depth=self.depth_var.get()
        )
        self.game_over = False
        self._draw_board()
        
        mode_str = self.mode_var.get().replace('_', ' + ').upper()
        self.update_status(f"Started: {mode_str}. Your Turn (White)")
        self.update_captures()

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
        if self.game_over or not self.ai:
            return
            
        c = round((event.x - self.margin) / self.cell_size)
        r = round((event.y - self.margin) / self.cell_size)
        
        if self.game.is_valid_move(r, c, WHITE):
            if self.game.make_move(r, c, WHITE):
                self._draw_board()
                self.update_captures()
                
                if self.game.winner:
                    self.end_game("White Wins!")
                    return
                
                self.update_status("AI Thinking...")
                self.root.update()
                self.root.after(50, self.make_ai_move)

    def make_ai_move(self):
        start = time.time()
        move = self.ai.get_best_move(self.game)
        dur = time.time() - start
        
        if move:
            r, c = move
            self.game.make_move(r, c, BLACK)
            self._draw_board()
            self.update_captures()
            
            info = (f"Time: {dur:.2f}s | "
                    f"Nodes: {self.ai.nodes_explored} | "
                    f"Pruned: {self.ai.pruned_branches} | "
                    f"Mode: {self.ai.mode}")
            self.info_label.config(text=info)
            
            if self.game.winner:
                self.end_game("AI (Black) Wins!")
                return
                
            self.update_status("Your Turn (White)")

    def update_status(self, msg):
        self.status_label.config(text=msg)

    def update_captures(self):
        self.capture_label.config(text=f"Captures - White: {self.game.captures[WHITE]} | Black: {self.game.captures[BLACK]}")

    def end_game(self, result):
        self.game_over = True
        self.status_label.config(text="GAME OVER: " + result, fg="red")
        messagebox.showinfo("Game Over", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = PenteGUI(root)
    root.mainloop()
