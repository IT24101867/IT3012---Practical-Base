# visual_grid_game.py
import random
import tkinter as tk

from agent import SimpleReflexAgent, ModelBasedAgent, SearchAgent


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.agent_direction = 'Right'

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Generate some default scattered walls for a larger grid
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    # STEP 1.1 (Practical 3): Expose the world model / global state alongside
    # the existing partial percept, so search agents can plan ahead.
    def get_percept(self) -> dict:
        x, y = self.agent_pos

        # Find the cell directly in front of the agent
        if self.agent_direction == 'Up':
            ahead = (x, y + 1)
        elif self.agent_direction == 'Down':
            ahead = (x, y - 1)
        elif self.agent_direction == 'Left':
            ahead = (x - 1, y)
        else:  # Right
            ahead = (x + 1, y)

        # Check whether there is a wall directly ahead
        wall_ahead = (
            ahead[0] < 0 or
            ahead[0] >= self.width or
            ahead[1] < 0 or
            ahead[1] >= self.height or
            ahead in self.walls
        )

        return {
            # Local, partial-observability percepts (reflex agents)
            'wall_ahead': wall_ahead,
            'food_here': tuple(self.agent_pos) in self.food_positions,

            # Global state (Practical 3, Step 1.1) - needed for planning agents
            'agent_pos': tuple(self.agent_pos),
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions),
        }

    # STEP 1.3: Direct grid movement for search agents (Up/Down/Left/Right move
    # the agent by one cell immediately), separate from the turn-based
    # Left/Right/Forward model used by the reflex agents above.
    def execute_direct_action(self, action: str):
        self.steps += 1
        x, y = self.agent_pos

        if action == 'Up':
            new_pos = (x, y + 1)
        elif action == 'Down':
            new_pos = (x, y - 1)
        elif action == 'Left':
            new_pos = (x - 1, y)
        elif action == 'Right':
            new_pos = (x + 1, y)
        elif action == 'Suck':
            current_pos = tuple(self.agent_pos)
            if current_pos in self.food_positions:
                self.food_positions.remove(current_pos)
                self.score += 20
            return
        else:
            return

        if (0 <= new_pos[0] < self.width and 0 <= new_pos[1] < self.height
                and new_pos not in self.walls):
            self.agent_pos = list(new_pos)
        else:
            self.score -= 5

    def execute_action(self, action: str):
        self.steps += 1

        # Turn left
        if action == 'Left':
            directions = ['Up', 'Left', 'Down', 'Right']
            current = directions.index(self.agent_direction)
            self.agent_direction = directions[(current + 1) % 4]

        # Turn right
        elif action == 'Right':
            directions = ['Up', 'Right', 'Down', 'Left']
            current = directions.index(self.agent_direction)
            self.agent_direction = directions[(current + 1) % 4]

        # Move forward
        elif action == 'Forward':
            new_pos = list(self.agent_pos)

            if self.agent_direction == 'Up':
                new_pos[1] += 1
            elif self.agent_direction == 'Down':
                new_pos[1] -= 1
            elif self.agent_direction == 'Left':
                new_pos[0] -= 1
            elif self.agent_direction == 'Right':
                new_pos[0] += 1

            # Check boundaries
            if (
                new_pos[0] < 0 or
                new_pos[0] >= self.width or
                new_pos[1] < 0 or
                new_pos[1] >= self.height
            ):
                self.score -= 5

            # Check wall
            elif tuple(new_pos) in self.walls:
                self.score -= 5

            else:
                self.agent_pos = new_pos

        # Collect food
        elif action == 'Suck':
            current_pos = tuple(self.agent_pos)
            if current_pos in self.food_positions:
                self.food_positions.remove(current_pos)
                self.score += 20

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, walls=None,
                 use_model_based=False, agent_type='reflex'):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                      custom_walls=walls)

        # STEP 1.2, 1.3 & Practical 4: Choose which agent to use.
        # agent_type: 'reflex' | 'model_based' | 'search' (SearchAgent using A*)
        if agent_type == 'search':
            self.agent = SearchAgent()
            self.agent_type = f"Search Agent ({self.agent.active_algo})"
        elif use_model_based or agent_type == 'model_based':
            self.agent = ModelBasedAgent()
            self.agent_type = "Model-Based Agent"
        else:
            self.agent = SimpleReflexAgent()
            self.agent_type = "Simple Reflex Agent"

        # Dynamically calculate cell size so the total canvas fits nicely within a 600x600 window ceiling
        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text=f"Score: 0 | Steps: 0 | Agent: {self.agent_type}", font=("Arial", 14))
        self.label.pack(pady=10)

        # Add agent selection buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        
        self.btn = tk.Button(button_frame, text="Start Simulation", command=self.run_loop, 
                           font=("Arial", 12), bg="#000066", fg="white")
        self.btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(button_frame, text="Reset", command=self.reset_game,
                                 font=("Arial", 12), bg="#660000", fg="white")
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Memory status label (for model-based agent)
        self.memory_label = tk.Label(root, text="", font=("Arial", 10), fg="gray")
        self.memory_label.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")
        
        # Add direction indicator
        if self.cell_size >= 30:
            ax, ay = self.env.agent_pos
            cx = ax * self.cell_size + self.cell_size / 2
            cy = (self.env.height - 1 - ay) * self.cell_size + self.cell_size / 2
            
            # Small arrow showing direction
            dir_offset = 10
            if self.env.agent_direction == 'Up':
                self.canvas.create_line(cx, cy + dir_offset, cx, cy - dir_offset, fill="white", width=2, arrow=tk.LAST)
            elif self.env.agent_direction == 'Down':
                self.canvas.create_line(cx, cy - dir_offset, cx, cy + dir_offset, fill="white", width=2, arrow=tk.LAST)
            elif self.env.agent_direction == 'Left':
                self.canvas.create_line(cx + dir_offset, cy, cx - dir_offset, cy, fill="white", width=2, arrow=tk.LAST)
            elif self.env.agent_direction == 'Right':
                self.canvas.create_line(cx - dir_offset, cy, cx + dir_offset, cy, fill="white", width=2, arrow=tk.LAST)

    def run_loop(self):
        self.btn.config(state="disabled")
        self.reset_btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()

                if isinstance(self.agent, SearchAgent):
                    # Practical 3 & 4: SearchAgent plans using the global state
                    # now included in get_percept(), then moves directly
                    action = self.agent.sense_and_act(percept)
                    self.env.execute_direct_action(action)
                else:
                    # Agent chooses an action (Step 1.2 or 1.3)
                    action = self.agent.sense_and_act(percept)

                    # Update agent memory (for model-based agent - Step 1.3)
                    if hasattr(self.agent, 'update_memory'):
                        self.agent.update_memory(action)

                    # Environment executes the action
                    self.env.execute_action(action)

                # Update GUI
                self.draw_grid()

                # Update status label
                status_text = (f"Score: {self.env.score} | "
                              f"Steps: {self.env.steps} | "
                              f"Direction: {self.env.agent_direction} | "
                              f"Action: {action} | "
                              f"Agent: {self.agent_type}")
                
                # Add memory info if using model-based agent
                if hasattr(self.agent, 'get_memory_stats'):
                    stats = self.agent.get_memory_stats()
                    memory_text = f" | Memory: {stats['total_actions']} actions"
                    if stats['is_stuck']:
                        memory_text += " ⚠️ STUCK DETECTED!"
                    self.memory_label.config(text=memory_text)
                else:
                    self.memory_label.config(text="")
                
                self.label.config(text=status_text)

                self.root.after(250, step)

            else:
                end_text = (
                    f"Finished! Final Score: {self.env.score}"
                    if not self.env.collision
                    else
                    f"Collision! Game Over! Final Score: {self.env.score}"
                )

                self.label.config(text=end_text)
                self.btn.config(state="normal")
                self.reset_btn.config(state="normal")

        step()

    def reset_game(self):
        """Reset the game with new random configuration."""
        self.env = VisualGridHuntGame(
            width=self.env.width, 
            height=self.env.height,
            num_food=len(self.env.food_positions),
            num_opponents=len(self.env.opponents),
            custom_walls=list(self.env.walls)
        )
        
        # Recreate the agent
        if self.agent_type.startswith("Search Agent"):
            self.agent = SearchAgent()
            self.agent_type = f"Search Agent ({self.agent.active_algo})"
        elif self.agent_type == "Model-Based Agent":
            self.agent = ModelBasedAgent()
        else:
            self.agent = SimpleReflexAgent()
        
        self.draw_grid()
        self.label.config(text=f"Score: 0 | Steps: 0 | Agent: {self.agent_type}")
        self.memory_label.config(text="")
        self.btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()

    # Practical 3, Step 1.3: Observation Task - change SearchAgent's
    # active_algo to 'BFS', 'DFS', or 'UCS' below and re-run to compare.
    print("=" * 50)
    print("PRACTICAL 3: Testing Search Agent (uninformed search)")
    print("=" * 50)
    print("Expected behavior: agent plans a full path to the nearest food")
    print("before moving. BFS/UCS take direct, optimal paths.")
    print("DFS takes a winding, non-optimal path to the same goal.")
    print("=" * 50)

    app1 = GridGameGUI(root, width=12, height=12, num_food=15, num_opponents=0, agent_type='search')

    root.mainloop()