import json
import random

# 新的 18 个概念
names = [
    "PCB概念", "创新药", "共封装光学(CPO)", "商业航天", 
    "存储芯片", "人形机器人", "光纤概念", "先进封装", 
    "算力租赁", "消费电子", "车路云", "低空经济", 
    "AI大模型", "半导体设备", "黄金概念", "CRO概念", 
    "液冷服务器", "AI应用"
]

# 给每个板块赋予一个初始的动量趋势（单位：亿元）
trends = {n: random.uniform(-1.0, 1.0) for n in names}
# 初始资金量为 0
vals = {n: 0.0 for n in names}
history = []

for h in range(9, 16):
    for m in range(0, 60):
        if (h == 9 and m < 30): continue
        if (h == 11 and m > 30): continue
        if (h == 12): continue
        if (h == 15 and m > 0): continue
        
        time_str = f"{h:02d}:{m:02d}"
        
        frame_data = []
        for n in names:
            # 趋势有 10% 概率反转或加速
            if random.random() < 0.1:
                trends[n] += random.uniform(-2.0, 2.0)
            
            # 添加随机波动，资金博弈非常剧烈，一分钟可能波动 1-5 亿
            change = trends[n] + random.uniform(-1.5, 1.5)
            vals[n] += change
            
            frame_data.append({
                "name": n,
                "value": round(vals[n], 2)
            })
            
        # 按照资金净额排序，取前 12 名
        frame_data.sort(key=lambda x: x['value'], reverse=True)
        
        history.append({
            "time": time_str,
            "data": frame_data[:12]
        })

with open('concept_history.js', 'w', encoding='utf-8') as f:
    f.write("window.HISTORY_DATA = " + json.dumps(history, ensure_ascii=False) + ";\n")
    
print("已成功生成绝对资金量(亿元)的 240 帧虚拟数据！")
