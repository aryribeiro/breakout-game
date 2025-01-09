import streamlit as st
import streamlit.components.v1 as components

# Configurações básicas
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BAR_WIDTH = 100
BAR_HEIGHT = 20
BALL_RADIUS = 10
BRICK_ROWS = 5
BRICK_COLUMNS = 9
BRICK_WIDTH = WINDOW_WIDTH // BRICK_COLUMNS
BRICK_HEIGHT = 30
FPS = 60  # Quadros por segundo

# Cores
BLACK = "#000000"
WHITE = "#FFFFFF"
RED = "#FF0000"
ORANGE = "#FFA500"
YELLOW = "#FFFF00"
GREEN = "#00FF00"
BLUE = "#0000FF"
BRICK_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE]

# JavaScript e HTML do jogo
breakout_js = """
<script>
class BreakoutGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d");

        // Configurações do jogo
        this.WINDOW_WIDTH = 800;
        this.WINDOW_HEIGHT = 600;
        this.BAR_WIDTH = 100;
        this.BAR_HEIGHT = 20;
        this.BALL_RADIUS = 10;
        this.BRICK_ROWS = 5;
        this.BRICK_COLUMNS = 9;
        this.BRICK_WIDTH = this.WINDOW_WIDTH / this.BRICK_COLUMNS;
        this.BRICK_HEIGHT = 30;
        this.FPS = 60;

        // Cores
        this.BLACK = "#000000";
        this.WHITE = "#FFFFFF";
        this.RED = "#FF0000";
        this.ORANGE = "#FFA500";
        this.YELLOW = "#FFFF00";
        this.GREEN = "#00FF00";
        this.BLUE = "#0000FF";
        this.BRICK_COLORS = [this.RED, this.ORANGE, this.YELLOW, this.GREEN, this.BLUE];

        // Estado inicial
        this.barPosition = [this.WINDOW_WIDTH / 2 - this.BAR_WIDTH / 2, this.WINDOW_HEIGHT - this.BAR_HEIGHT - 10];
        this.ballPosition = [this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2];
        this.ballVelocity = [4, -4];  // Velocidade inicial da bola
        this.bricks = [];
        this.score = 0;
        this.lives = 3;  // Vidas do jogador
        this.maxScore = 0;  // Pontuação máxima
        this.isDragging = false;

        // Rastreamento das teclas pressionadas
        this.keys = {
            ArrowLeft: false,
            ArrowRight: false,
        };

        // Inicializa os tijolos
        this.resetGame();

        // Configura o canvas
        this.canvas.width = this.WINDOW_WIDTH;
        this.canvas.height = this.WINDOW_HEIGHT;

        // Eventos do mouse
        this.canvas.addEventListener("mousedown", (event) => this.handleMouseDown(event));
        this.canvas.addEventListener("mouseup", () => this.handleMouseUp());
        this.canvas.addEventListener("mousemove", (event) => this.handleMouseMove(event));

        // Eventos do teclado
        document.addEventListener("keydown", (event) => this.handleKeyDown(event));
        document.addEventListener("keyup", (event) => this.handleKeyUp(event));

        // Inicia o jogo
        this.gameLoop();
    }

    // Função para criar os tijolos
    createBricks() {
        const bricks = [];
        for (let row = 0; row < this.BRICK_ROWS; row++) {
            for (let col = 0; col < this.BRICK_COLUMNS; col++) {
                bricks.push({
                    x: col * this.BRICK_WIDTH,
                    y: row * this.BRICK_HEIGHT + 50,
                    color: this.BRICK_COLORS[row % this.BRICK_COLORS.length],
                    width: this.BRICK_WIDTH - 2,  // Espaçamento entre tijolos
                    height: this.BRICK_HEIGHT - 2,
                });
            }
        }
        return bricks;
    }

    resetGame() {
        this.bricks = this.createBricks();  // Usa a função createBricks para inicializar os tijolos
        this.barPosition = [this.WINDOW_WIDTH / 2 - this.BAR_WIDTH / 2, this.WINDOW_HEIGHT - this.BAR_HEIGHT - 10];
        this.ballPosition = [this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2];
        this.ballVelocity = [4, -4];  // Reinicia a velocidade da bola
        this.score = 0;
        this.lives = 3;  // Reinicia as vidas
    }

    handleMouseDown(event) {
        const mouseX = event.clientX - this.canvas.offsetLeft;
        const mouseY = event.clientY - this.canvas.offsetTop;
        if (
            mouseX >= this.barPosition[0] &&
            mouseX <= this.barPosition[0] + this.BAR_WIDTH &&
            mouseY >= this.barPosition[1] &&
            mouseY <= this.barPosition[1] + this.BAR_HEIGHT
        ) {
            this.isDragging = true;
        }
    }

    handleMouseUp() {
        this.isDragging = false;  // Sempre define isDragging como false ao soltar o botão do mouse
    }

    handleMouseMove(event) {
        if (this.isDragging && !this.keys.ArrowLeft && !this.keys.ArrowRight) {
            const mouseX = event.clientX - this.canvas.offsetLeft;
            // Garante que a barra não ultrapasse os limites da tela
            this.barPosition[0] = Math.max(0, Math.min(this.WINDOW_WIDTH - this.BAR_WIDTH, mouseX - this.BAR_WIDTH / 2));
        }
    }

    handleKeyDown(event) {
        if (event.key in this.keys) {
            this.keys[event.key] = true;
            this.isDragging = false;  // Desativa o controle do mouse ao usar o teclado
        }
    }

    handleKeyUp(event) {
        if (event.key in this.keys) {
            this.keys[event.key] = false;
        }
    }

    updateBarPosition() {
        // A velocidade da barra é proporcional à velocidade da bola
        const moveSpeed = Math.max(6, Math.abs(this.ballVelocity[0]) * 1.5);  // Velocidade dinâmica
        if (this.keys.ArrowLeft) {
            // Move a barra para a esquerda
            this.barPosition[0] = Math.max(0, this.barPosition[0] - moveSpeed);
        }
        if (this.keys.ArrowRight) {
            // Move a barra para a direita
            this.barPosition[0] = Math.min(this.WINDOW_WIDTH - this.BAR_WIDTH, this.barPosition[0] + moveSpeed);
        }
    }

    drawBar() {
        this.ctx.fillStyle = this.BLUE;
        this.ctx.fillRect(this.barPosition[0], this.barPosition[1], this.BAR_WIDTH, this.BAR_HEIGHT);
    }

    drawBall() {
        this.ctx.beginPath();
        this.ctx.arc(this.ballPosition[0], this.ballPosition[1], this.BALL_RADIUS, 0, Math.PI * 2);
        this.ctx.fillStyle = this.RED;
        this.ctx.fill();
        this.ctx.closePath();
    }

    drawBricks() {
        this.bricks.forEach(brick => {
            this.ctx.fillStyle = brick.color;
            this.ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
        });
    }

    drawScore() {
        this.ctx.font = "35px Arial";
        this.ctx.fillStyle = this.WHITE;
        this.ctx.fillText(`Pontos: ${this.score}`, 10, 30);
        this.ctx.fillText(`Vidas: ${this.lives}`, this.WINDOW_WIDTH - 150, 30);
        this.ctx.fillText(`Máximo: ${this.maxScore}`, this.WINDOW_WIDTH / 2 - 70, 30);
    }

    updateGame() {
        // Atualiza a posição da barra com base nas teclas pressionadas
        this.updateBarPosition();

        // Movimenta a bola
        this.ballPosition[0] += this.ballVelocity[0];
        this.ballPosition[1] += this.ballVelocity[1];

        // Verifica colisões com as bordas
        if (this.ballPosition[0] <= this.BALL_RADIUS || this.ballPosition[0] >= this.WINDOW_WIDTH - this.BALL_RADIUS) {
            this.ballVelocity[0] *= -1;
        }
        if (this.ballPosition[1] <= this.BALL_RADIUS) {
            this.ballVelocity[1] *= -1;
        }

        // Colisão com a barra
        if (
            this.ballPosition[1] + this.BALL_RADIUS >= this.barPosition[1] &&  // Verifica se a bola está na altura da barra
            this.ballPosition[0] >= this.barPosition[0] - this.BALL_RADIUS &&  // Verifica se a bola está à esquerda da barra
            this.ballPosition[0] <= this.barPosition[0] + this.BAR_WIDTH + this.BALL_RADIUS  // Verifica se a bola está à direita da barra
        ) {
            this.ballVelocity[1] *= -1;  // Inverte a direção da bola
        }

        // Colisão com os tijolos
        this.bricks.forEach((brick, index) => {
            if (
                this.ballPosition[0] >= brick.x &&
                this.ballPosition[0] <= brick.x + brick.width &&
                this.ballPosition[1] >= brick.y &&
                this.ballPosition[1] <= brick.y + brick.height
            ) {
                this.bricks.splice(index, 1);
                this.ballVelocity[1] *= -1;
                this.score += 10;

                // Aumenta a dificuldade a cada 10 pontos (reduzido para 5%)
                if (this.score % 10 === 0) {
                    this.ballVelocity[0] *= 1.05;  // Aumenta a velocidade em 5%
                    this.ballVelocity[1] *= 1.05;
                }

                // Atualiza a pontuação máxima
                if (this.score > this.maxScore) {
                    this.maxScore = this.score;
                }
            }
        });

        // Game over
        if (this.ballPosition[1] > this.WINDOW_HEIGHT) {
            this.lives -= 1;
            if (this.lives === 0) {
                alert("Game Over! Clique para reiniciar.");
                this.resetGame();
            } else {
                this.ballPosition = [this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2];
                this.ballVelocity = [4, -4];
            }
        }

        // Vitória
        if (this.bricks.length === 0) {
            alert("Você venceu! Clique para reiniciar.");
            this.resetGame();
        }
    }

    gameLoop() {
        this.ctx.clearRect(0, 0, this.WINDOW_WIDTH, this.WINDOW_HEIGHT);
        this.drawBar();
        this.drawBall();
        this.drawBricks();
        this.drawScore();
        this.updateGame();
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Inicializa o jogo quando o componente é carregado
document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("gameCanvas");
    new BreakoutGame(canvas);
});
</script>
"""

# HTML do jogo
breakout_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Breakout Game</title>
    <style>
        canvas {{
            display: block;
            margin: 0 auto;
            background: {BLACK};
        }}
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    {breakout_js}
</body>
</html>
"""

# Exibe o jogo no Streamlit
def breakout_game():
    components.html(breakout_html, height=900, width=900)

# Interface do Streamlit
st.title("Breakout Game")
breakout_game()