"""Flask application for LEX game."""

from __future__ import annotations

import os
import random
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypedDict
from flask import Flask, Blueprint, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename
from lexcel.lex import Board, CYAN, VIOLET, other, Player
from lexcel.game import get_move, learn

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xlsx"}


class PlayerConfig(TypedDict):
    """Type definition for player configuration."""

    type: str
    exp: str | None


class GameState(TypedDict):
    """Type definition for game state."""

    board_code: str
    current_player: Player
    turn: int
    winner: Player | None
    memory: dict[Player, list[tuple[str, str, Player]]]
    players: tuple[PlayerConfig, PlayerConfig]  # (CYAN config, VIOLET config)
    random_state: tuple


# In-memory storage for game states
# In production, use Redis or a database
games: dict[str, GameState] = {}

# Create API Blueprint
api = Blueprint("api", __name__, url_prefix="/api")


@dataclass
class PlayerData(ABC):
    """Abstract base class for player configuration."""

    player: Player  # CYAN or VIOLET

    @abstractmethod
    def can_play_automatically(self) -> bool:
        """Check if player can make automatic moves."""
        raise NotImplementedError

    @abstractmethod
    def execute_move(
        self, state: GameState, rand: random.Random, move: str | None
    ) -> tuple[Board, Player | None]:
        """Execute a move for this player type."""
        raise NotImplementedError

    @staticmethod
    def from_state(state: GameState, player: Player) -> PlayerData:
        """Create appropriate PlayerData subclass from game state."""
        # CYAN is index 0, VIOLET is index 1
        player_idx = 0 if player == CYAN else 1
        player_config = state["players"][player_idx]

        if player_config["type"] == "computer":
            return ComputerPlayer(player=player, experience=player_config["exp"])
        return HumanPlayer(player=player)


@dataclass
class HumanPlayer(PlayerData):
    """Human player configuration."""

    def can_play_automatically(self) -> bool:
        """Human players cannot play automatically."""
        return False

    def execute_move(
        self, state: GameState, rand: random.Random, move: str | None
    ) -> tuple[Board, Player | None]:
        """Execute a human move."""
        if not move:
            raise ValueError("Move required for human player")

        move = move.upper()
        board = Board(state["board_code"])
        if move not in board.WELL_FORMED_MOVES:
            raise ValueError("Invalid move format")

        new_board = board.move(self.player, move[0], move[1])
        new_winner = self.player if new_board.is_winner(self.player) else None
        return new_board, new_winner


@dataclass
class ComputerPlayer(PlayerData):
    """Computer player configuration."""

    experience: str | None = None

    def can_play_automatically(self) -> bool:
        """Computer players can play automatically if they have experience."""
        return self.experience is not None

    def execute_move(
        self, state: GameState, rand: random.Random, move: str | None
    ) -> tuple[Board, Player | None]:
        """Execute a computer move."""
        # Computer can also play manually
        if move:
            return HumanPlayer(self.player).execute_move(state, rand, move)

        if not self.experience:
            raise ValueError("Computer player requires experience file")

        board = Board(state["board_code"])
        turn = state["turn"]
        move_memory = state["memory"][self.player]
        new_board, new_winner = get_move(
            board, self.player, turn, rand, self.experience, move_memory
        )
        state["memory"][self.player] = move_memory
        return new_board, new_winner


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_game_state() -> GameState | None:
    """Get current game state from server-side storage."""
    game_id = session.get("game_id")
    if game_id and game_id in games:
        return games[game_id]
    return None


def save_game_state(state: GameState) -> None:
    """Save game state to server-side storage."""
    if "game_id" not in session:
        session["game_id"] = str(uuid.uuid4())
    games[session["game_id"]] = state


def apply_learning_for_player(state: GameState, winner: Player, player: Player) -> None:
    """Apply learning for a specific player if they are a computer player."""
    player_data = PlayerData.from_state(state, player)

    if player_data.can_play_automatically():
        assert isinstance(player_data, ComputerPlayer)
        assert player_data.experience is not None
        learn(
            player,
            winner,
            state["memory"][player],
            player_data.experience,
            player_data.experience,
        )


def apply_learning(state: GameState, winner: Player) -> None:
    """Apply learning to computer players."""
    apply_learning_for_player(state, winner, CYAN)
    apply_learning_for_player(state, winner, VIOLET)


def board_to_dict(board: Board) -> dict:
    """Convert Board to dictionary for JSON serialization."""
    return {
        "code": board.get_code(),
        "cols": board.COLS,
        "nrows": board.NROWS,
        "pawns": {col: board[col] for col in board.COLS},
        "is_symmetrical": board.is_symmetrical(),
    }


def create_initial_state(
    board: Board, players: tuple[PlayerConfig, PlayerConfig]
) -> GameState:
    """Create the initial game state dictionary.

    First player is always CYAN.
    """
    return {
        "board_code": board.get_code(),
        "current_player": CYAN,
        "turn": 1,
        "winner": None,
        "memory": {CYAN: [], VIOLET: []},
        "players": players,
        "random_state": random.Random().getstate(),
    }


def update_game_state_after_move(
    state: GameState, new_board: Board, new_winner: Player | None, rand: random.Random
) -> list[str]:
    """Update game state after a move and return next legal moves."""
    state["random_state"] = rand.getstate()
    state["board_code"] = new_board.get_code()
    state["turn"] = state["turn"] + 1
    state["winner"] = new_winner

    if not new_winner:
        state["current_player"] = other(state["current_player"])
        return new_board.get_legal_moves(other(state["current_player"]))

    apply_learning(state, new_winner)
    return []


def validate_game_state(state: GameState | None) -> tuple[bool, str | None]:
    """Validate that game state exists and is valid.

    Return (is_valid, error_message).
    """
    if not state:
        return False, "No game in progress"

    if winner := state.get("winner"):
        return False, f"Game is already finished (winner: {winner})"

    return True, None


def get_random_generator(state: GameState) -> random.Random:
    """Get random generator from saved state or create new one."""
    rand = random.Random()
    if "random_state" in state:
        rand.setstate(state["random_state"])
    return rand


def execute_move(
    state: GameState, player_data: PlayerData, move: str | None
) -> tuple[Board, Player | None]:
    """Execute the appropriate move based on player type.

    Raise Board.IllegalMoveError or ValueError if move is invalid.
    """
    rand = get_random_generator(state)
    return player_data.execute_move(state, rand, move)


def create_move_response(
    new_board: Board, state: GameState, next_legal_moves: list[str]
) -> dict:
    """Create the JSON response for a successful move."""
    return {
        "success": True,
        "board": board_to_dict(new_board),
        "current_player": state["current_player"],
        "turn": state["turn"],
        "winner": state.get("winner"),
        "legal_moves": next_legal_moves,
    }


def save_uploaded_file(file, player: str, state: GameState | None) -> tuple[str, str]:
    """Save uploaded experience file and update game state."""
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    if state:
        player_idx = 0 if player == "player1" else 1
        # Create a new tuple with updated config
        current_players: tuple[PlayerConfig, PlayerConfig] = state["players"]
        players_list: list[PlayerConfig] = list(current_players)
        old_config: PlayerConfig = players_list[player_idx]
        new_config: PlayerConfig = {"type": old_config["type"], "exp": filepath}
        players_list[player_idx] = new_config
        new_players: tuple[PlayerConfig, PlayerConfig] = (
            players_list[0],
            players_list[1],
        )
        state["players"] = new_players
        save_game_state(state)

    return filename, filepath


def get_available_experience_files() -> list[str]:
    """Get list of available experience files in upload folder."""
    if not os.path.exists(UPLOAD_FOLDER):
        return []

    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)

    return sorted(files)


# API Blueprint routes
@api.route("/new_game", methods=["POST"])
def new_game() -> Response:
    """Start a new game."""
    data = request.get_json()

    player1_type = data.get("player1_type", "human")
    player2_type = data.get("player2_type", "human")
    player1_exp = data.get("player1_exp", None)
    player2_exp = data.get("player2_exp", None)

    board = Board(ncols=3)
    players: tuple[PlayerConfig, PlayerConfig] = (
        {"type": player1_type, "exp": player1_exp},  # CYAN
        {"type": player2_type, "exp": player2_exp},  # VIOLET
    )
    state = create_initial_state(board, players)
    save_game_state(state)

    return jsonify(
        {
            "success": True,
            "board": board_to_dict(board),
            "current_player": CYAN,
            "turn": 1,
            "legal_moves": board.get_legal_moves(CYAN),
        }
    )


@api.route("/move", methods=["POST"])
def make_move() -> tuple[Response, int]:
    """Make a move (human or computer)."""
    state = get_game_state()

    # Validate game state
    is_valid, error_msg = validate_game_state(state)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    assert state is not None
    # Extract request data
    data = request.get_json()
    move = data.get("move", None)

    # Get player configuration
    current_player = state["current_player"]
    player_data = PlayerData.from_state(state, current_player)

    try:
        # Execute the move
        new_board, new_winner = execute_move(state, player_data, move)

        # Update game state
        rand = get_random_generator(state)
        next_legal_moves = update_game_state_after_move(
            state, new_board, new_winner, rand
        )
        save_game_state(state)

        # Return response
        return jsonify(create_move_response(new_board, state, next_legal_moves)), 200

    except Board.IllegalMoveError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error making move: %s", e)
        return jsonify({"error": str(e)}), 500


@api.route("/upload_experience", methods=["POST"])
def upload_experience() -> tuple[Response, int]:
    """Upload an experience Excel file."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    player = request.form.get("player", "player1")

    if file is None or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file.filename is not None and allowed_file(file.filename):
        state = get_game_state()
        filename, filepath = save_uploaded_file(file, player, state)

        return jsonify(
            {"success": True, "filename": filename, "filepath": filepath}
        ), 200

    return jsonify({"error": "Invalid file type"}), 400


@api.route("/experience_files", methods=["GET"])
def list_experience_files() -> tuple[Response, int]:
    """Get list of available experience files."""
    files = get_available_experience_files()
    return jsonify({"success": True, "files": files}), 200


def configure_app(app: Flask, test_config=None) -> None:
    """Configure the Flask application."""
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # 32KB max file size

    if test_config is not None:
        app.config.update(test_config)


def create_app(test_config=None) -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    configure_app(app, test_config)

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Register API Blueprint
    app.register_blueprint(api)

    # Register main index route
    @app.route("/")
    def index():
        """Render the main game page."""
        return render_template("index.html")

    return app


def main() -> None:
    """Run the Flask development server."""
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "true")
    port = os.environ.get("FLASK_PORT", "5000")
    if debug == "true":
        app.run(debug=True, port=int(port))
    else:
        app.run(debug=False, host="0.0.0.0", port=int(port))


if __name__ == "__main__":
    main()
