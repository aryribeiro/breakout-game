import streamlit as st
import streamlit.components.v1 as components
import requests
import requests_cache
import base64

# Configura o cache para requisições HTTP
requests_cache.install_cache('sounds_cache', expire_after=86400)

# Configuração inicial do Streamlit
st.set_page_config(page_title="Breakout Web Game", page_icon="🎮", layout="wide")

st.markdown("""
    <h1 style='text-align: center;'>🎮Breakout Web Game</h1>
""", unsafe_allow_html=True)

# Configurações do jogo
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
BAR_WIDTH = 100
BAR_HEIGHT = 20
BALL_RADIUS = 10
BRICK_ROWS = 5
BRICK_COLUMNS = 9
BRICK_WIDTH = WINDOW_WIDTH // BRICK_COLUMNS
BRICK_HEIGHT = 30
FPS = 60

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
    "loseLife": "https://www.soundjay.com/misc/sounds/fail-buzzer-01.mp3"
}

# URL da logo do Python
PYTHON_LOGO_URL = "https://www.python.org/static/community_logos/python-logo.png"

# Função para carregar sons com tratamento de erro
def load_sound(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        st.error(f"Erro ao carregar som de {url}: {e}")
        return ""

# Função para carregar a logo do Python
def load_python_logo():
    try:
        response = requests.get(PYTHON_LOGO_URL, timeout=5)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        st.error(f"Erro ao carregar logo: {e}")
        return ""

# Carrega recursos
python_logo_base64 = load_python_logo()
sounds_base64 = {key: load_sound(url) for key, url in SOUND_URLS.items()}

# HTML e JavaScript do jogo
breakout_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        canvas {{
            border: 1px solid black;
            display: block;
            margin: 0 auto;
        }}
        body {{
            margin: 0;
            overflow: hidden;
            tabindex: 0;
        }}
    </style>
</head>
<body>
    <canvas id="gameCanvas" tabindex="0"></canvas>
    <script>
        class BreakoutGame {{
            constructor(canvas) {{
                this.canvas = canvas;
                this.ctx = canvas.getContext("2d");
                this.WINDOW_WIDTH = {WINDOW_WIDTH};
                this.WINDOW_HEIGHT = {WINDOW_HEIGHT};
                this.BAR_WIDTH = {BAR_WIDTH};
                this.BAR_HEIGHT = {BAR_HEIGHT};
                this.BALL_RADIUS = {BALL_RADIUS};
                this.BRICK_ROWS = {BRICK_ROWS};
                this.BRICK_COLUMNS = {BRICK_COLUMNS};
                this.BRICK_WIDTH = {BRICK_WIDTH};
                this.BRICK_HEIGHT = {BRICK_HEIGHT};
                this.FPS = {FPS};

                // Estado inicial
                this.barPosition = [this.WINDOW_WIDTH / 2 - this.BAR_WIDTH / 2, this.WINDOW_HEIGHT - this.BAR_HEIGHT - 10];
                this.ballPosition = [this.WINDOW_WIDTH / 2, this.barPosition[1] - this.BALL_RADIUS];
                this.ballVelocity = [5, -5];
                this.bricks = [];
                this.score = 0;
                this.lives = 3;
                this.gameState = "initial";
                this.ballStuckToBar = true;

                // Sons
                this.sounds = {{
                    bounce: new Audio("data:audio/mp3;base64,{sounds_base64['bounce']}"),
                    brick: new Audio("data:audio/mp3;base64,{sounds_base64['brick']}"),
                    gameOver: new Audio("data:audio/mp3;base64,{sounds_base64['gameOver']}"),
                    victory: new Audio("data:audio/mp3;base64,{sounds_base64['victory']}"),
                    loseLife: new Audio("data:audio/mp3;base64,{sounds_base64['loseLife']}")
                }};

                // Logo
                this.pythonLogo = new Image();
                this.pythonLogo.src = "data:image/png;base64,{python_logo_base64}";
                this.pythonLogo.onload = () => {{
                    this.logoWidth = 211;
                    this.logoHeight = 71;
                    this.logoX = (this.WINDOW_WIDTH - this.logoWidth) / 2;
                    this.logoY = (this.WINDOW_HEIGHT - this.logoHeight) / 2;
                }};

                // Configura canvas
                this.canvas.width = this.WINDOW_WIDTH;
                this.canvas.height = this.WINDOW_HEIGHT;

                // Inicializa tijolos
                this.createBricks();

                // Eventos
                this.setupEvents();

                // Inicia loop
                this.lastTime = performance.now();
                this.gameLoop(this.lastTime);
            }}

            createBricks() {{
                this.bricks = [];
                for (let row = 0; row < this.BRICK_ROWS; row++) {{
                    for (let col = 0; col < this.BRICK_COLUMNS; col++) {{
                        this.bricks.push({{
                            x: col * this.BRICK_WIDTH + 1,
                            y: row * this.BRICK_HEIGHT + 50,
                            width: this.BRICK_WIDTH - 2,
                            height: this.BRICK_HEIGHT - 2,
                            color: ["{RED}", "{ORANGE}", "{YELLOW}", "{GREEN}", "{BLUE}"][row % 5]
                        }});
                    }}
                }}
            }}

            setupEvents() {{
                this.canvas.addEventListener("mousemove", (e) => {{
                    const rect = this.canvas.getBoundingClientRect();
                    this.barPosition[0] = Math.max(0, Math.min(
                        this.WINDOW_WIDTH - this.BAR_WIDTH,
                        e.clientX - rect.left - this.BAR_WIDTH / 2
                    ));
                    console.log("Mouse moved, bar position:", this.barPosition[0]);
                }});
                this.canvas.addEventListener("click", () => {{
                    console.log("Canvas clicked, current state:", this.gameState);
                    if (this.gameState === "initial" || this.ballStuckToBar) {{
                        this.gameState = "playing";
                        this.ballStuckToBar = false;
                        console.log("Game started, state changed to playing");
                    }} else if (this.gameState === "gameOver" || this.gameState === "victory") {{
                        this.resetGame();
                        console.log("Game reset");
                    }}
                }});
                document.addEventListener("keydown", (e) => {{
                    if (e.code === "Space" && (this.gameState === "initial" || this.ballStuckToBar)) {{
                        console.log("Space pressed, starting game");
                        this.gameState = "playing";
                        this.ballStuckToBar = false;
                        e.preventDefault();
                    }}
                }});
            }}

            resetGame() {{
                this.score = 0;
                this.lives = 3;
                this.gameState = "initial";
                this.ballStuckToBar = true;
                this.barPosition = [this.WINDOW_WIDTH / 2 - this.BAR_WIDTH / 2, this.WINDOW_HEIGHT - this.BAR_HEIGHT - 10];
                this.ballPosition = [this.WINDOW_WIDTH / 2, this.barPosition[1] - this.BALL_RADIUS];
                this.ballVelocity = [5, -5];
                this.createBricks();
            }}

            resetBall() {{
                this.ballPosition = [this.barPosition[0] + this.BAR_WIDTH / 2, this.barPosition[1] - this.BALL_RADIUS];
                this.ballVelocity = [5, -5];
                this.ballStuckToBar = true;
            }}

            gameLoop(currentTime) {{
                const deltaTime = Math.min(currentTime - this.lastTime, 100);
                this.lastTime = currentTime;

                if (this.gameState === "playing") {{
                    this.update(deltaTime / 1000);
                }}
                this.render();

                requestAnimationFrame((time) => this.gameLoop(time));
            }}

            update(deltaTime) {{
                if (this.ballStuckToBar) {{
                    this.ballPosition[0] = this.barPosition[0] + this.BAR_WIDTH / 2;
                    return;
                }}

                this.ballPosition[0] += this.ballVelocity[0] * deltaTime * this.FPS;
                this.ballPosition[1] += this.ballVelocity[1] * deltaTime * this.FPS;

                // Colisão com paredes
                if (this.ballPosition[0] - this.BALL_RADIUS <= 0) {{
                    this.ballPosition[0] = this.BALL_RADIUS;
                    this.ballVelocity[0] = Math.abs(this.ballVelocity[0]);
                    this.playSound(this.sounds.bounce);
                }} else if (this.ballPosition[0] + this.BALL_RADIUS >= this.WINDOW_WIDTH) {{
                    this.ballPosition[0] = this.WINDOW_WIDTH - this.BALL_RADIUS;
                    this.ballVelocity[0] = -Math.abs(this.ballVelocity[0]);
                    this.playSound(this.sounds.bounce);
                }}
                if (this.ballPosition[1] - this.BALL_RADIUS <= 0) {{
                    this.ballPosition[1] = this.BALL_RADIUS;
                    this.ballVelocity[1] = Math.abs(this.ballVelocity[1]);
                    this.playSound(this.sounds.bounce);
                }}

                // Colisão com o fundo (perda de vida)
                if (this.ballPosition[1] + this.BALL_RADIUS >= this.WINDOW_HEIGHT) {{
                    this.lives--;
                    this.playSound(this.sounds.loseLife);
                    if (this.lives <= 0) {{
                        this.gameState = "gameOver";
                        this.playSound(this.sounds.gameOver);
                    }} else {{
                        this.resetBall();
                    }}
                    return;
                }}

                // Colisão com a barra
                if (
                    this.ballPosition[1] + this.BALL_RADIUS >= this.barPosition[1] &&
                    this.ballPosition[1] - this.BALL_RADIUS <= this.barPosition[1] + this.BAR_HEIGHT &&
                    this.ballPosition[0] >= this.barPosition[0] &&
                    this.ballPosition[0] <= this.barPosition[0] + this.BAR_WIDTH
                ) {{
                    const hitPos = (this.ballPosition[0] - this.barPosition[0]) / this.BAR_WIDTH;
                    const angle = (hitPos - 0.5) * Math.PI * 0.8;
                    const speed = Math.sqrt(this.ballVelocity[0] ** 2 + this.ballVelocity[1] ** 2);
                    this.ballVelocity[0] = Math.sin(angle) * speed;
                    this.ballVelocity[1] = -Math.cos(angle) * speed;
                    this.ballPosition[1] = this.barPosition[1] - this.BALL_RADIUS;
                    this.playSound(this.sounds.bounce);
                }}

                // Colisão com tijolos
                for (let i = this.bricks.length - 1; i >= 0; i--) {{
                    const brick = this.bricks[i];
                    if (
                        this.ballPosition[0] + this.BALL_RADIUS >= brick.x &&
                        this.ballPosition[0] - this.BALL_RADIUS <= brick.x + brick.width &&
                        this.ballPosition[1] + this.BALL_RADIUS >= brick.y &&
                        this.ballPosition[1] - this.BALL_RADIUS <= brick.y + brick.height
                    ) {{
                        this.bricks.splice(i, 1);
                        this.score += 10;
                        this.ballVelocity[1] *= -1;
                        this.playSound(this.sounds.brick);
                        if (this.bricks.length === 0) {{
                            this.gameState = "victory";
                            this.playSound(this.sounds.victory);
                        }}
                        break;
                    }}
                }}
            }}

            playSound(audio) {{
                if (audio.src.includes("base64,,")) return;
                audio.currentTime = 0;
                audio.play().catch((e) => console.error("Erro ao tocar som:", e));
            }}

            render() {{
                // Limpa o canvas
                this.ctx.fillStyle = "{BLACK}";
                this.ctx.fillRect(0, 0, this.WINDOW_WIDTH, this.WINDOW_HEIGHT);

                // Desenha logo
                if (this.pythonLogo.complete) {{
                    this.ctx.globalAlpha = this.gameState === "playing" ? 0.2 : 1.0;
                    this.ctx.drawImage(this.pythonLogo, this.logoX, this.logoY, this.logoWidth, this.logoHeight);
                    this.ctx.globalAlpha = 1.0;
                }}

                // Desenha barra
                this.ctx.fillStyle = "{BLUE}";
                this.ctx.fillRect(this.barPosition[0], this.barPosition[1], this.BAR_WIDTH, this.BAR_HEIGHT);

                // Desenha bola
                this.ctx.beginPath();
                this.ctx.arc(this.ballPosition[0], this.ballPosition[1], this.BALL_RADIUS, 0, Math.PI * 2);
                this.ctx.fillStyle = "{RED}";
                this.ctx.fill();
                this.ctx.closePath();

                // Desenha tijolos
                this.bricks.forEach((brick) => {{
                    this.ctx.fillStyle = brick.color;
                    this.ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
                }});

                // Desenha HUD
                this.ctx.fillStyle = "{RED}";
                this.ctx.font = "24px Arial";
                this.ctx.textAlign = "left";
                this.ctx.fillText(`Score: ${{this.score}} Lives: ${{this.lives}}`, 10, 30);

                // Desenha mensagens
                this.ctx.textAlign = "center";
                this.ctx.font = "54px Arial Black";
                if (this.gameState === "initial" || this.ballStuckToBar) {{
                    this.ctx.fillText("clique no mouse", this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2 + 50);
                }} else if (this.gameState === "gameOver") {{
                    this.ctx.fillText("Game Over!", this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2);
                }} else if (this.gameState === "victory") {{
                    this.ctx.fillText("Vitória!", this.WINDOW_WIDTH / 2, this.WINDOW_HEIGHT / 2);
                }}
            }}
        }}

        // Inicializa o jogo
        window.addEventListener('DOMContentLoaded', () => {{
            try {{
                const canvas = document.getElementById("gameCanvas");
                if (!canvas) throw new Error("Canvas não encontrado");
                const game = new BreakoutGame(canvas);
                console.log("Jogo Breakout inicializado com sucesso");
                document.body.focus();
            }} catch (e) {{
                console.error("Erro ao inicializar o jogo:", e);
            }}
        }});
    </script>
</body>
</html>
"""

# Renderiza o jogo
components.html(breakout_html, height=WINDOW_HEIGHT + 50, scrolling=False)

st.markdown("""
<div style="text-align: center;">
    <h4>🎮Breakout Web Game: em Python, Streamlit e outros.</h4>
    💬 Por <strong>Ary Ribeiro</strong>. Contato, através do email: <a href="mailto:aryribeiro@gmail.com">aryribeiro@gmail.com</a><br><br>
    <em>Obs.: o app foi testado apenas em computador. Use o mouse p/ controlar a barra.<br>
    No smartphone, procure ativar o recurso <strong>"Versão para Computador"</strong> do navegador.</em>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #333333;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* Esconde completamente todos os elementos da barra padrão do Streamlit */
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    /* Remove qualquer espaço em branco adicional */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Remove quaisquer margens extras */
    .element-container {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)