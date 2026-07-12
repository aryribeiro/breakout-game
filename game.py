import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os

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

# Progressão de dificuldade
MAX_LEVEL = 5
BALL_SPEED = 7.0          # velocidade da bola no nível 1 (px por frame de 60fps)
LEVEL_SPEED_STEP = 0.10   # +10% de velocidade a cada nível
RALLY_ACCEL = 1.015       # aceleração a cada rebatida na barra
RALLY_MAX = 1.5           # teto da aceleração dentro de um mesmo nível
LIVES = 3

# Cores
BLACK = "#000000"
RED = "#FF0000"
ORANGE = "#FFA500"
YELLOW = "#FFFF00"
GREEN = "#00FF00"
BLUE = "#0000FF"
BRICK_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE]

# Arquivos de som locais (pasta "som")
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "som")
SOUND_FILES = {
    "bounce": "cell-phone-1-nr7.mp3",
    "brick": "gun-gunshot-02.mp3",
    "gameOver": "fail-trombone-01.mp3",
    "victory": "applause-8.mp3",
    "loseLife": "fail-buzzer-01.mp3"
}

# Logo local do Python (pasta "som")
PYTHON_LOGO_FILE = "python-logo.png"


# Função para carregar arquivos locais em base64 com tratamento de erro
@st.cache_data
def load_asset(filename):
    filepath = os.path.join(SOUND_DIR, filename)
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Erro ao carregar arquivo {filepath}: {e}")
        return ""


def data_uri(mime, encoded):
    return f"data:{mime};base64,{encoded}" if encoded else ""


# Carrega recursos
python_logo_base64 = load_asset(PYTHON_LOGO_FILE)
sounds_base64 = {key: load_asset(filename) for key, filename in SOUND_FILES.items()}

# Configuração entregue ao JavaScript como JSON, para não misturar as chaves
# do JS com as da f-string do Python.
GAME_CONFIG = {
    "windowWidth": WINDOW_WIDTH,
    "windowHeight": WINDOW_HEIGHT,
    "barWidth": BAR_WIDTH,
    "barHeight": BAR_HEIGHT,
    "ballRadius": BALL_RADIUS,
    "brickRows": BRICK_ROWS,
    "brickColumns": BRICK_COLUMNS,
    "brickWidth": BRICK_WIDTH,
    "brickHeight": BRICK_HEIGHT,
    "fps": FPS,
    "maxLevel": MAX_LEVEL,
    "ballSpeed": BALL_SPEED,
    "levelSpeedStep": LEVEL_SPEED_STEP,
    "rallyAccel": RALLY_ACCEL,
    "rallyMax": RALLY_MAX,
    "lives": LIVES,
    "brickColors": BRICK_COLORS,
    "colors": {
        "black": BLACK,
        "red": RED,
        "blue": BLUE,
        "green": GREEN,
        "yellow": YELLOW,
    },
    "logo": data_uri("image/png", python_logo_base64),
    "sounds": {key: data_uri("audio/mp3", value) for key, value in sounds_base64.items()},
}

GAME_CSS = """
    body {
        margin: 0;
        overflow: hidden;
        background: transparent;
    }
    #wrap {
        width: 100%;
        max-width: 900px;
        margin: 0 auto;
    }
    #gameCanvas {
        display: block;
        width: 100%;
        aspect-ratio: 900 / 600;
        /* moldura via box-shadow: uma borda somaria 2px à largura e
           desalinharia a conversão de pixel da tela para coordenada do jogo */
        box-shadow: 0 0 0 1px #333;
        border-radius: 4px;
        background: #000;
        cursor: none;
        outline: none;
        touch-action: none;
    }
    #controls {
        display: flex;
        justify-content: flex-end;
        margin-top: 8px;
    }
    #muteBtn {
        /* as fontes de emoji no fim do stack garantem o ícone colorido */
        font: 500 14px system-ui, -apple-system, "Segoe UI", sans-serif,
              "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji";
        color: #888;
        background: transparent;
        border: 1px solid #888;
        border-radius: 6px;
        padding: 5px 12px;
        cursor: pointer;
    }
    #muteBtn:hover {
        color: #ccc;
        border-color: #ccc;
    }
"""

GAME_JS = """
(function () {
    const cfg = window.__BREAKOUT_CFG__;
    const W = cfg.windowWidth;
    const H = cfg.windowHeight;
    const BAR_W = cfg.barWidth;
    const BAR_H = cfg.barHeight;
    const R = cfg.ballRadius;
    const BRICK_W = cfg.brickWidth;
    const BRICK_H = cfg.brickHeight;
    const IS_TOUCH = window.matchMedia("(hover: none)").matches;
    const ACTION = IS_TOUCH ? "toque" : "clique";
    const MAX_PARTICLES = 300;

    // localStorage pode lançar em contextos restritos: degrada para memória.
    const store = {
        get(key, fallback) {
            try {
                const value = localStorage.getItem(key);
                return value === null ? fallback : value;
            } catch (e) {
                return fallback;
            }
        },
        set(key, value) {
            try {
                localStorage.setItem(key, value);
            } catch (e) { /* sem persistência */ }
        }
    };

    // Um único objeto Audio por som corta o som anterior quando dois tocam
    // juntos; sons curtos e sobrepostos ganham um pool de canais.
    class SoundBank {
        constructor(sources) {
            this.muted = store.get("breakout:muted", "0") === "1";
            this.channels = {};
            for (const [name, src] of Object.entries(sources)) {
                if (!src) continue;
                const size = (name === "bounce" || name === "brick") ? 5 : 1;
                this.channels[name] = {
                    pool: Array.from({ length: size }, () => new Audio(src)),
                    next: 0
                };
            }
        }

        play(name, volume = 1) {
            if (this.muted) return;
            const channel = this.channels[name];
            if (!channel) return;
            const audio = channel.pool[channel.next];
            channel.next = (channel.next + 1) % channel.pool.length;
            audio.volume = volume;
            audio.currentTime = 0;
            audio.play().catch(() => { /* autoplay bloqueado até o 1º gesto */ });
        }

        stopAll() {
            for (const channel of Object.values(this.channels)) {
                for (const audio of channel.pool) {
                    audio.pause();
                    audio.currentTime = 0;
                }
            }
        }

        toggleMute() {
            this.muted = !this.muted;
            if (this.muted) this.stopAll();
            store.set("breakout:muted", this.muted ? "1" : "0");
            return this.muted;
        }
    }

    class BreakoutGame {
        constructor(canvas, sounds) {
            this.canvas = canvas;
            this.ctx = canvas.getContext("2d");
            this.sounds = sounds;
            this.canvas.width = W;
            this.canvas.height = H;

            this.logo = new Image();
            this.logo.src = cfg.logo;
            this.logoWidth = 211;
            this.logoHeight = 71;
            this.logoX = (W - this.logoWidth) / 2;
            this.logoY = (H - this.logoHeight) / 2;

            this.highScore = parseInt(store.get("breakout:highscore", "0"), 10) || 0;
            this.particles = [];
            this.shakeMag = 0;
            this.shakeTime = 0;
            this.shakeDuration = 1;
            this.flashTime = 0;
            this.flashDuration = 1;
            this.flashColor = "#FFFFFF";
            this.paddleFlash = 0;

            this.resetGame();
            this.setupEvents();

            this.lastTime = performance.now();
            this.gameLoop(this.lastTime);
        }

        // ---------- estado ----------

        resetGame() {
            this.score = 0;
            this.lives = cfg.lives;
            this.level = 1;
            this.newRecord = false;
            this.gameState = "initial";
            this.barPosition = [W / 2 - BAR_W / 2, H - BAR_H - 10];
            this.startLevel();
        }

        startLevel() {
            this.createBricks();
            this.resetBall();
        }

        resetBall() {
            this.speed = cfg.ballSpeed * (1 + cfg.levelSpeedStep * (this.level - 1));
            this.maxSpeed = this.speed * cfg.rallyMax;
            const direction = Math.random() < 0.5 ? -1 : 1;
            this.ballVelocity = [
                direction * this.speed * Math.SQRT1_2,
                -this.speed * Math.SQRT1_2
            ];
            this.ballPosition = [this.barPosition[0] + BAR_W / 2, this.barPosition[1] - R];
            this.ballStuckToBar = true;
            this.trail = [];
        }

        createBricks() {
            this.bricks = [];
            // A partir do nível 2 as fileiras de cima passam a exigir 2 acertos.
            const toughRows = Math.min(Math.max(this.level - 1, 0), 3);
            for (let row = 0; row < cfg.brickRows; row++) {
                for (let col = 0; col < cfg.brickColumns; col++) {
                    this.bricks.push({
                        x: col * BRICK_W + 1,
                        y: row * BRICK_H + 50,
                        width: BRICK_W - 2,
                        height: BRICK_H - 2,
                        color: cfg.brickColors[row % cfg.brickColors.length],
                        hits: row < toughRows ? 2 : 1
                    });
                }
            }
        }

        addScore(points) {
            this.score += points;
            if (this.score > this.highScore) {
                this.highScore = this.score;
                this.newRecord = true;
                store.set("breakout:highscore", String(this.highScore));
            }
        }

        // ---------- eventos ----------

        setupEvents() {
            this.canvas.addEventListener("mousemove", (e) => this.moveBar(e.clientX));
            this.canvas.addEventListener("click", () => this.handleAction());
            this.canvas.addEventListener("touchstart", (e) => {
                e.preventDefault();
                this.moveBar(e.touches[0].clientX);
                this.handleAction();
            }, { passive: false });
            this.canvas.addEventListener("touchmove", (e) => {
                e.preventDefault();
                this.moveBar(e.touches[0].clientX);
            }, { passive: false });

            document.addEventListener("keydown", (e) => {
                if (e.code === "Space") {
                    e.preventDefault();
                    this.handleAction();
                } else if (e.code === "KeyP" || e.code === "Escape") {
                    e.preventDefault();
                    this.togglePause();
                } else if (e.code === "KeyM") {
                    e.preventDefault();
                    this.onMuteToggle();
                }
            });

            document.addEventListener("visibilitychange", () => {
                if (document.hidden && this.gameState === "playing") this.togglePause();
            });
        }

        // O canvas escala por CSS, então o pixel da tela precisa virar
        // coordenada do jogo antes de posicionar a barra.
        moveBar(clientX) {
            const rect = this.canvas.getBoundingClientRect();
            if (!rect.width) return;
            const x = (clientX - rect.left) * (W / rect.width);
            this.barPosition[0] = Math.max(0, Math.min(W - BAR_W, x - BAR_W / 2));
        }

        handleAction() {
            if (this.gameState === "initial") {
                this.gameState = "playing";
                this.ballStuckToBar = false;
            } else if (this.gameState === "playing") {
                this.ballStuckToBar = false;
            } else if (this.gameState === "levelComplete") {
                this.level++;
                this.startLevel();
                this.gameState = "playing";
            } else if (this.gameState === "gameOver" || this.gameState === "victory") {
                this.resetGame();
            }
        }

        togglePause() {
            if (this.gameState === "playing") {
                this.gameState = "paused";
            } else if (this.gameState === "paused") {
                this.gameState = "playing";
                this.lastTime = performance.now();
            }
        }

        onMuteToggle() {
            const muted = this.sounds.toggleMute();
            const button = document.getElementById("muteBtn");
            if (button) {
                button.textContent = muted ? "🔇 Mudo" : "🔊 Som";
                button.setAttribute("aria-pressed", String(muted));
            }
            this.canvas.focus();
        }

        // ---------- efeitos ----------

        addShake(magnitude, duration) {
            this.shakeMag = Math.max(this.shakeMag, magnitude);
            this.shakeTime = Math.max(this.shakeTime, duration);
            this.shakeDuration = Math.max(this.shakeDuration, this.shakeTime);
        }

        addFlash(color, duration) {
            this.flashColor = color;
            this.flashTime = duration;
            this.flashDuration = duration;
        }

        spawnParticles(x, y, color, count, speed) {
            for (let i = 0; i < count && this.particles.length < MAX_PARTICLES; i++) {
                const angle = Math.random() * Math.PI * 2;
                const magnitude = speed * (0.3 + Math.random() * 0.7);
                const life = 0.35 + Math.random() * 0.35;
                this.particles.push({
                    x: x,
                    y: y,
                    vx: Math.cos(angle) * magnitude,
                    vy: Math.sin(angle) * magnitude - 40,
                    life: life,
                    maxLife: life,
                    size: 2 + Math.random() * 2,
                    color: color
                });
            }
        }

        // Roda em todos os frames, inclusive nos estados de menu: os efeitos
        // precisam terminar de decair mesmo depois do game over.
        updateEffects(deltaTime) {
            this.shakeTime = Math.max(0, this.shakeTime - deltaTime);
            if (this.shakeTime === 0) {
                this.shakeMag = 0;
                this.shakeDuration = 1;
            }
            this.flashTime = Math.max(0, this.flashTime - deltaTime);
            this.paddleFlash = Math.max(0, this.paddleFlash - deltaTime);

            for (let i = this.particles.length - 1; i >= 0; i--) {
                const particle = this.particles[i];
                particle.life -= deltaTime;
                if (particle.life <= 0) {
                    this.particles.splice(i, 1);
                    continue;
                }
                particle.vy += 500 * deltaTime;
                particle.x += particle.vx * deltaTime;
                particle.y += particle.vy * deltaTime;
            }
        }

        // ---------- loop ----------

        gameLoop(currentTime) {
            const deltaTime = Math.min(currentTime - this.lastTime, 100) / 1000;
            this.lastTime = currentTime;

            if (this.gameState === "playing") this.update(deltaTime);
            this.updateEffects(deltaTime);
            this.render();

            requestAnimationFrame((time) => this.gameLoop(time));
        }

        update(deltaTime) {
            if (this.ballStuckToBar) {
                this.ballPosition[0] = this.barPosition[0] + BAR_W / 2;
                this.ballPosition[1] = this.barPosition[1] - R;
                return;
            }

            // Divide o movimento em sub-passos de no máximo um raio de bola,
            // para não atravessar tijolos/barra em frames lentos (tunneling)
            const frameScale = deltaTime * cfg.fps;
            const speed = Math.hypot(this.ballVelocity[0], this.ballVelocity[1]);
            const steps = Math.max(1, Math.ceil((speed * frameScale) / R));

            for (let i = 0; i < steps; i++) {
                this.ballPosition[0] += this.ballVelocity[0] * frameScale / steps;
                this.ballPosition[1] += this.ballVelocity[1] * frameScale / steps;
                if (!this.handleCollisions()) return;
            }

            this.trail.push([this.ballPosition[0], this.ballPosition[1]]);
            if (this.trail.length > 12) this.trail.shift();
        }

        // Retorna false quando a bola foi perdida ou o nível terminou (interrompe os sub-passos)
        handleCollisions() {
            // Colisão com paredes
            if (this.ballPosition[0] - R <= 0) {
                this.ballPosition[0] = R;
                this.ballVelocity[0] = Math.abs(this.ballVelocity[0]);
                this.sounds.play("bounce");
            } else if (this.ballPosition[0] + R >= W) {
                this.ballPosition[0] = W - R;
                this.ballVelocity[0] = -Math.abs(this.ballVelocity[0]);
                this.sounds.play("bounce");
            }
            if (this.ballPosition[1] - R <= 0) {
                this.ballPosition[1] = R;
                this.ballVelocity[1] = Math.abs(this.ballVelocity[1]);
                this.sounds.play("bounce");
            }

            // Colisão com o fundo (perda de vida)
            if (this.ballPosition[1] + R >= H) {
                this.lives--;
                this.sounds.play("loseLife");
                this.spawnParticles(this.ballPosition[0], H - R, cfg.colors.red, 18, 140);
                this.addShake(8, 0.35);
                this.addFlash(cfg.colors.red, 0.4);
                if (this.lives <= 0) {
                    this.gameState = "gameOver";
                    this.sounds.play("gameOver");
                    this.addShake(10, 0.5);
                } else {
                    this.resetBall();
                }
                return false;
            }

            // Colisão com a barra (apenas com a bola descendo, considerando o raio)
            if (
                this.ballVelocity[1] > 0 &&
                this.ballPosition[1] + R >= this.barPosition[1] &&
                this.ballPosition[1] - R <= this.barPosition[1] + BAR_H &&
                this.ballPosition[0] + R >= this.barPosition[0] &&
                this.ballPosition[0] - R <= this.barPosition[0] + BAR_W
            ) {
                const hitPos = Math.max(0, Math.min(1,
                    (this.ballPosition[0] - this.barPosition[0]) / BAR_W
                ));
                this.speed = Math.min(this.speed * cfg.rallyAccel, this.maxSpeed);
                const angle = (hitPos - 0.5) * Math.PI * 0.8;
                this.ballVelocity[0] = Math.sin(angle) * this.speed;
                this.ballVelocity[1] = -Math.cos(angle) * this.speed;
                this.ballPosition[1] = this.barPosition[1] - R;
                this.paddleFlash = 0.12;
                this.addShake(1, 0.05);
                this.sounds.play("bounce");
            }

            // Colisão com tijolos
            for (let i = this.bricks.length - 1; i >= 0; i--) {
                const brick = this.bricks[i];
                if (
                    this.ballPosition[0] + R >= brick.x &&
                    this.ballPosition[0] - R <= brick.x + brick.width &&
                    this.ballPosition[1] + R >= brick.y &&
                    this.ballPosition[1] - R <= brick.y + brick.height
                ) {
                    // Rebate no eixo de menor penetração: lateral inverte X, topo/fundo inverte Y
                    const overlapX = this.ballPosition[0] < brick.x + brick.width / 2
                        ? this.ballPosition[0] + R - brick.x
                        : brick.x + brick.width - (this.ballPosition[0] - R);
                    const overlapY = this.ballPosition[1] < brick.y + brick.height / 2
                        ? this.ballPosition[1] + R - brick.y
                        : brick.y + brick.height - (this.ballPosition[1] - R);
                    if (overlapX < overlapY) {
                        this.ballVelocity[0] *= -1;
                    } else {
                        this.ballVelocity[1] *= -1;
                    }

                    const centerX = brick.x + brick.width / 2;
                    const centerY = brick.y + brick.height / 2;
                    brick.hits--;
                    if (brick.hits <= 0) {
                        this.bricks.splice(i, 1);
                        this.addScore(10);
                        this.spawnParticles(centerX, centerY, brick.color, 14, 160);
                        this.addShake(3, 0.12);
                        this.sounds.play("brick");
                    } else {
                        this.addScore(5);
                        this.spawnParticles(centerX, centerY, "#FFFFFF", 6, 90);
                        this.addShake(1.5, 0.07);
                        this.sounds.play("brick", 0.5);
                    }

                    if (this.bricks.length === 0) {
                        this.addFlash("#FFFFFF", 0.35);
                        if (this.level >= cfg.maxLevel) {
                            this.gameState = "victory";
                            this.sounds.play("victory");
                            this.addShake(6, 0.5);
                        } else {
                            this.gameState = "levelComplete";
                            this.sounds.play("victory", 0.6);
                        }
                        return false;
                    }
                    break;
                }
            }

            return true;
        }

        // ---------- render ----------

        render() {
            const ctx = this.ctx;

            // Fundo desenhado sem shake, para o tremor não revelar as bordas
            ctx.fillStyle = cfg.colors.black;
            ctx.fillRect(0, 0, W, H);

            ctx.save();
            if (this.shakeTime > 0) {
                const intensity = (this.shakeTime / this.shakeDuration) * this.shakeMag;
                ctx.translate(
                    (Math.random() * 2 - 1) * intensity,
                    (Math.random() * 2 - 1) * intensity
                );
            }

            this.drawLogo(ctx);
            this.drawBricks(ctx);
            this.drawTrail(ctx);
            this.drawBall(ctx);
            this.drawBar(ctx);
            this.drawParticles(ctx);
            ctx.restore();

            if (this.flashTime > 0) {
                ctx.globalAlpha = (this.flashTime / this.flashDuration) * 0.35;
                ctx.fillStyle = this.flashColor;
                ctx.fillRect(0, 0, W, H);
                ctx.globalAlpha = 1;
            }

            this.drawHud(ctx);
            this.drawMessages(ctx);
        }

        drawLogo(ctx) {
            // naturalWidth > 0 garante imagem decodificada com sucesso
            if (!this.logo.complete || this.logo.naturalWidth === 0) return;
            ctx.globalAlpha = this.gameState === "playing" ? 0.2 : 1.0;
            ctx.drawImage(this.logo, this.logoX, this.logoY, this.logoWidth, this.logoHeight);
            ctx.globalAlpha = 1.0;
        }

        drawBricks(ctx) {
            for (const brick of this.bricks) {
                ctx.fillStyle = brick.color;
                ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
                if (brick.hits > 1) {
                    // Tijolo reforçado: moldura branca até levar o primeiro acerto
                    ctx.strokeStyle = "#FFFFFF";
                    ctx.lineWidth = 3;
                    ctx.strokeRect(brick.x + 2, brick.y + 2, brick.width - 4, brick.height - 4);
                    ctx.lineWidth = 1;
                }
            }
        }

        drawTrail(ctx) {
            const total = this.trail.length;
            ctx.fillStyle = cfg.colors.red;
            for (let i = 0; i < total; i++) {
                const fade = (i + 1) / total;
                ctx.globalAlpha = fade * 0.3;
                ctx.beginPath();
                ctx.arc(this.trail[i][0], this.trail[i][1], R * fade * 0.9, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.globalAlpha = 1;
        }

        drawBall(ctx) {
            ctx.beginPath();
            ctx.arc(this.ballPosition[0], this.ballPosition[1], R, 0, Math.PI * 2);
            ctx.fillStyle = cfg.colors.red;
            ctx.fill();
            ctx.closePath();
        }

        drawBar(ctx) {
            ctx.fillStyle = this.paddleFlash > 0 ? "#FFFFFF" : cfg.colors.blue;
            ctx.fillRect(this.barPosition[0], this.barPosition[1], BAR_W, BAR_H);
        }

        drawParticles(ctx) {
            for (const particle of this.particles) {
                ctx.globalAlpha = Math.max(0, particle.life / particle.maxLife);
                ctx.fillStyle = particle.color;
                ctx.fillRect(particle.x, particle.y, particle.size, particle.size);
            }
            ctx.globalAlpha = 1;
        }

        drawHud(ctx) {
            ctx.font = "20px Arial, sans-serif";
            ctx.textAlign = "left";
            ctx.fillStyle = cfg.colors.red;
            ctx.fillText(
                "Pontos: " + this.score + "   Vidas: " + this.lives +
                "   Nível: " + this.level + "/" + cfg.maxLevel,
                10, 30
            );
            ctx.textAlign = "right";
            ctx.fillStyle = "#AAAAAA";
            ctx.fillText("Recorde: " + this.highScore, W - 10, 30);
        }

        drawMessages(ctx) {
            if (this.gameState === "playing" && !this.ballStuckToBar) return;

            let title = "";
            let subtitle = "";
            let color = "#FFFFFF";

            if (this.gameState === "initial" || this.ballStuckToBar) {
                title = ACTION + " para jogar";
                subtitle = IS_TOUCH
                    ? "arraste o dedo para mover a barra"
                    : "mova o mouse para controlar a barra · P para pausar";
            } else if (this.gameState === "paused") {
                title = "Pausa";
                subtitle = "P para continuar";
            } else if (this.gameState === "levelComplete") {
                title = "Nível " + this.level + " concluído!";
                subtitle = ACTION + " para ir ao nível " + (this.level + 1);
                color = cfg.colors.green;
            } else if (this.gameState === "gameOver") {
                title = "Game Over!";
                subtitle = ACTION + " para recomeçar";
                color = cfg.colors.red;
            } else if (this.gameState === "victory") {
                title = "Vitória!";
                subtitle = "você zerou os " + cfg.maxLevel + " níveis · " + ACTION + " para recomeçar";
                color = cfg.colors.green;
            }

            // Escurece o fundo nas telas de interrupção, para o texto ficar legível.
            // A tela inicial fica de fora: é a mesma situação da bola presa à barra
            // durante a partida, e escurecer só ali criava um pisca ao primeiro clique.
            if (this.gameState !== "playing" && this.gameState !== "initial") {
                ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
                ctx.fillRect(0, 0, W, H);
            }

            ctx.textAlign = "center";
            ctx.font = "44px Arial Black, Arial, sans-serif";
            ctx.fillStyle = color;
            ctx.fillText(title, W / 2, H / 2 + 70);

            ctx.font = "20px Arial, sans-serif";
            ctx.fillStyle = "#DDDDDD";
            ctx.fillText(subtitle, W / 2, H / 2 + 110);

            if (this.newRecord && (this.gameState === "gameOver" || this.gameState === "victory")) {
                ctx.font = "24px Arial Black, Arial, sans-serif";
                ctx.fillStyle = cfg.colors.yellow;
                ctx.fillText("Novo recorde: " + this.highScore, W / 2, H / 2 + 150);
            }
        }
    }

    // O iframe do Streamlit tem altura fixa; com o canvas responsivo ela precisa
    // acompanhar a altura real do conteúdo, senão sobra faixa vazia no mobile.
    function fitFrame() {
        try {
            const frame = window.frameElement;
            if (!frame) return;
            const height = Math.ceil(document.getElementById("wrap").getBoundingClientRect().height) + 4;
            frame.style.height = height + "px";
            frame.height = height;
        } catch (e) { /* cross-origin: mantém a altura definida no Python */ }
    }

    window.addEventListener("DOMContentLoaded", () => {
        try {
            const canvas = document.getElementById("gameCanvas");
            if (!canvas) throw new Error("Canvas não encontrado");

            const sounds = new SoundBank(cfg.sounds);
            const game = new BreakoutGame(canvas, sounds);

            const muteBtn = document.getElementById("muteBtn");
            muteBtn.textContent = sounds.muted ? "🔇 Mudo" : "🔊 Som";
            muteBtn.setAttribute("aria-pressed", String(sounds.muted));
            muteBtn.addEventListener("click", () => game.onMuteToggle());

            canvas.focus();
            fitFrame();
            window.addEventListener("resize", fitFrame);
            new ResizeObserver(fitFrame).observe(canvas);

            // Superfície de inspeção usada pelos testes de ponta a ponta
            window.__breakout = { game: game, sounds: sounds, isTouch: IS_TOUCH };
        } catch (e) {
            console.error("Erro ao inicializar o jogo:", e);
        }
    });
})();
"""

breakout_html = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'><style>" + GAME_CSS + "</style></head>"
    "<body><div id='wrap'>"
    "<canvas id='gameCanvas' tabindex='0'></canvas>"
    "<div id='controls'>"
    "<button id='muteBtn' type='button' aria-label='Ativar ou desativar o som'>🔊 Som</button>"
    "</div>"
    "</div>"
    "<script>window.__BREAKOUT_CFG__ = " + json.dumps(GAME_CONFIG) + ";</script>"
    "<script>" + GAME_JS + "</script>"
    "</body></html>"
)

# Renderiza o jogo
components.html(breakout_html, height=WINDOW_HEIGHT + 60, scrolling=False)

st.markdown("""
<div style="text-align: center;">
    <h4>🎮Breakout Web Game: em Python, Streamlit e outros.</h4>
    💬 Por <strong>Ary Ribeiro</strong>: <a href="https://www.linkedin.com/in/aryribeiro" target="_blank">linkedin.com/in/aryribeiro</a><br><br>
    <em>No computador, use o mouse para controlar a barra (P pausa, M silencia).<br>
    No smartphone, arraste o dedo sobre a área do jogo.</em>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* O Streamlit reserva no container a altura declarada em components.html.
       Como o canvas é responsivo, o iframe se redimensiona sozinho e o container
       precisa acompanhá-lo, senão sobra uma faixa vazia embaixo do jogo.
       O container é item de um flex column: quem manda na altura é o
       flex-basis, não o height. */
    div[data-testid="stElementContainer"]:has(iframe[data-testid="stIFrame"]) {
        height: auto !important;
        flex-basis: auto !important;
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
