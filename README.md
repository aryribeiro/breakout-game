Obs.: caso o app esteja no modo "sleeping" (dormindo) ao entrar, basta clicar no botão que estará disponível e aguardar, para ativar o mesmo. 
![print breakout producao](https://github.com/user-attachments/assets/9ffa430c-900c-490e-a60f-a3761b462135)

## 🎮 Breakout Web Game

Este projeto é um jogo clássico Breakout implementado utilizando Python, Streamlit, e JavaScript. O jogo é uma adaptação do famoso jogo de arcade, onde o objetivo é destruir todos os tijolos utilizando uma bola que se rebate nas paredes e em uma barra controlada pelo jogador. O jogo é simples, mas divertido, com sons e animações baseados no navegador.

## Como Jogar

São **5 níveis**. A cada nível a bola fica mais rápida e as fileiras de cima passam a exigir dois acertos (elas aparecem com uma moldura branca até levarem o primeiro golpe). A bola também acelera aos poucos enquanto você mantém o rally, então segurar a barra parada no meio não funciona por muito tempo. Você começa com 3 vidas e o recorde fica salvo no navegador.

- **Computador**: mova o mouse para controlar a barra e clique (ou aperte Espaço) para lançar a bola. `P` ou `Esc` pausa, `M` liga e desliga o som.
- **Smartphone**: toque na área do jogo para lançar a bola e arraste o dedo para mover a barra.

O botão de som fica logo abaixo da área do jogo, e a preferência de mudo é lembrada entre as sessões.

## Tecnologias Utilizadas

- **Python**: Linguagem de programação principal para o backend e geração do app com Streamlit.
- **Streamlit**: Framework Python utilizado para criação de aplicativos web interativos.
- **JavaScript**: Utilizado para a implementação do jogo e interação com a interface.
- **HTML5 Canvas**: Utilizado para renderizar o jogo na tela.

Os efeitos sonoros e a logo ficam na pasta `som/` e são embutidos diretamente no jogo, sem depender de servidores externos.

## Como Rodar o Projeto

1. Clone o repositório:
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <DIRETORIO_DO_PROJETO>
    ```

2. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

3. Execute o aplicativo:
    ```bash
    streamlit run game.py
    ```

4. Acesse o jogo via navegador. Funciona tanto no computador quanto no smartphone: a área do jogo se ajusta à largura da tela.

## Contato

Caso tenha alguma dúvida ou queira entrar em contato, mande um email para: [aryribeiro@gmail.com](mailto:aryribeiro@gmail.com).
