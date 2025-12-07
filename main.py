import os
import smtplib
import feedparser
import time
import urllib.parse
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ================= 1. 讀取密碼 =================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")

# ================= 2. 【賺錢核心】居家生活蝦皮連結 =================
SHOPEE_LINKS = {
    "default": "https://s.shopee.tw/50Rnwvlxuj", 
    "tissue": "https://s.shopee.tw/4q8NkcmbFi", "paper": "https://s.shopee.tw/4q8NkcmbFi",
    "clean": "https://s.shopee.tw/4foxYJnEah", "wash": "https://s.shopee.tw/4foxYJnEah", "soap": "https://s.shopee.tw/4foxYJnEah",
    "storage": "https://s.shopee.tw/4VVXM0nrvg", "box": "https://s.shopee.tw/4VVXM0nrvg", "organize": "https://s.shopee.tw/4VVXM0nrvg",
    "kitchen": "https://s.shopee.tw/4LC79hoVGf", "cook": "https://s.shopee.tw/4LC79hoVGf", "pan": "https://s.shopee.tw/4LC79hoVGf",
    "home": "https://s.shopee.tw/9pX3hrs8IE", "decor": "https://s.shopee.tw/9pX3hrs8IE", "bed": "https://s.shopee.tw/9pX3hrs8IE",
    "furniture": "https://s.shopee.tw/9fDdVYsldD", "chair": "https://s.shopee.tw/9fDdVYsldD", "desk": "https://s.shopee.tw/9fDdVYsldD"
}

# ================= 3. AI 設定 =================
genai.configure(api_key=GOOGLE_API_KEY)

def get_valid_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    return genai.GenerativeModel(m.name)
        return None
    except:
        return None

model = get_valid_model()
# 🔥 優化：改用 Google News RSS (居家收納關鍵字)，保證抓得到文章
RSS_URL = "https://news.google.com/rss/search?q=home+organization+cleaning+hacks+interior+design&hl=en-US&gl=US&ceid=US:en"

# ================= 4. 居家風格圖片生成 =================
def get_home_image(title):
    magic_prompt = f"{title}, modern interior design, bright natural lighting, cozy home atmosphere, 8k resolution, photorealistic, architectural photography"
    safe_prompt = urllib.parse.quote(magic_prompt)
    seed = int(time.time())
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=600&nologo=true&seed={seed}&model=flux"
    return f'<div style="text-align:center; margin-bottom:20px;"><img src="{img_url}" style="width:100%; max-width:800px; border-radius:12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"></div>'

# ================= 5. 智慧選連結 =================
def get_best_link(title, content):
    text_to_check = (title + " " + content).lower()
    for keyword, link in SHOPEE_LINKS.items():
        if keyword in text_to_check and keyword != "default":
            print(f"💰 偵測到居家商機：[{keyword}]")
            return link
    return SHOPEE_LINKS["default"]

# ================= 6. AI 寫作 (SEO 強力優化版) =================
def ai_process_article(title, summary, shopee_link):
    if not model: return None, None
    print(f"🤖 AI 正在撰寫居家文章：{title}...")
    
    # 🔥 SEO 優化 Prompt：加入「標題誘餌」與「中段導購」
    prompt = f"""
    任務：將以下英文新聞改寫成「繁體中文」的「居家生活/收納技巧」部落格文章。
    
    【標題】{title}
    【摘要】{summary}
    
    【SEO 關鍵字策略 (標題必填)】
    1. 標題必須包含：收納技巧、生活智慧、清潔妙招、租屋族必看、好物推薦、Dcard熱推 (擇一使用)。
    2. 標題範例：「{title}？這3招讓家裡變大一倍」。

    【內文結構要求】
    1. **情境開頭**：描述家裡亂糟糟或生活不便的困擾，引起共鳴。
    2. **解決方案**：介紹新聞裡的技巧。
    3. **中段廣告 (重要)**：在第二段結束後，自然插入一句「💡 租屋族/收納控必備好物 (點此查看)」，並設為超連結({shopee_link})。
    4. **步驟教學**：簡單的執行步驟。
    5. **結尾**：鼓勵大家動手做。
    
    【回傳格式 (JSON)】：
    {{
        "category": "生活智慧",
        "html_body": "這裡填 HTML 內容"
    }}
    
    【文末按鈕】：
    <br><div style="text-align:center;margin:30px;"><a href="{shopee_link}" style="background:#ee4d2d;color:white;padding:15px 30px;text-decoration:none;border-radius:50px;font-weight:bold;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🏠 質感生活好物 (蝦皮優惠)</a></div>
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        data = json.loads(raw_text[start:end])
        return data.get("category", "生活智慧"), data.get("html_body", "")
    except Exception as e:
        print(f"❌ AI 處理失敗: {e}")
        return "生活新知", f"<p>{summary}</p><br><div style='text-align:center'><a href='{shopee_link}'>點此查看詳情</a></div>"

# ================= 7. 寄信 =================
def send_email(subject, category, body_html):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = BLOGGER_EMAIL
    msg['Subject'] = f"{subject} #{category}"
    msg.attach(MIMEText(body_html, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ 居家文章已發布！分類：{category}")
    except Exception as e:
        print(f"❌ 寄信失敗: {e}")

# ================= 8. 主程式 =================
if __name__ == "__main__":
    print(">>> 系統啟動 (居家生活版)...")
    if not GMAIL_APP_PASSWORD or not model:
        exit(1)

    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        entry = feed.entries[0]
        print(f"📄 處理文章：{entry.title}")
        my_link = get_best_link(entry.title, getattr(entry, 'summary', ''))
        img_html = get_home_image(entry.title)
        category, text_html = ai_process_article(entry.title, getattr(entry, 'summary', ''), my_link)
        if text_html:
            send_email(entry.title, category, img_html + text_html)
    else:
        print("📭 無新文章")
