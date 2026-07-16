import time
import requests
import subprocess
from datetime import datetime

# ==========================================
# --- 手机端自动抢券配置参数 ---
# ==========================================

# 抢券时间点，格式为 "YYYY-MM-DD HH:MM:SS"
TARGET_TIME_STR = "2026-06-10 10:00:00"

# 领券按钮在你手机屏幕上的精确坐标 (X, Y)
# 获取方法：在手机设置中搜索“开发者选项”，开启“指针位置”，然后点击按钮，看屏幕顶部显示的 X 和 Y 坐标
TAP_X = 1014  # 替换为你的实际 X 坐标
TAP_Y = 1467 # 替换为你的实际 Y 坐标

# 提前抢券的微调值（毫秒）。因为 adb 命令发送到手机大概有 50-100 毫秒延迟，可以适当提前
ADVANCE_MS = 100 

# ADB 工具路径。如果你配置了环境变量，直接用 "adb"。否则填入 adb.exe 的绝对路径
ADB_PATH = r"D:\Antigravity\platform-tools\adb.exe"

# --- 自动刷新配置 ---
# 刷新方式支持:
# 'NONE'  - 不刷新（默认）
# 'SWIPE' - 下拉手势刷新（适用于大多数App活动页、小程序）
# 'TAP'   - 点击页面上的刷新按钮
REFRESH_TYPE = 'SWIPE'

# [下拉刷新 'SWIPE' 参数] 下拉手势坐标：(X1, Y1) 滑动到 (X2, Y2)，以及滑动持续时间（毫秒）
SWIPE_START_X = 540
SWIPE_START_Y = 600
SWIPE_END_X = 540
SWIPE_END_Y = 1400
SWIPE_DURATION_MS = 250

# [点击刷新 'TAP' 参数] 刷新按钮在屏幕上的坐标 (X, Y)
REFRESH_X = 900
REFRESH_Y = 150

# 提前刷新时间（毫秒）。因为页面刷新加载需要一定时间（例如页面请求、渲染等），
# 建议比抢券时间提前 500-1000 毫秒刷新，等刷新完成时，操作刚好卡在抢券点。
REFRESH_ADVANCE_MS = 800

# ==========================================

def get_server_time():
    """获取高精度服务器时间戳（采用淘宝通用时间接口，毫秒级，各电商大厂时间误差几乎为0）"""
    url = "http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp"
    try:
        start = time.perf_counter()
        res = requests.get(url, timeout=2)
        end = time.perf_counter()
        latency = (end - start) * 1000 / 2
        # 解析返回的毫秒级时间戳
        server_time = int(res.json()['data']['t'])
        return server_time + int(latency)
    except Exception:
        return int(time.time() * 1000)

def get_time_offset():
    """计算时间偏差"""
    print("正在同步高精度电商服务器时间（适用于唯品会/淘宝/京东）...")
    offsets = []
    for _ in range(5):
        server_ts = get_server_time()
        local_ts = int(time.time() * 1000)
        offsets.append(server_ts - local_ts)
        time.sleep(0.5)
    mean_offset = sum(offsets) / len(offsets)
    print(f"时间同步完成，本地时间比电商服务器慢 {mean_offset:.2f} 毫秒")
    return mean_offset

def check_adb_connection():
    """检查手机是否成功连接到电脑"""
    try:
        result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        # 第一行是 "List of devices attached"，如果有设备，会有第二行
        if len(lines) > 1 and "device" in lines[1]:
            print("✅ 成功检测到手机连接！")
            return True
        else:
            print("❌ 未检测到手机，请确认已开启 USB 调试并连接电脑。")
            return False
    except FileNotFoundError:
        print(f"❌ 找不到 ADB 工具。请确保安装了 adb，或在脚本中配置正确的 ADB_PATH。")
        return False

def fast_tap_via_adb(x, y, times=5):
    """
    通过 ADB 发送点击指令
    将多次点击合并为一条命令发送，减少通信延迟
    """
    commands = []
    for _ in range(times):
        commands.append(f"input tap {x} {y}")
    
    # 组合命令，例如: input tap 500 1000; input tap 500 1000
    combined_command = " ; ".join(commands)
    subprocess.Popen([ADB_PATH, "shell", combined_command])

def refresh_page():
    """执行页面刷新操作"""
    if REFRESH_TYPE == 'SWIPE':
        print("🌀 触发下拉刷新...")
        # 发送 swipe 指令模拟下拉刷新动作
        subprocess.Popen([ADB_PATH, "shell", f"input swipe {SWIPE_START_X} {SWIPE_START_Y} {SWIPE_END_X} {SWIPE_END_Y} {SWIPE_DURATION_MS}"])
    elif REFRESH_TYPE == 'TAP':
        print("🌀 触发点击刷新按钮...")
        # 发送 tap 指令点击特定的刷新按钮
        subprocess.Popen([ADB_PATH, "shell", f"input tap {REFRESH_X} {REFRESH_Y}"])

def run_mobile_rob():
    if not check_adb_connection():
        return

    target_dt = datetime.strptime(TARGET_TIME_STR, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_dt.timestamp() * 1000)
    
    time_offset = get_time_offset()
    
    print(f"🎯 目标抢券时间: {TARGET_TIME_STR}")
    print(f"🎯 预设点击坐标: X={TAP_X}, Y={TAP_Y}")
    if REFRESH_TYPE != 'NONE':
        print(f"🌀 已开启自动刷新，方式: {REFRESH_TYPE}，提前 {REFRESH_ADVANCE_MS}ms 刷新")
    print("⏳ 正在等待时机，请保持手机亮屏并停留在领券页面...")
    
    refreshed = False
    
    while True:
        current_jd_time = int(time.time() * 1000) + time_offset
        remaining = target_timestamp - current_jd_time
        
        # 1. 在提前量到达时触发刷新
        if REFRESH_TYPE != 'NONE' and not refreshed and remaining <= REFRESH_ADVANCE_MS:
            refresh_page()
            refreshed = True
            
        # 2. 到达抢券时间点，开始疯狂连点
        if remaining <= ADVANCE_MS:
            print(f"🚀 时间已到！开始对手机发送疯狂点击指令！(偏差值: {remaining}ms)")
            break
            
        # 动态控制 sleep 精度
        if remaining > 2000:
            time.sleep(0.1)
        elif remaining > 500:
            time.sleep(0.01)
        else:
            time.sleep(0.002) # 临近抢券时间高频轮询
            
    # 发送几轮连点指令
    for _ in range(3):
        fast_tap_via_adb(TAP_X, TAP_Y, times=5)
        time.sleep(0.1) # 稍微停顿，防止手机卡死
        
    print("✅ 抢券点击指令已发送完毕，请看手机屏幕是否领到！")

if __name__ == "__main__":
    run_mobile_rob()
