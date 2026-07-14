import os
import json
import base64
import datetime
import asyncio
from playwright.async_api import async_playwright
import requests

PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '') 

async def capture_final_board():
    html_path = f"file:///{os.path.abspath('concept_race_board.html').replace(chr(92), '/')}"
    screenshot_path = 'latest_board.png'
    
    print("启动浏览器内核，渲染概念赛跑最终榜单...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 600, "height": 800}, device_scale_factor=2)
        await page.goto(html_path)
        
        await page.wait_for_timeout(1000)
        
        await page.evaluate("""
            const slider = document.getElementById('timeSlider');
            if (slider && window.HISTORY_DATA) {
                slider.value = window.HISTORY_DATA.length - 1;
                slider.dispatchEvent(new Event('input'));
            }
        """)
        
        await page.wait_for_timeout(1500)
        
        container = await page.query_selector('.container')
        if container:
            await container.screenshot(path=screenshot_path, type="jpeg", quality=60)
        else:
            await page.screenshot(path=screenshot_path, type="jpeg", quality=60)
            
        await browser.close()
        print(f"成功保存最终榜单截图: {screenshot_path}")
        return screenshot_path

def push_to_wechat(screenshot_path):
    if not PUSHPLUS_TOKEN:
        print("未检测到 PUSHPLUS_TOKEN，跳过推送！")
        return

    history_file = 'concept_history.json'
    last_frame = None
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                if history_data:
                    last_frame = history_data[-1]
        except Exception as e:
            print("读取 JSON 失败:", e)
            
    summary_text = ""
    if last_frame:
        time_str = last_frame['time']
        top5 = sorted(last_frame['data'], key=lambda x: x['value'], reverse=True)[:5]
        
        summary_text += f"<h3 style='color: #d84a38;'>📈 核心概念净流入排行榜 ({time_str})</h3>"
        summary_text += "<hr>"
        
        for i, item in enumerate(top5):
            sign = '+' if item['value'] > 0 else ''
            color = 'red' if item['value'] > 0 else 'green'
            summary_text += f"<p>{i+1}. <b>{item['name']}</b> : <span style='color:{color}'>{sign}{item['value']} 亿</span></p>"

    img_html = ""
    if os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode()
            img_html = f'<div style="text-align:center; margin-top:20px;"><img src="data:image/jpeg;base64,{b64_str}" style="max-width:100%; border-radius:10px;"></div>'

    html_content = f"""
    <div style="font-family: sans-serif; background-color: #f7f9f9; padding: 15px; border-radius: 8px;">
        {summary_text}
        {img_html}
        <br>
        <p style="font-size: 12px; color: #888; text-align: center;">💡 观看全天动态赛跑回放，<br>请在本地打开 concept_race_board.html</p>
    </div>
    """

    date_str = datetime.datetime.now().strftime("%m-%d")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": f"【资金净流向】{date_str} 核心概念榜单",
        "content": html_content,
        "template": "html"
    }
    
    print("正在推送到微信...")
    try:
        resp = requests.post(url, json=data, timeout=10)
        res_json = resp.json()
        if res_json.get("code") == 200:
            print("✅ 微信推送成功！")
        else:
            print("❌ 推送失败:", res_json)
    except Exception as e:
        print("推送请求异常:", e)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    img_path = asyncio.run(capture_final_board())
    push_to_wechat(img_path)
