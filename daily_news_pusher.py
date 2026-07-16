import json
import time
import requests
import akshare as ak
from openai import OpenAI
from datetime import datetime
import hashlib
import os
import argparse

# ==========================================
# 用户配置区
# ==========================================

# 1. 填入你的 DeepSeek API Key 
# 安全提醒：上传 GitHub 前，强烈建议将下面后半部分的真实秘钥删除，仅保留 os.getenv("DEEPSEEK_API_KEY") 即可。
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 2. 填入你的 PushPlus Token (微信接收)
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")

# 3. 你的特别关注领域
FOCUS_AREA = "科技板块，首要关注AI整条产业链上的软硬件发展、算力、铜缆等。也关注A股和美股的相关重大利好或利空。"

# 4. 你的重点自选股（盘中突发时会着重监控）
MY_STOCKS = "立讯精密/歌尔股份/上工申贝/山子高科/永辉超市/章源钨业/天赐材料/沃尔核材/京东方A"

# ==========================================

def fetch_data_by_mode(mode, limit=150):
    """根据模式多维抓取数据"""
    print(f"正在启动 [{mode}] 模式的数据抓取...")
    news_list = []
    
    if mode == "morning":
        # 早盘：宏观、隔夜、三大报、公司公告
        try:
            df_sina = ak.stock_info_global_sina()
            df_sina.columns = ["time", "content"]
            count = 0
            for _, row in df_sina.head(limit).iterrows():
                news_list.append({"source": "Sina", "time": str(row['time']), "content": str(row['content'])})
                count += 1
            print(f"✅ 早盘获取 [新浪宏观与公告快讯] {count} 条。")
        except Exception as e:
            print(f"❌ 新浪接口抓取失败: {e}")
            
        try:
            df_futu = ak.stock_info_global_futu()
            count = 0
            for _, row in df_futu.head(limit).iterrows():
                title = row.get('标题', '')
                content = row.get('内容', '')
                time_val = row.get('发布时间', '')
                news_list.append({"source": "Futu", "time": str(time_val), "content": f"{title} - {content}"})
                count += 1
            print(f"✅ 早盘获取 [富途隔夜科技快讯] {count} 条。")
        except Exception as e:
            print(f"❌ 富途接口抓取失败: {e}")

    elif mode == "intraday":
        # 盘中：使用同花顺抓取最新突发（减少 limit 提高速度）
        try:
            df_ths = ak.stock_info_global_ths()
            count = 0
            for _, row in df_ths.head(60).iterrows():
                title = row.get('标题', '')
                content = row.get('内容', '')
                time_val = row.get('发布时间', '')
                news_list.append({"source": "THS", "time": str(time_val), "content": f"{title} - {content}"})
                count += 1
            print(f"✅ 盘中获取 [同花顺实时异动] {count} 条。")
        except Exception as e:
            print(f"同花顺抓取失败: {e}")

    elif mode == "evening":
        # 盘后：取消龙虎榜，改为全方位抓取下午及盘后的宏观与公告快讯
        try:
            df_sina = ak.stock_info_global_sina()
            df_sina.columns = ["time", "content"]
            count = 0
            for _, row in df_sina.head(100).iterrows():
                news_list.append({"source": "Sina", "time": str(row['time']), "content": str(row['content'])})
                count += 1
            print(f"✅ 盘后获取 [新浪宏观及公告] {count} 条。")
        except Exception as e:
            print(f"新浪抓取失败: {e}")
            
        try:
            df_ths = ak.stock_info_global_ths()
            count = 0
            for _, row in df_ths.head(100).iterrows():
                title = row.get('标题', '')
                content = row.get('内容', '')
                time_val = row.get('发布时间', '')
                news_list.append({"source": "THS", "time": str(time_val), "content": f"{title} - {content}"})
                count += 1
            print(f"✅ 盘后获取 [同花顺全天复盘与公告快讯] {count} 条。")
        except Exception as e:
            print(f"同花顺抓取失败: {e}")

    print(f"🌍 [{mode}] 模式数据准备完毕，共提取底层信息 {len(news_list)} 条。")
    return news_list

def get_news_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def filter_seen_news(news_list, cache_file="seen_news.json"):
    """过滤掉已经推送过的新闻"""
    if not os.path.exists(cache_file):
        seen_hashes = []
    else:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                seen_hashes = json.load(f)
        except:
            seen_hashes = []
            
    new_news = []
    current_hashes = set(seen_hashes)
    
    for news in news_list:
        h = get_news_hash(news['content'])
        if h not in current_hashes:
            new_news.append(news)
            current_hashes.add(h)
            seen_hashes.append(h)
            
    # 控制缓存大小，最多存 2000 条
    if len(seen_hashes) > 2000:
        seen_hashes = seen_hashes[-2000:]
        
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(seen_hashes, f, ensure_ascii=False)
        
    print(f"去重完成：共抓取 {len(news_list)} 条，新增未读 {len(new_news)} 条。")
    return new_news

def analyze_and_score_news(news_list, mode):
    """调用 DeepSeek API 进行过滤、总结和评分"""
    if not news_list:
        return []

    print(f"正在呼叫 AI 进行 [{mode}] 模式分析...")
    news_text = "\n".join([f"[{i+1}] 时间:{item['time']} | 内容:{item['content']}" for i, item in enumerate(news_list)])

    # 根据模式动态设置规则
    mode_rules = ""
    if mode == "morning":
        mode_rules = "当前为【早盘定调】模式。请着重提取：发改委/央行等宏观政策、三大报头版定调、美股隔夜映射表现、A股龙头停牌重组或财报预警等开盘前核心信息。过滤掉昨日盘中的旧杂音。"
    elif mode == "intraday":
        mode_rules = "当前为【盘中突发监控】模式。要求极高标准：只允许输出 4星 和 5星 的核弹级突发或产业链关键异动。严禁输出日常总结性新闻，宁缺毋滥！"
    elif mode == "evening":
        mode_rules = "当前为【盘后复盘】模式。请重点总结 A股全天的市场情绪、核心板块风向，并挖掘盘后各大上市企业的重磅公告（如减持、业绩预告等）。如果新闻中提及了【自选股列表】中的个股，必须重点提取并详细分析！"

    prompt = f"""
你是一位极其苛刻、嗅觉敏锐的顶级量化游资交易员。你对市场的利好和利空极度敏感，你的任务是从海量新闻中挖掘出A股的真实炒作逻辑。
用户的特别关注领域：【{FOCUS_AREA}】
用户的自选股列表：【{MY_STOCKS}】（对于涉及自选股的异动，必须无条件优先提取并提高评级，在股票名前加*号）

任务：从以下新闻中，筛选出具有“炒作预期”或“重大杀跌风险”的事件。
【特殊指令】：{mode_rules}

打分标准（1-5星）：
- 5星：核弹级（如国家级重大会议结果、龙头超预期财报、颠覆性技术突破、自选股重大利好/利空）
- 4星：重大影响（重要产业政策出台、产业链关键涨价、资金大举抢筹）
- 3星：值得关注（行业趋势变化、一般性题材发酵）
- 1~2星：日常琐碎新闻（绝对不要输出，宁缺毋滥！）

如果 mode 是 intraday，仅输出 4-5 星的核弹级异动。否则输出 3星及以上。
请务必输出合法 JSON 格式（包含 "news" 键的对象），不可包含 Markdown 符号。
【输出要求】：对于 analysis 字段，你必须强制使用结构化输出，严格按照“利好板块：xxx | 利空板块：xxx | 潜在炒作逻辑：xxx”的格式编写。请将极其核心的字眼（如暴增、涨停、重创等）用 <b>关键词</b> 的形式包裹，前端会自动标红。
【提取代码】：在 targets 字段中，除了板块，必须自动提取并直接列出最可能受益的 2-3 只A股核心概念股。

返回格式如下：
{{
    "news": [
        {{
            "time": "原时间",
            "title": "用一句话精准总结核心事件",
            "category": "资讯类型：【宏观政策 / 财报业绩 / 新品技术 / 产业链异动 / 突发黑天鹅 / 公司公告 / 资金复盘】",
            "impact": "利好 / 利空 / 中性",
            "targets": "关联板块及 2-3 只核心受益股（自选股在名称前加*号，例如：*沃尔核材）",
            "analysis": "利好板块：xxx | 利空板块：xxx | 潜在炒作逻辑：简述资金可能炒作的路线。核心字眼用<b>包裹",
            "original": "保留或精简后的原始新闻",
            "stars": 4
        }}
    ]
}}

新闻快讯如下：
{news_text}
"""

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个只输出严谨 JSON 格式的分析助手。不要输出任何多余的话。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        parsed_json = json.loads(result_text)
        important_news = parsed_json.get("news", [])
        important_news.sort(key=lambda x: x.get('stars', 0), reverse=True)
        return important_news
    except Exception as e:
        print(f"AI 分析失败: {e}")
        return []

def push_to_wechat(important_news, mode):
    """通过 PushPlus 推送精美 HTML 页面到微信"""
    if not important_news:
        print(f"[{mode}] 模式下未筛选出符合要求的重要新闻，跳过推送。")
        return

    print("正在推送到微信...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    
    if mode == "morning":
        title = f"🌅 {date_str} 早盘定调与隔夜映射"
        main_header = f"🌅 {date_str} 早盘核心定调"
    elif mode == "intraday":
        title = f"⚡ 盘中突发重磅预警 ({time_str})"
        main_header = f"⚡ 盘中突发重磅预警 ({time_str})"
    elif mode == "evening":
        title = f"🌙 {date_str} A股盘后复盘与公告"
        main_header = f"🌙 {date_str} 盘后重点复盘"
    else:
        title = f"🔔 {date_str} 科技与AI要闻推送"
        main_header = title

    # 构建 HTML 头部和 CSS
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                background-color: #121212;
                color: #E0E0E0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 0;
                padding: 10px;
            }}
            .news-card {{
                background-color: #1e1e24;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            }}
            .badge-container {{
                display: flex;
                gap: 8px;
                margin-bottom: 16px;
                flex-wrap: wrap;
            }}
            .badge {{
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            .badge-bullish {{ background-color: #ff4d4f; color: #fff; }}
            .badge-bearish {{ background-color: #52c41a; color: #fff; }}
            .badge-neutral {{ background-color: #595959; color: #fff; }}
            .badge-stars {{ background-color: #2b2b36; color: #ffd700; border: 1px solid #444; }}
            .badge-category {{ background-color: #2b2b36; color: #177ddc; border: 1px solid #444; }}
            
            .news-title {{
                font-size: 21px;
                font-weight: bold;
                color: #FFFFFF;
                line-height: 1.4;
                margin-bottom: 6px;
            }}
            .news-time {{
                font-size: 13px;
                color: #7a828e;
                margin-bottom: 16px;
            }}
            .news-targets {{
                font-size: 15px;
                color: #ffa940;
                margin-bottom: 16px;
                font-weight: bold;
            }}
            .analysis-box {{
                background-color: #232a35;
                border-left: 4px solid #177ddc;
                border-radius: 0 8px 8px 0;
                padding: 16px;
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 16px;
                color: #d0d0d0;
            }}
            .original-text {{
                font-size: 14px;
                color: #7a828e;
                line-height: 1.5;
                background-color: #17171a;
                padding: 12px;
                border-radius: 8px;
            }}
            b {{
                color: #ff4d4f;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="mobile-container">
    """

    # 循环生成新闻卡片
    for news in important_news:
        stars = int(news.get("stars", 3))
        stars_str = "⭐" * stars + "☆" * (5 - stars)
        impact = news.get("impact", "中性")
        
        if "利好" in impact:
            impact_badge = f'<span class="badge badge-bullish">{impact}</span>'
        elif "利空" in impact:
            impact_badge = f'<span class="badge badge-bearish">{impact}</span>'
        else:
            impact_badge = f'<span class="badge badge-neutral">{impact}</span>'
            
        category = news.get("category", "综合资讯")
        news_title = news.get('title', '无标题')
        targets = news.get('targets', '无')
        analysis = news.get('analysis', '无')
        original = news.get('original', '无')
        time_display = news.get('time', '未知')

        card_html = f"""
        <div class="news-card">
            <div class="badge-container">
                {impact_badge}
                <span class="badge badge-stars">{stars_str}</span>
                <span class="badge badge-category">{category}</span>
            </div>
            
            <div class="news-title">
                {news_title}
            </div>
            
            <div class="news-time">
                时间: {time_display}
            </div>

            <div class="news-targets">
                关联标的：{targets}
            </div>

            <div class="analysis-box">
                <strong>深度分析：</strong> {analysis}
            </div>

            <div class="original-text">
                <strong>原始资讯：</strong> {original}
            </div>
        </div>
        """
        html_content += card_html

    html_content += """
        </div>
    </body>
    </html>
    """

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
                print("微信推送成功！你现在可以在手机上看到了。")
            else:
                print(f"微信推送失败，PushPlus返回错误: {result}")
        else:
            print(f"微信推送网络错误: {response.text}")
    except Exception as e:
        print(f"请求 PushPlus 失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI 智能资讯推送系统")
    parser.add_argument("--mode", choices=["morning", "intraday", "evening"], default="morning", help="运行模式")
    args = parser.parse_args()
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行 [{args.mode}] 模式任务...")
    
    # 盘中模式频率高，减少单次拉取量
    limit = 60 if args.mode == "intraday" else 150
    latest_news = fetch_data_by_mode(args.mode, limit=limit)
    
    # 根据模式决定使用的缓存文件，防止盘前盘后去重冲突
    cache_file = f"seen_news_{args.mode}.json"
    new_news = filter_seen_news(latest_news, cache_file)
    
    if not new_news:
        print(f"[{args.mode}] 暂无增量资讯，任务终止。")
        return
        
    important_news = analyze_and_score_news(new_news, args.mode)
    push_to_wechat(important_news, args.mode)
    print(f"[{args.mode}] 任务执行完毕。")

if __name__ == "__main__":
    main()
