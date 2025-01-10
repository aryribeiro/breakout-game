import streamlit as st
import streamlit.components.v1 as components
import requests
import requests_cache
import base64

# Configura o cache para armazenar as requisições HTTP
requests_cache.install_cache('sounds_cache', expire_after=86400)  # Cache válido por 1 dia

# Configuração inicial do Streamlit
st.set_page_config(page_title="Breakout Web Game", page_icon="🎮")

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

# URLs dos sons
SOUND_URLS = {
    "bounce": "https://www.soundjay.com/phone/cell-phone-1-nr7.mp3",
    "brick": "https://www.soundjay.com/mechanical/gun-gunshot-02.mp3",
    "gameOver": "https://www.soundjay.com/misc/sounds/fail-trombone-01.mp3",
    "victory": "https://www.soundjay.com/human/applause-8.mp3",
    "loseLife": "https://www.soundjay.com/misc/sounds/fail-buzzer-01.mp3",
}

# URL da logo do Python
PYTHON_LOGO_URL = "https://www.python.org/static/community_logos/python-logo.png"

# Função para carregar os sons do cache ou do site e codificar em Base64
def load_sound(url):
    response = requests.get(url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')  # Codifica em Base64
    return None

# Função para carregar a logo do Python e codificar em Base64
def load_python_logo():
    response = requests.get(PYTHON_LOGO_URL)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')  # Codifica em Base64
    return None

# Carrega a logo do Python
python_logo_base64 = load_python_logo()

# JavaScript e HTML do jogo
breakout_js = f"""
<script>
class BreakoutGame {{
    constructor(canvas) {{
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
        this.keys = {{
            ArrowLeft: false,
            ArrowRight: false,
        }};

        // Sons do jogo
        this.sounds = {{
            bounce: this.createSoundPool("data:audio/mp3;base64,{load_sound(SOUND_URLS['bounce'])}", 5),  // Pool de 5 instâncias
            brick: this.createSoundPool("data:audio/mp3;base64,{load_sound(SOUND_URLS['brick'])}", 5),    // Pool de 5 instâncias
            gameOver: this.createSoundPool("data:audio/mp3;base64,{load_sound(SOUND_URLS['gameOver'])}", 1),
            victory: this.createSoundPool("data:audio/mp3;base64,{load_sound(SOUND_URLS['victory'])}", 1),
            loseLife: this.createSoundPool("data:audio/mp3;base64,{load_sound(SOUND_URLS['loseLife'])}", 1),
        }};

        // Carrega a logo do Python
        this.pythonLogo = new Image();
        this.pythonLogo.src = "data:image/png;base64,{python_logo_base64}";
        this.pythonLogo.onload = () => {{
            this.logoWidth = 211;  // Largura da logo
            this.logoHeight = 71; // Altura da logo
            this.logoX = (this.WINDOW_WIDTH - this.logoWidth) / 2;  // Centraliza horizontalmente
            this.logoY = (this.WINDOW_HEIGHT - this.logoHeight) / 2;  // Centraliza verticalmente
        }};

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
    }}

    // Cria um pool de instâncias de áudio para evitar delays
    createSoundPool(url, poolSize) {{
        const pool = [];
        for (let i = 0; i < poolSize; i++) {{
            const audio = new Audio(url);
            pool.push(audio);
        }}
        return pool;
    }}

    // Toca um som do pool
    playSound(pool) {{
        const audio = pool.find(a => a.paused);  // Encontra uma instância disponível
        if (audio) {{
            audio.currentTime = 0;  // Reinicia o som
            audio.play();           // Toca o som
        }}
    }}

    // Função para criar os tijolos
    createBricks() {{
        const bricks = [];
        for (let row = 0; row < this.BRICK_ROWS; row++) {{
            for (let col = 0; col < this.BRICK_COLUMNS; col++) {{
                bricks.push({{
                    x: col * this.BRICK_WIDTH,
                    y: row * this.BRICK_HEIGHT + 50,
                    color: this.BRICK_COLORS[row % this.BRICK_COLORS.length],
                    width: this.BRICK_WIDTH - 2,  // Espaçamento entre tijolos
                    height: this.BRICK_HEIGHT - 2,
                }});
            }}
        }}
        return bricks;
    }}

    resetGame() {{
        this.bricks = this.createBricks();  // Usa a função createBricks para inicializar os tijolos
        this.barPosition = [this.WINDOW_WIDTH / 2 - this.BAR_WIDTH / 2, this.WINDOW_HEIGHT - this.BAR_HEIGHT - 10];
        this.ballPosition = [this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2];
        this.ballVelocity = [4, -4];  // Reinicia a velocidade da bola
        this.score = 0;
        this.lives = 3;  // Reinicia as vidas
    }}

    handleMouseDown(event) {{
        const mouseX = event.clientX - this.canvas.offsetLeft;
        const mouseY = event.clientY - this.canvas.offsetTop;
        if (
            mouseX >= this.barPosition[0] &&
            mouseX <= this.barPosition[0] + this.BAR_WIDTH &&
            mouseY >= this.barPosition[1] &&
            mouseY <= this.barPosition[1] + this.BAR_HEIGHT
        ) {{
            this.isDragging = true;
        }}
    }}

    handleMouseUp() {{
        this.isDragging = false;  // Sempre define isDragging como false ao soltar o botão do mouse
    }}

    handleMouseMove(event) {{
        if (this.isDragging && !this.keys.ArrowLeft && !this.keys.ArrowRight) {{
            const mouseX = event.clientX - this.canvas.offsetLeft;
            // Garante que a barra não ultrapasse os limites da tela
            this.barPosition[0] = Math.max(0, Math.min(this.WINDOW_WIDTH - this.BAR_WIDTH, mouseX - this.BAR_WIDTH / 2));
        }}
    }}

    handleKeyDown(event) {{
        if (event.key in this.keys) {{
            this.keys[event.key] = true;
            this.isDragging = false;  // Desativa o controle do mouse ao usar o teclado
        }}
    }}

    handleKeyUp(event) {{
        if (event.key in this.keys) {{
            this.keys[event.key] = false;
        }}
    }}

    updateBarPosition() {{
        // A velocidade da barra é proporcional à velocidade da bola
        const moveSpeed = Math.max(6, Math.abs(this.ballVelocity[0]) * 1.5);  // Velocidade dinâmica
        if (this.keys.ArrowLeft) {{
            // Move a barra para a esquerda
            this.barPosition[0] = Math.max(0, this.barPosition[0] - moveSpeed);
        }}
        if (this.keys.ArrowRight) {{
            // Move a barra para a direita
            this.barPosition[0] = Math.min(this.WINDOW_WIDTH - this.BAR_WIDTH, this.barPosition[0] + moveSpeed);
        }}
    }}

    drawBar() {{
        this.ctx.fillStyle = this.BLUE;
        this.ctx.fillRect(this.barPosition[0], this.barPosition[1], this.BAR_WIDTH, this.BAR_HEIGHT);
    }}

    drawBall() {{
        this.ctx.beginPath();
        this.ctx.arc(this.ballPosition[0], this.ballPosition[1], this.BALL_RADIUS, 0, Math.PI * 2);
        this.ctx.fillStyle = this.RED;
        this.ctx.fill();
        this.ctx.closePath();
    }}

    drawBricks() {{
        this.bricks.forEach(brick => {{
            this.ctx.fillStyle = brick.color;
            this.ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
        }});
    }}

    drawScore() {{
        this.ctx.font = "35px Arial";
        this.ctx.fillStyle = this.WHITE;
        this.ctx.fillText(`Pontos: ${{this.score}}`, 10, 30);
        this.ctx.fillText(`Vidas: ${{this.lives}}`, this.WINDOW_WIDTH - 150, 30);
        this.ctx.fillText(`Máximo: ${{this.maxScore}}`, this.WINDOW_WIDTH / 2 - 70, 30);
    }}

    drawPythonLogo() {{
        if (this.pythonLogo.complete) {{
            this.ctx.drawImage(
                this.pythonLogo,
                this.logoX,
                this.logoY,
                this.logoWidth,
                this.logoHeight
            );
        }}
    }}

    updateGame() {{
        // Limpa o canvas com a cor de fundo preta
        this.ctx.fillStyle = this.BLACK;
        this.ctx.fillRect(0, 0, this.WINDOW_WIDTH, this.WINDOW_HEIGHT);

        // Desenha a logo do Python
        this.drawPythonLogo();

        // Desenha os elementos do jogo
        this.drawBar();
        this.drawBall();
        this.drawBricks();
        this.drawScore();

        // Atualiza a lógica do jogo
        this.updateGameLogic();
    }}

    updateGameLogic() {{
        // Atualiza a posição da barra com base nas teclas pressionadas
        this.updateBarPosition();

        // Movimenta a bola
        this.ballPosition[0] += this.ballVelocity[0];
        this.ballPosition[1] += this.ballVelocity[1];

        // Verifica colisões com as bordas
        if (this.ballPosition[0] <= this.BALL_RADIUS || this.ballPosition[0] >= this.WINDOW_WIDTH - this.BALL_RADIUS) {{
            this.ballVelocity[0] *= -1;
            this.playSound(this.sounds.bounce);  // Reproduz som de colisão com a borda
        }}
        if (this.ballPosition[1] <= this.BALL_RADIUS) {{
            this.ballVelocity[1] *= -1;
            this.playSound(this.sounds.bounce);  // Reproduz som de colisão com a borda
        }}

        // Colisão com a barra
        if (
            this.ballPosition[1] + this.BALL_RADIUS >= this.barPosition[1] &&  // Verifica se a bola está na altura da barra
            this.ballPosition[0] >= this.barPosition[0] - this.BALL_RADIUS &&  // Verifica se a bola está à esquerda da barra
            this.ballPosition[0] <= this.barPosition[0] + this.BAR_WIDTH + this.BALL_RADIUS  // Verifica se a bola está à direita da barra
        ) {{
            this.ballVelocity[1] *= -1;  // Inverte a direção da bola
            this.playSound(this.sounds.bounce);  // Reproduz som de colisão com a barra
        }}

        // Colisão com os tijolos
        this.bricks.forEach((brick, index) => {{
            if (
                this.ballPosition[0] >= brick.x &&
                this.ballPosition[0] <= brick.x + brick.width &&
                this.ballPosition[1] >= brick.y &&
                this.ballPosition[1] <= brick.y + brick.height
            ) {{
                this.bricks.splice(index, 1);
                this.ballVelocity[1] *= -1;
                this.score += 10;
                this.playSound(this.sounds.brick);  // Reproduz som de colisão com tijolo

                // Aumenta a dificuldade a cada 10 pontos (reduzido para 5%)
                if (this.score % 10 === 0) {{
                    this.ballVelocity[0] *= 1.05;  // Aumenta a velocidade em 5%
                    this.ballVelocity[1] *= 1.05;
                }}

                // Atualiza a pontuação máxima
                if (this.score > this.maxScore) {{
                    this.maxScore = this.score;
                }}
            }}
        }});

        // Game over ou perda de vida
        if (this.ballPosition[1] > this.WINDOW_HEIGHT) {{
            this.lives -= 1;
            this.playSound(this.sounds.loseLife);  // Reproduz som de perder vida
            if (this.lives === 0) {{
                this.playSound(this.sounds.gameOver);  // Reproduz som de game over
                alert("                 GAME OVER!!!   Clique em OK para reiniciar o jogo.");
                this.resetGame();
            }} else {{
                this.ballPosition = [this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2];
                this.ballVelocity = [4, -4];
            }}
        }}

        // Vitória
        if (this.bricks.length === 0) {{
            this.playSound(this.sounds.victory);  // Reproduz som de vitória
            alert("                 VOCÊ VENCEU!     Clique em OK p/ reiniciar o jogo.");
            this.resetGame();
        }}
    }}

    gameLoop() {{
        this.updateGame();
        requestAnimationFrame(() => this.gameLoop());
    }}
}}

// Inicializa o jogo quando o componente é carregado
document.addEventListener("DOMContentLoaded", () => {{
    const canvas = document.getElementById("gameCanvas");
    new BreakoutGame(canvas);
}});
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
    components.html(breakout_html, height=620, width=900)

# Interface do Streamlit
st.title("🎮Breakout Web Game")
breakout_game()

# informações de contato
st.markdown("""
---
#### 🎮Breakout Web Game: em Python, Streamlit e outros.
💬 Por **Ary Ribeiro**. Contato, através do email: aryribeiro@gmail.com
\n Obs.: o app foi testado em computador. Use o teclado ou o mouse p/ controlar a barra. Caso esteja
\n usando smartphone, procure ativar o recurso **"Versão para Computador"** do navegador.
""")