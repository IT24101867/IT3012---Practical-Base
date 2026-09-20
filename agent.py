# agent.py
import random
import math
import heapq
from collections import deque

class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)


class SimpleReflexAgent:
    """Step 1.2: Simple Reflex Agent with NO memory - pure IF-THEN rules."""
    
    def sense_and_act(self, percept: dict) -> str:
        # Rule 1: IF food_here THEN Suck
        if percept['food_here']:
            return 'Suck'
        
        # Rule 2: IF wall_ahead THEN Left
        elif percept['wall_ahead']:
            return 'Left'
        
        # Rule 3: ELSE Forward
        else:
            return 'Forward'


class ModelBasedAgent:
    """Step 1.3: Model-Based Agent with internal memory/state."""
    
    def __init__(self):
        # ✅ INTERNAL STATE (Memory)
        self.position_history = []      # Tracks actions taken
        self.action_counter = {}        # Counts each action
        self.stuck_counter = 0          # How long stuck
        self.last_action = None
    
    def sense_and_act(self, percept: dict) -> str:
        # Rule 1: Always collect food
        if percept['food_here']:
            return 'Suck'
        
        # Rule 2: Detect if stuck (memory check)
        if len(self.position_history) >= 5:
            last_5 = self.position_history[-5:]
            if len(set(last_5)) <= 2:   # Only 1-2 unique actions
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
            
            # If stuck, try different strategy
            if self.stuck_counter >= 3:
                return 'Right'  # Turn right instead of left
        
        # Rule 3: Check wall ahead with memory
        if percept['wall_ahead']:
            # Check last action from memory
            if len(self.position_history) >= 2:
                last_action = self.position_history[-1]
                if last_action == 'Left':
                    return 'Right'  # Try turning right
                elif last_action == 'Right':
                    return 'Left'   # Try turning left
            
            # Default to left turn
            return 'Left'
        
        # Rule 4: Default move forward
        return 'Forward'
    
    # ✅ TRANSITION MODEL: Update state before next action
    def update_memory(self, action: str):
        """Update internal state (Transition & Sensor Model)."""
        self.last_action = action
        self.position_history.append(action)
        
        # Count actions
        self.action_counter[action] = self.action_counter.get(action, 0) + 1
        
        # Keep history manageable
        if len(self.position_history) > 50:
            self.position_history.pop(0)
    
    # ✅ SENSOR MODEL: Get memory stats
    def get_memory_stats(self) -> dict:
        """Return current memory state."""
        return {
            'total_actions': len(self.position_history),
            'action_counts': self.action_counter,
            'is_stuck': self.stuck_counter >= 3,
            'last_action': self.last_action
        }


class SearchAgent:
    """Practicals 3 & 4: Problem-Solving Agent using BFS, UCS, and A* Search.

    Grid convention (matches test_suite.py): positions are (x, y) tuples,
    'Up' increases y, 'Down' decreases y, 'Left' decreases x, 'Right' increases x.
    """

    def __init__(self):
        self.plan = []            # queued actions from the last search
        self.active_algo = 'AStar'  # 'BFS', 'UCS', or 'AStar'

    # ---------------- Step 1.1: Heuristic functions ----------------
    def manhattan_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return abs(x1 - x2) + abs(y1 - y2)

    def euclidean_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    # ---------------- Shared helper: valid neighbouring cells ----------------
    def _neighbors(self, pos, walls, grid_size):
        width, height = grid_size
        moves = [(0, 1, 'Up'), (0, -1, 'Down'), (-1, 0, 'Left'), (1, 0, 'Right')]
        results = []
        for dx, dy, action in moves:
            nx, ny = pos[0] + dx, pos[1] + dy
            npos = (nx, ny)
            if 0 <= nx < width and 0 <= ny < height and npos not in walls:
                results.append((npos, action))
        return results

    # ---------------- Uninformed search (previous lab) ----------------
    def bfs_search(self, start_pos, goal_pos, walls, grid_size):
        frontier = deque([(start_pos, [])])
        reached = {start_pos}
        while frontier:
            current_pos, path_taken = frontier.popleft()
            if current_pos == goal_pos:
                return path_taken
            for npos, action in self._neighbors(current_pos, walls, grid_size):
                if npos not in reached:
                    reached.add(npos)
                    frontier.append((npos, path_taken + [action]))
        return None

    def ucs_search(self, start_pos, goal_pos, walls, grid_size):
        frontier = [(0, start_pos, [])]
        reached = set()
        while frontier:
            g_cost, current_pos, path_taken = heapq.heappop(frontier)
            if current_pos == goal_pos:
                return path_taken
            if current_pos in reached:
                continue
            reached.add(current_pos)
            for npos, action in self._neighbors(current_pos, walls, grid_size):
                if npos not in reached:
                    heapq.heappush(frontier, (g_cost + 1, npos, path_taken + [action]))
        return None

    # ---------------- Step 1.2: A* Search ----------------
    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):
        heuristic_fn = self.manhattan_distance if heuristic_type == 'manhattan' else self.euclidean_distance

        start_g = 0
        start_h = heuristic_fn(start_pos, goal_pos)
        # Tuple format: (f_cost, g_cost, current_pos, path_taken)
        frontier = [(start_g + start_h, start_g, start_pos, [])]
        reached_states = set()

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == goal_pos:
                return path_taken

            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)

            for npos, action in self._neighbors(current_pos, walls, grid_size):
                if npos in reached_states:
                    continue
                g_new = g_cost + 1
                h_new = heuristic_fn(npos, goal_pos)
                f_new = g_new + h_new
                heapq.heappush(frontier, (f_new, g_new, npos, path_taken + [action]))

        return None  # no path found

    # ---------------- Step 1.3: Decision loop integration ----------------
    def sense_and_act(self, percept: dict) -> str:
        """Expects a FULL-observability percept:
        {'agent_pos', 'remaining_food', 'walls', 'grid_size'}
        (see the get_percept() changes needed in visual_grid_game.py)."""

        agent_pos = tuple(percept['agent_pos'])
        remaining_food = percept['remaining_food']
        walls = percept['walls']
        grid_size = percept['grid_size']

        # If we already have a plan, keep executing it
        if self.plan:
            return self.plan.pop(0)

        # No food left / no plan possible
        if not remaining_food:
            return 'Suck'  # harmless no-op if nothing to collect

        # Find the closest food item (by heuristic distance) to act as goal_pos
        goal_pos = min(remaining_food, key=lambda f: self.manhattan_distance(agent_pos, f))

        if self.active_algo == 'AStar':
            path = self.astar_search(agent_pos, goal_pos, walls, grid_size, heuristic_type='manhattan')
        elif self.active_algo == 'UCS':
            path = self.ucs_search(agent_pos, goal_pos, walls, grid_size)
        else:  # BFS
            path = self.bfs_search(agent_pos, goal_pos, walls, grid_size)

        if not path:
            return 'Suck'  # stuck / unreachable food, no-op

        self.plan = path + ['Suck']  # walk the path, then collect the food
        return self.plan.pop(0)