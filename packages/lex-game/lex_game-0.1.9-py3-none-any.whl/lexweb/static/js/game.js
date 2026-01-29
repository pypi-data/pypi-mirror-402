// Game state
let gameState = null;
let selectedCell = null;

// Store uploaded file paths
let player1ExpPath = null;
let player2ExpPath = null;

// Player symbols
const MARKS = {
    0: ' ',
    1: '♙',
    2: '♟'
};

const PLAYER_NAMES = {
    1: 'Cyan',
    2: 'Violet'
};

const PLAYER_COLORS = {
    1: 'cyan',
    2: 'violet'
};

// Constants
const CYAN = 1;
const VIOLET = 2;

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load available experience files
    loadExperienceFiles();

    // Player type radio buttons
    document.querySelectorAll('input[name="player1Type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById('player1ExpSection').style.display =
                this.value === 'computer' ? 'block' : 'none';
        });
    });

    document.querySelectorAll('input[name="player2Type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById('player2ExpSection').style.display =
                this.value === 'computer' ? 'block' : 'none';
        });
    });

    // File upload handlers
    document.getElementById('player1Exp').addEventListener('change', function() {
        if (this.files[0]) {
            uploadExperience('player1', this.files[0]);
        }
    });

    document.getElementById('player2Exp').addEventListener('change', function() {
        if (this.files[0]) {
            uploadExperience('player2', this.files[0]);
        }
    });

    // Select dropdown handlers
    document.getElementById('player1ExpSelect').addEventListener('change', function() {
        if (this.value) {
            player1ExpPath = 'uploads/' + this.value;
            // Clear file input when selecting from dropdown
            document.getElementById('player1Exp').value = '';
        }
    });

    document.getElementById('player2ExpSelect').addEventListener('change', function() {
        if (this.value) {
            player2ExpPath = 'uploads/' + this.value;
            // Clear file input when selecting from dropdown
            document.getElementById('player2Exp').value = '';
        }
    });
});

async function loadExperienceFiles() {
    try {
        const response = await fetch('/api/experience_files');
        const result = await response.json();

        if (result.success) {
            const player1Select = document.getElementById('player1ExpSelect');
            const player2Select = document.getElementById('player2ExpSelect');

            // Clear existing options except the first one
            player1Select.innerHTML = '<option value="">-- Choose a file --</option>';
            player2Select.innerHTML = '<option value="">-- Choose a file --</option>';

            // Add available files
            result.files.forEach(file => {
                const option1 = document.createElement('option');
                option1.value = file;
                option1.textContent = file;
                player1Select.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = file;
                option2.textContent = file;
                player2Select.appendChild(option2);
            });
        }
    } catch (error) {
        console.error('Error loading experience files:', error);
    }
}

async function startNewGame() {
    const boardCode = document.getElementById('boardCode').value.trim();
    const player1Type = document.querySelector('input[name="player1Type"]:checked').value;
    const player2Type = document.querySelector('input[name="player2Type"]:checked').value;

    // Validate that computer players have experience files
    if (player1Type === 'computer' && !player1ExpPath) {
        alert('Please upload or select an experience file for Player 1 (computer)');
        return;
    }

    if (player2Type === 'computer' && !player2ExpPath) {
        alert('Please upload or select an experience file for Player 2 (computer)');
        return;
    }

    const data = {
        board_code: boardCode || null,
        player1_type: player1Type,
        player2_type: player2Type,
        player1_exp: player1ExpPath,
        player2_exp: player2ExpPath
    };

    try {
        const response = await fetch('/api/new_game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            gameState = result;
            document.getElementById('gameSetup').style.display = 'none';
            document.getElementById('gameContainer').style.display = 'block';
            renderBoard(result.board);
            updateGameStatus();

            // If current player is computer, make its move
            if (isCurrentPlayerComputer()) {
                setTimeout(makeComputerMove, 500);
            }
        } else {
            alert('Error starting game: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to start game: ' + error.message);
    }
}

function renderBoard(board) {
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';

    // Add column headers
    const headerRow = document.createElement('div');
    headerRow.className = 'board-header';
    board.cols.forEach(col => {
        const label = document.createElement('div');
        label.className = 'col-label';
        label.textContent = col;
        headerRow.appendChild(label);
    });
    boardDiv.appendChild(headerRow);

    // Add rows (from top to bottom)
    for (let row = board.nrows - 1; row >= 0; row--) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'board-row';

        board.cols.forEach(col => {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.col = col;
            cell.dataset.row = row;

            const pawn = board.pawns[col][row];
            cell.textContent = MARKS[pawn];

            if (pawn !== 0) {
                cell.classList.add(PLAYER_COLORS[pawn]);
            }

            cell.addEventListener('click', () => handleCellClick(col, row, pawn));

            rowDiv.appendChild(cell);
        });

        boardDiv.appendChild(rowDiv);
    }

    document.getElementById('boardCodeDisplay').textContent = board.code;
}

function handleCellClick(col, row, pawn) {
    if (gameState.winner) return;
    if (isCurrentPlayerComputer()) return;

    // Check if clicking on current player's pawn
    if (pawn === gameState.current_player) {
        selectCell(col, row);
    } else if (selectedCell) {
        // Try to make a move
        const move = selectedCell.col + col;
        makeMove(move);
    }
}

function selectCell(col, row) {
    // Clear previous selection
    document.querySelectorAll('.cell.selected').forEach(cell => {
        cell.classList.remove('selected');
    });

    selectedCell = { col, row };

    // Highlight selected cell
    const cells = document.querySelectorAll('.cell');
    cells.forEach(cell => {
        if (cell.dataset.col === col && parseInt(cell.dataset.row) === row) {
            cell.classList.add('selected');
        }
    });

    // Show legal moves from this position
    showLegalMovesForSelection(col);
}

function showLegalMovesForSelection(fromCol) {
    const legalMoves = gameState.legal_moves.filter(move => move[0] === fromCol);

    if (legalMoves.length > 0) {
        const movesDiv = document.getElementById('legalMoves');
        movesDiv.innerHTML = '';

        legalMoves.forEach(move => {
            const button = document.createElement('button');
            button.className = 'move-button';
            button.textContent = move;
            button.onclick = () => makeMove(move);
            movesDiv.appendChild(button);
        });

        document.getElementById('moveSelection').style.display = 'block';
    } else {
        document.getElementById('moveSelection').style.display = 'none';
    }
}

async function makeMove(move) {
    selectedCell = null;
    document.querySelectorAll('.cell.selected').forEach(cell => {
        cell.classList.remove('selected');
    });
    document.getElementById('moveSelection').style.display = 'none';

    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ move: move })
        });

        const result = await response.json();

        if (result.success) {
            gameState = result;
            renderBoard(result.board);
            updateGameStatus();

            if (result.winner) {
                showWinner(result.winner);
            } else if (isCurrentPlayerComputer()) {
                setTimeout(makeComputerMove, 500);
            }
        } else {
            alert('Invalid move: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to make move: ' + error.message);
    }
}

async function makeComputerMove() {
    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        const result = await response.json();

        if (result.success) {
            gameState = result;
            renderBoard(result.board);
            updateGameStatus();

            if (result.winner) {
                showWinner(result.winner);
            } else if (isCurrentPlayerComputer()) {
                setTimeout(makeComputerMove, 500);
            }
        } else {
            alert('Computer move failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Computer move failed: ' + error.message);
    }
}

function isCurrentPlayerComputer() {
    if (!gameState) return false;

    const player1Type = document.querySelector('input[name="player1Type"]:checked').value;
    const player2Type = document.querySelector('input[name="player2Type"]:checked').value;

    if (gameState.current_player === CYAN) {
        return player1Type === 'computer';
    } else {
        return player2Type === 'computer';
    }
}

function updateGameStatus() {
    const playerName = PLAYER_NAMES[gameState.current_player];
    const playerSymbol = MARKS[gameState.current_player];

    document.getElementById('currentPlayerSpan').textContent =
        `Current player: ${playerName} ${playerSymbol}`;
    document.getElementById('turnSpan').textContent =
        ` | Turn: ${gameState.turn}`;
}

function showWinner(winner) {
    const winnerName = PLAYER_NAMES[winner];
    const winnerSymbol = MARKS[winner];
    const message = `Player ${winnerName} ${winnerSymbol} won!!!`;

    document.getElementById('winnerMessage').textContent = message;
    document.getElementById('winnerMessage').style.display = 'block';
    document.getElementById('moveSelection').style.display = 'none';
}

function resetGame() {
    gameState = null;
    selectedCell = null;
    player1ExpPath = null;
    player2ExpPath = null;
    document.getElementById('gameSetup').style.display = 'block';
    document.getElementById('gameContainer').style.display = 'none';
    document.getElementById('winnerMessage').style.display = 'none';
    document.getElementById('player1Exp').value = '';
    document.getElementById('player2Exp').value = '';
    document.getElementById('player1ExpSelect').value = '';
    document.getElementById('player2ExpSelect').value = '';

    // Reload experience files list
    loadExperienceFiles();
}

async function uploadExperience(player, file) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('player', player);

    try {
        const response = await fetch('/api/upload_experience', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Store the file path
            if (player === 'player1') {
                player1ExpPath = result.filepath;
            } else {
                player2ExpPath = result.filepath;
            }

            // Reload the list of experience files
            await loadExperienceFiles();

            // Select the newly uploaded file in the dropdown
            const selectId = player === 'player1' ? 'player1ExpSelect' : 'player2ExpSelect';
            document.getElementById(selectId).value = result.filename;

            alert(`Experience file uploaded successfully for ${player}: ${result.filename}`);
        } else {
            alert('Upload failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Upload failed: ' + error.message);
    }
}
