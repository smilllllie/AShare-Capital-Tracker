const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const highScoreElement = document.getElementById('high-score');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over');
const startBtn = document.getElementById('start-btn');
const restartBtn = document.getElementById('restart-btn');

// --- 游戏核心配置 ---
const gridSize = 20; // 网格大小
const tileCount = canvas.width / gridSize; // 每行/列的格子数
let snake = [];
let dx = 0; // x轴速度
let dy = 0; // y轴速度
let foodX;
let foodY;
let score = 0;
let highScore = localStorage.getItem('neonSnakeHighScore') || 0;
let gameSpeed = 120; // 初始速度，数值越小越快
let isPlaying = false;
let gameLoopId;

// 初始化最高分显示
highScoreElement.textContent = highScore;

// --- 视觉色彩配置 ---
const snakeHeadColor = '#66fcf1'; // 青色
const snakeBodyColor = 'rgba(102, 252, 241, 0.8)';
const foodColor = '#ff0055'; // 粉红色
const gridColor = 'rgba(255, 255, 255, 0.05)';

// 重置游戏状态
function resetGame() {
    // 初始蛇的长度为3
    snake = [
        { x: Math.floor(tileCount / 2), y: Math.floor(tileCount / 2) },
        { x: Math.floor(tileCount / 2), y: Math.floor(tileCount / 2) + 1 },
        { x: Math.floor(tileCount / 2), y: Math.floor(tileCount / 2) + 2 }
    ];
    dx = 0;
    dy = -1; // 默认向上移动
    score = 0;
    gameSpeed = 130; // 重置速度
    scoreElement.textContent = score;
    placeFood();
}

// 绘制网格背景
function drawGrid() {
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let i = 0; i <= canvas.width; i += gridSize) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(canvas.width, i);
        ctx.stroke();
    }
}

// 绘制贪吃蛇
function drawSnake() {
    snake.forEach((segment, index) => {
        if (index === 0) {
            // 蛇头：添加发光效果
            ctx.shadowBlur = 15;
            ctx.shadowColor = snakeHeadColor;
            ctx.fillStyle = snakeHeadColor;
        } else {
            // 蛇身
            ctx.shadowBlur = 0;
            ctx.fillStyle = snakeBodyColor;
        }

        // 使用圆角矩形绘制，让蛇看起来更圆润现代
        ctx.beginPath();
        ctx.roundRect(
            segment.x * gridSize + 1, 
            segment.y * gridSize + 1, 
            gridSize - 2, 
            gridSize - 2, 
            4
        );
        ctx.fill();
        ctx.shadowBlur = 0; // 重置阴影避免影响其他绘制
    });
}

// 绘制食物
function drawFood() {
    ctx.shadowBlur = 20;
    ctx.shadowColor = foodColor;
    ctx.fillStyle = foodColor;
    
    // 画一个圆形的食物
    ctx.beginPath();
    ctx.arc(
        foodX * gridSize + gridSize / 2, 
        foodY * gridSize + gridSize / 2, 
        gridSize / 2 - 2, 
        0, 
        Math.PI * 2
    );
    ctx.fill();
    ctx.shadowBlur = 0;
}

// 随机生成食物位置
function placeFood() {
    let newX, newY;
    let onSnake;
    // 确保食物不会生成在蛇的身体上
    do {
        newX = Math.floor(Math.random() * tileCount);
        newY = Math.floor(Math.random() * tileCount);
        onSnake = snake.some(segment => segment.x === newX && segment.y === newY);
    } while (onSnake);
    foodX = newX;
    foodY = newY;
}

// 移动逻辑
function moveSnake() {
    // 计算新的蛇头位置
    const head = { x: snake[0].x + dx, y: snake[0].y + dy };
    snake.unshift(head); // 将新头部加入数组最前面

    // 吃到食物
    if (head.x === foodX && head.y === foodY) {
        score += 10;
        scoreElement.textContent = score;
        
        // 更新最高分
        if (score > highScore) {
            highScore = score;
            highScoreElement.textContent = highScore;
            localStorage.setItem('neonSnakeHighScore', highScore);
        }
        
        placeFood();
        
        // 游戏加速，增加难度 (下限为 50ms)
        if (gameSpeed > 50) gameSpeed -= 3;
    } else {
        // 没吃到食物，移除尾部，保持长度
        snake.pop();
    }
}

// 碰撞检测
function checkCollision() {
    const head = snake[0];

    // 撞墙检测
    if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
        return true;
    }

    // 撞自己检测 (跳过头部，从 i=1 开始)
    for (let i = 1; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            return true;
        }
    }

    return false;
}

// 主游戏循环
function update() {
    if (!isPlaying) return;

    if (checkCollision()) {
        gameOver();
        return;
    }

    // 清屏
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制游戏元素
    drawGrid();
    drawFood();
    moveSnake();
    drawSnake();

    // 控制帧率（游戏速度）
    gameLoopId = setTimeout(() => {
        requestAnimationFrame(update);
    }, gameSpeed);
}

// 游戏状态控制
function startGame() {
    startScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    clearTimeout(gameLoopId);
    resetGame();
    isPlaying = true;
    update();
}

function gameOver() {
    isPlaying = false;
    gameOverScreen.classList.remove('hidden');
}

// --- 键盘事件监听 ---
let lastInputTime = 0;
document.addEventListener('keydown', (e) => {
    // 防抖：防止快速按键导致蛇在原地调头咬死自己
    const currentTime = Date.now();
    if (currentTime - lastInputTime < 40) return;
    lastInputTime = currentTime;

    switch (e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
            if (dy !== 1) { dx = 0; dy = -1; }
            break;
        case 'ArrowDown':
        case 's':
        case 'S':
            if (dy !== -1) { dx = 0; dy = 1; }
            break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
            if (dx !== 1) { dx = -1; dy = 0; }
            break;
        case 'ArrowRight':
        case 'd':
        case 'D':
            if (dx !== -1) { dx = 1; dy = 0; }
            break;
    }
});

// 绑定按钮事件
startBtn.addEventListener('click', startGame);
restartBtn.addEventListener('click', startGame);

// 初始化画面
drawGrid();
