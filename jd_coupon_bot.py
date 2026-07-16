import time
import requests
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# --- 配置参数 ---
# 京东领券页面的 URL
COUPON_URL = "https://coupon.jd.com/xxxxxx.html"  # 替换为你要抢的优惠券页面链接
# 抢券时间点，格式为 "YYYY-MM-DD HH:MM:SS"
TARGET_TIME_STR = "2026-06-08 22:00:00"
# 本地与京东服务器的时间差（毫秒），提前抢券的微调值（如提前50毫秒发送点击）
ADVANCE_MS = 50 
# Chrome 调试端口（用于接管已登录的浏览器，避开复杂的扫码登录和大部分滑块风控）
# 启动 Chrome 的命令：chrome.exe --remote-debugging-port=9222
CHROME_DEBUG_PORT = 9222

def get_jd_time():
    """
    获取京东服务器的当前时间戳（毫秒）
    """
    url = "https://api.m.jd.com/client.action?functionId=queryMaterialProducts"
    try:
        start = time.perf_counter()
        res = requests.get(url, timeout=2)
        end = time.perf_counter()
        # 考虑网络延迟，估算服务器时间
        latency = (end - start) * 1000 / 2
        server_time = int(res.headers.get("Date-convert-timestamp", time.time() * 1000))
        return server_time + int(latency)
    except Exception:
        # 如果获取失败，降级使用本地时间
        return int(time.time() * 1000)

def get_time_offset():
    """
    计算本地时间与京东服务器时间的差值 (京东时间 - 本地时间)
    """
    print("正在同步京东服务器时间...")
    offsets = []
    for _ in range(5):
        jd_ts = get_jd_time()
        local_ts = int(time.time() * 1000)
        offsets.append(jd_ts - local_ts)
        time.sleep(0.5)
    # 取平均值作为最终的偏移量
    mean_offset = sum(offsets) / len(offsets)
    print(f"时间同步完成，本地时间比京东服务器慢 {mean_offset:.2f} 毫秒")
    return mean_offset

async def run_rob():
    # 转换目标时间为时间戳
    target_dt = datetime.strptime(TARGET_TIME_STR, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_dt.timestamp() * 1000)
    
    # 同步服务器时间差
    time_offset = get_time_offset()
    
    async with async_playwright() as p:
        print(f"正在连接到本地 Chrome 调试端口 {CHROME_DEBUG_PORT}...")
        try:
            # 接管本地 Chrome，共享登录状态
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{CHROME_DEBUG_PORT}")
        except Exception as e:
            print(f"连接 Chrome 失败！请确保你已经关闭所有 Chrome，并使用命令行启动了调试模式：")
            print(f'chrome.exe --remote-debugging-port={CHROME_DEBUG_PORT}')
            print(f"错误详情: {e}")
            return
        
        # 获取当前打开的页面，或者新建一个
        context = browser.contexts[0]
        page = await context.new_page()
        
        print(f"正在打开领券页面: {COUPON_URL}")
        await page.goto(COUPON_URL)
        
        # --- 定位领券按钮的 CSS Selector ---
        # 注意：不同领券页面的 HTML 结构可能不同，需要根据实际页面修改 selector
        # 京东常见的领券按钮 selector 可能是 ".btn-coupon", "text=立即领取", "div.coupon-btn" 等
        button_selector = "text=立即领取" 
        
        print("等待领券按钮加载...")
        try:
            await page.wait_for_selector(button_selector, timeout=10000)
            btn = page.locator(button_selector)
            print("领券按钮已找到，准备抢券！")
        except Exception:
            print(f"未找到指定的按钮 '{button_selector}'，请检查领券页面元素！")
            await browser.close()
            return

        print(f"目标抢券时间: {TARGET_TIME_STR}")
        print("正在等待时机，进入毫秒级倒计时...")
        
        while True:
            # 获取当前京东服务器时间
            current_jd_time = int(time.time() * 1000) + time_offset
            remaining = target_timestamp - current_jd_time
            
            if remaining <= 1000:
                # 剩余时间小于 1 秒时，进入高频轮询
                if remaining <= ADVANCE_MS:
                    print(f"时间已到！开始抢券！(偏差值: {remaining}ms)")
                    break
            else:
                # 剩余时间较长，sleep 以节省 CPU
                await asyncio.sleep(0.1)
                
        # --- 触发多轮快速点击 ---
        # 为了防止单次点击失效或网络抖动，通常在极短时间内连续点击多次
        tasks = []
        for i in range(10):  # 连续点击 10 次
            # click() 方法默认会等待元素可交互，但在秒杀时，我们需要强制快速触发
            tasks.append(btn.click(force=True, timeout=1000))
            # 每次点击间隔 20 毫秒
            await asyncio.sleep(0.02)
            
        # 等待所有点击任务执行完毕
        await asyncio.gather(*tasks, return_exceptions=True)
        print("抢券指令发送完毕，请在浏览器中查看是否领券成功！")
        
        # 保持页面打开一段时间供确认结果
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_rob())
