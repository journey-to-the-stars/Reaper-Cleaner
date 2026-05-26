from src.model.game_state import GameState


class StateMachine:
    def __init__(self):
        self.current_state = GameState.MENU
        self.previous_state = None

    def change_to(self, new_state):
        self.previous_state = self.current_state
        self.current_state = new_state

    def revert(self):
        if self.previous_state:
            self.current_state = self.previous_state
            self.previous_state = None

    def is_in(self, *states):
        return self.current_state in states
