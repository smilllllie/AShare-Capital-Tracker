# 资金流向榜单实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建一个高度可视化的 A 股资金流向追踪板，具有发光特效和真实的长度计算同步，并通过 Python 每天截取高清图推送到手机端。

**架构：**
前端基于原生 HTML/CSS/JS 实现动态排行榜，利用全局变量 `window.CAPITAL_DATA` 接收真实数据并按最大值动态渲染进度条百分比。后端 Python 利用 `akshare` 拉取资金流向，格式化注入 HTML 模板，并通过 `playwright` 自动截取图片发送到手机。

**技术栈：** HTML5, CSS3, JavaScript, Python 3, akshare, pandas, playwright, requests

---

### 任务 1：创建视觉展现层（基础结构与样式）

**文件：**
- 创建：`capital_flow_template.html`

- [ ] **步骤 1：编写基础 HTML 和 CSS 骨架**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>热点资金榜</title>
    <style>
        body {
            background-color: #0b0c10;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 480px;
            background: rgba(20, 20, 25, 0.8);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .header h1 {
            font-size: 20px;
            margin: 0;
            letter-spacing: 1px;
        }
        .section-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid;
        }
        .title-outflow { border-color: #00ff88; color: #00ff88; text-shadow: 0 0 8px rgba(0,255,136,0.4); }
        .title-inflow { border-color: #ff3333; color: #ff3333; text-shadow: 0 0 8px rgba(255,51,51,0.4); }
        
        .list-container { margin-bottom: 30px; }
        
        .item {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            position: relative;
        }
        .item-rank {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
            z-index: 2;
        }
        .rank-outflow { background: #00ff88; color: #000; box-shadow: 0 0 8px #00ff88; }
        .rank-inflow { background: #ff3333; color: #fff; box-shadow: 0 0 8px #ff3333; }
        
        .item-name {
            width: 80px;
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            z-index: 2;
        }
        .item-bar-bg {
            flex: 1;
            height: 16px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin: 0 10px;
            overflow: hidden;
            position: relative;
        }
        .item-bar-fill {
            height: 100%;
            width: 0%; /* Initial state for animation */
            border-radius: 8px;
            transition: width 1.2s cubic-bezier(0.1, 0.8, 0.2, 1);
        }
        .fill-outflow { background: linear-gradient(90deg, transparent, #00ff88); box-shadow: 0 0 10px rgba(0,255,136,0.6); }
        .fill-inflow { background: linear-gradient(90deg, transparent, #ff3333); box-shadow: 0 0 10px rgba(255,51,51,0.6); }
        
        .item-value {
            width: 70px;
            text-align: right;
            font-size: 14px;
            font-weight: bold;
            z-index: 2;
        }
        .val-outflow { color: #00ff88; }
        .val-inflow { color: #ff3333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div><span id="dateStr" style="font-size: 18px; font-weight: bold;">--月--日</span> <span style="background: #ff3333; font-size: 10px; padding: 2px 6px; border-radius: 4px; margin-left:5px;">收盘</span></div>
            <h1>热点资金榜</h1>
            <div style="text-align: right;">
                <div style="font-size: 10px; color: #888;">上证指数</div>
                <div id="indexVal" style="font-size: 16px; font-weight: bold;">----.--</div>
            </div>
        </div>
        
        <div class="list-container">
            <div class="section-title title-outflow">净流出</div>
            <div id="outflow-list"></div>
        </div>
        
        <div class="list-container">
            <div class="section-title title-inflow">净流入</div>
            <div id="inflow-list"></div>
        </div>
    </div>
    
    <script>
        // Placeholder test data
        window.CAPITAL_DATA = {
            date: '07月14日',
            index: '2900.00',
            inflow: [
                { rank: 1, name: '商业航天', value: 73.6, text: '+73.6亿' },
                { rank: 2, name: '军工', value: 62.3, text: '+62.3亿' }
            ],
            outflow: [
                { rank: 1, name: '半导体', value: 165.2, text: '-165.2亿' },
                { rank: 2, name: '国产芯片', value: 146.8, text: '-146.8亿' }
            ]
        };
    </script>
</body>
</html>
```

---

### 任务 2：创建渲染逻辑（JavaScript）

**文件：**
- 修改：`capital_flow_template.html`

- [ ] **步骤 1：添加动态渲染和百分比计算 JS**
在 HTML `</body>` 标签前添加渲染逻辑。

```html
<script>
    function renderBoard() {
        const data = window.CAPITAL_DATA || { inflow: [], outflow: [] };
        
        document.getElementById('dateStr').textContent = data.date || '未知日期';
        document.getElementById('indexVal').textContent = data.index || '----.--';
        
        // Find max absolute value to sync proportion
        let maxVal = 0;
        [...data.inflow, ...data.outflow].forEach(item => {
            if (item.value > maxVal) maxVal = item.value;
        });
        if (maxVal === 0) maxVal = 1; // Prevent divide by zero

        const renderList = (listId, items, type) => {
            const container = document.getElementById(listId);
            container.innerHTML = '';
            
            items.forEach((item, index) => {
                const widthPercent = (item.value / maxVal) * 100;
                
                const div = document.createElement('div');
                div.className = 'item';
                div.innerHTML = `
                    <div class="item-rank rank-${type}">${item.rank}</div>
                    <div class="item-name">${item.name}</div>
                    <div class="item-bar-bg">
                        <div class="item-bar-fill fill-${type}" style="width: 0%;" data-target="${widthPercent}%"></div>
                    </div>
                    <div class="item-value val-${type}">${item.text}</div>
                `;
                container.appendChild(div);
            });
        };

        renderList('outflow-list', data.outflow, 'outflow');
        renderList('inflow-list', data.inflow, 'inflow');

        // Trigger animation
        setTimeout(() => {
            document.querySelectorAll('.item-bar-fill').forEach(bar => {
                bar.style.width = bar.getAttribute('data-target');
            });
        }, 100);
    }
    
    // Execute on load
    window.onload = renderBoard;
</script>
```

---

### 任务 3：编写后端数据拉取（Python）

**文件：**
- 创建：`generate_board.py`

- [ ] **步骤 1：编写数据拉取核心逻辑**

```python
import json
import datetime
from decimal import Decimal
import akshare as ak

def get_capital_flow_data():
    # 获取今日行业资金流向
    df = ak.stock_sector_fund_flow_rank()
    
    # "今日主力净流入-净额" 列包含数值和单位，或者纯数值。通常 akshare 返回格式如 "12.34亿" 或浮点数
    # 为了鲁棒性，我们需要清洗列数据（确保转化为float）。
    # 假设 '今日主力净流入-净额' 列存在且可能需要处理单位。
    target_col = '今日主力净流入-净额'
    
    def parse_value(val):
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '').replace('万', '').replace('亿', '')
        try:
            return float(val_str)
        except:
            return 0.0

    df['parsed_val'] = df[target_col].apply(parse_value)
    
    # 如果原始单位是元，需转化为亿
    if df['parsed_val'].abs().max() > 100000:
        df['parsed_val'] = df['parsed_val'] / 100000000

    # 排序
    df_sorted = df.sort_values(by='parsed_val', ascending=False)
    
    inflow_df = df_sorted.head(10)
    outflow_df = df_sorted.tail(10).sort_values(by='parsed_val', ascending=True)
    
    def format_items(sub_df, is_inflow):
        result = []
        for rank, (_, row) in enumerate(sub_df.iterrows(), 1):
            val = row['parsed_val']
            # 流出取绝对值展示进度条长度
            display_val = abs(val) 
            sign = '+' if is_inflow else ''
            # 如果流出本身带有负号，则 val 已经是负数，直接使用；否则格式化
            formatted_text = f"{sign}{val:.1f}亿" if is_inflow else f"{val:.1f}亿"
            if not is_inflow and val > 0: formatted_text = f"-{val:.1f}亿"
            
            result.append({
                'rank': rank,
                'name': row['名称'],
                'value': display_val,
                'text': formatted_text
            })
        return result

    inflow_data = format_items(inflow_df, True)
    outflow_data = format_items(outflow_df, False)
    
    # 大盘指数（上证）
    try:
        sh_df = ak.stock_zh_a_spot_em()
        sh_index = sh_df[sh_df['代码'] == '000001']['最新价'].values[0]
    except:
        sh_index = "----.--"

    today_str = datetime.datetime.now().strftime('%m月%d日')
    
    return {
        'date': today_str,
        'index': str(sh_index),
        'inflow': inflow_data,
        'outflow': outflow_data
    }
```

---

### 任务 4：模版渲染与无头浏览器截图

**文件：**
- 修改：`generate_board.py`

- [ ] **步骤 1：加入 playwright 截图逻辑**

```python
import os
import asyncio
from playwright.async_api import async_playwright

async def generate_screenshot():
    data = get_capital_flow_data()
    data_json = json.dumps(data, ensure_ascii=False)
    
    # 读取模板
    with open('capital_flow_template.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # 替换预设的测试 JSON 变量
    # 注意：我们用字符串替换的方式注入
    replace_target = "window.CAPITAL_DATA = {"
    html_content = html_content.split(replace_target)[0] + f"window.CAPITAL_DATA = {data_json};\n    </script>\n</body>\n</html>"
    
    render_path = os.path.abspath('capital_flow_render.html')
    with open(render_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 480, "height": 1200})
        await page.goto(f"file://{render_path}")
        
        # 等待动画完成
        await page.wait_for_timeout(1500)
        
        # 获取核心容器的高度进行精准截图
        clip = await page.evaluate('''() => {
            const el = document.querySelector('.container');
            const rect = el.getBoundingClientRect();
            return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        }''')
        
        img_path = os.path.abspath('board_screenshot.png')
        await page.screenshot(path=img_path, clip=clip)
        await browser.close()
        
    return img_path

# 简单测试代码
# if __name__ == '__main__':
#     asyncio.run(generate_screenshot())
```

---

### 任务 5：与现有的推送体系集成

**文件：**
- 修改：`generate_board.py`

- [ ] **步骤 1：主入口与发送逻辑集成**

```python
import requests

def push_to_mobile(image_path):
    # 这里我们预留使用类似 server酱/PushPlus 的接口
    # 也可以复用目录下的 daily_news_pusher 的推送配置
    # 注意：很多推送服务发图需要先传图床或者直接通过企微机器人 webhook 发图
    print(f"准备推送图片: {image_path}")
    # 占位：实际发送逻辑将在实现时根据 user_token 编写
    # 示例 (企业微信 webhook 传文件):
    # ...
    
if __name__ == '__main__':
    print("开始获取资金流向数据并生成可视化...")
    img_path = asyncio.run(generate_screenshot())
    print(f"截图生成完毕: {img_path}")
    push_to_mobile(img_path)
    print("推送完成。")
```
