import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import json
import base64
import asyncio
import datetime
import requests
import akshare as ak
from playwright.async_api import async_playwright

# ==========================================
# 用户配置区
# ==========================================
# 你的 PushPlus Token (微信接收)
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "a6314ea7fa9246f7a4710b521d7634fb")

def get_capital_flow_data():
    """使用 akshare 获取 A 股资金流向数据"""
    print("正在拉取 A 股板块资金流向数据...")
    df = ak.stock_fund_flow_industry(symbol='即时')
    
    target_col = '净额'
    
    def parse_value(val):
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '').replace('万', '').replace('亿', '')
        try:
            return float(val_str)
        except:
            return 0.0

    df['parsed_val'] = df[target_col].apply(parse_value)
    
    # 将单位统一为亿
    if df['parsed_val'].abs().max() > 100000:
        df['parsed_val'] = df['parsed_val'] / 100000000

    df_sorted = df.sort_values(by='parsed_val', ascending=False)
    
    inflow_df = df_sorted.head(10)
    outflow_df = df_sorted.tail(10).sort_values(by='parsed_val', ascending=True)
    
    def format_items(sub_df, is_inflow):
        result = []
        for rank, (_, row) in enumerate(sub_df.iterrows(), 1):
            val = row['parsed_val']
            display_val = abs(val) 
            sign = '+' if is_inflow else ''
            formatted_text = f"{sign}{val:.1f}亿" if is_inflow else f"{val:.1f}亿"
            if not is_inflow and val > 0: formatted_text = f"-{val:.1f}亿"
            
            result.append({
                'rank': rank,
                'name': row['行业'],
                'value': display_val,
                'text': formatted_text
            })
        return result

    inflow_data = format_items(inflow_df, True)
    outflow_data = format_items(outflow_df, False)
    
    try:
        sh_df = ak.stock_zh_a_spot_em()
        sh_index = sh_df[sh_df['代码'] == '000001']['最新价'].values[0]
    except Exception as e:
        print("拉取上证指数失败", e)
        sh_index = "----.--"

    today_str = datetime.datetime.now().strftime('%m月%d日')
    
    return {
        'date': today_str,
        'index': str(sh_index),
        'inflow': inflow_data,
        'outflow': outflow_data
    }

async def generate_screenshot():
    """将数据注入 HTML 模板并使用 Playwright 截图"""
    data = get_capital_flow_data()
    data_json = json.dumps(data, ensure_ascii=False)
    
    # 读取模板
    with open('capital_flow_template.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    import re
    html_content = re.sub(r'window\.CAPITAL_DATA\s*=\s*\{.*?\};', f'window.CAPITAL_DATA = {data_json};', html_content, flags=re.DOTALL)
    
    render_path = os.path.abspath('capital_flow_render.html')
    with open(render_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("正在启动无头浏览器截图...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 480, "height": 1200})
        await page.goto(f"file:///{render_path}")
        
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
        
    print(f"✅ 截图成功：{img_path}")
    return img_path

def upload_image_to_telegraph(image_path):
    """将图片上传到免费图床以便推送"""
    print("正在上传截图到图床...")
    try:
        with open(image_path, 'rb') as f:
            url = 'https://freeimage.host/api/1/upload'
            data = {'key': '6d207e02198a847aa98d0a2a901485a5', 'action': 'upload'}
            files = {'source': f}
            res = requests.post(url, data=data, files=files, timeout=15)
            if res.status_code == 200:
                img_url = res.json()['image']['url']
                print(f"✅ 图床上传成功: {img_url}")
                return img_url
            else:
                print(f"❌ 图床上传失败，状态码: {res.status_code}, 内容: {res.text}")
    except Exception as e:
        print("❌ 图床上传失败:", e)
    return None

def push_to_mobile(image_path):
    """将带有截图的 HTML 推送到 PushPlus"""
    if not PUSHPLUS_TOKEN or PUSHPLUS_TOKEN == "请在这里填入你的Token":
        print("未配置 PUSHPLUS_TOKEN，跳过推送环节。")
        return

    # 先上传到图床获取直链
    img_url = upload_image_to_telegraph(image_path)
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    title = f"📈 {date_str} 热点资金流向榜"
    
    if img_url:
        html_content = f"""
        <div style="text-align:center;">
            <h3>今日 A股热点资金榜</h3>
            <img src="{img_url}" alt="资金流向图" style="max-width:100%; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.5);">
            <p style="color:#888; font-size:12px;">自动生成</p>
        </div>
        """
    else:
        # 如果图床失败，尝试使用 Base64 (PushPlus 可能由于字符超长被截断)
        with open(image_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode()
        html_content = f'<img src="data:image/png;base64,{b64_str}" style="max-width:100%;">'

    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": html_content,
        "template": "html"
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print("✅ 微信推送成功！")
            else:
                print(f"❌ 微信推送失败，PushPlus返回错误: {result}")
        else:
            print(f"❌ 微信推送网络错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求 PushPlus 失败: {e}")

if __name__ == '__main__':
    print("="*40)
    print("开始生成资金榜单...")
    img_path = asyncio.run(generate_screenshot())
    push_to_mobile(img_path)
    print("="*40)
