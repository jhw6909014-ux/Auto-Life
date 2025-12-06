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
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL") # 記得確認這裡是「居家生活」的部落格信箱

# ================= 2. 【賺錢核心】居家生活蝦皮連結 =================
# 我已經把你給的 7 個連結都填進去了，並設定好關鍵字邏輯
SHOPEE_LINKS = {
    # 1. 預設連結 (萬用備胎)
    "default": "https://s.shopee.tw/50Rnwvlxuj", 
    
    # 2. 衛生紙與紙品 (銷量最大)
    "tissue": "https://s.shopee.tw/4q8NkcmbFi",
    "paper": "https://s.shopee.tw/4q8NkcmbFi",
    
    # 3. 清潔用品 (洗衣、洗碗)
    "clean": "https://s.shopee.tw/4foxYJnEah",
    "wash": "https://s.shopee.tw/4foxYJnEah",
    "soap": "https://s.shopee.tw/4foxYJnEah",
    
    # 4. 收納整理 (收納盒、櫃子)
    "storage": "https://s.shopee.tw/4VVXM0nrvg",
    "box": "https://s.shopee.tw/4VVXM0nrvg",
    "organize": "https://s.shopee.tw/4VVXM0nrvg",
    
    # 5. 廚房用品 (鍋具、餐具)
    "kitchen": "https://s.shopee.tw/4LC79hoVGf",
    "cook": "https://s.shopee.tw/4LC79hoVGf",
    "pan": "https://s.shopee.tw/4LC79hoVGf",
    
    # 6. 居家裝飾 (寢具、佈置)
    "home": "https://s.shopee.tw/9pX3hrs8IE",
    "decor": "https://s.shopee.tw/9pX3hrs8IE",
    "bed": "https://s.shopee.tw/9pX3hrs8IE",
    
    # 7. 傢俱與其他
    "furniture": "https://s.shopee.tw/9fDdVYsldD",
    "chair": "https://s.shopee.tw/9fDdVYsldD",
    "desk": "https://s.shopee.tw/9fDdVYsldD"
}

# ================= 3. AI 設定 (自動偵測可用模型) =================
genai.configure(api_key=GOOGLE_API_KEY)

def get_valid_model():
    try:
        # 自動尋找你的 API Key 能用的模型
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    return genai.GenerativeModel(m.name)
        return None
    except:
        return None

model = get_valid_model()
# 新聞來源：Lifehacker (生活智慧王)
RSS_URL = "https://lifehacker.com/rss"

# ================= 4. 居家風格圖片生成 =================
def get_home_image(title):
    """
    生成「居家生活風格」的精美圖片
    關鍵字：室內設計、明亮光線、舒適感、高畫質
    """
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

# ================= 6. AI 寫作 (生活小撇步風格) =================
def ai_process_article(title, summary, shopee_link):
    if not model: return None, None
    print(f"🤖 AI 正在撰寫居家文章：{title}...")
    
    prompt = f"""
    任務：將以下英文新聞改寫成「繁體中文」的「居家生活小撇步」部落格文章。
    
    【標題】{title}
    【摘要】{summary}
    
    【要求】
    1. **分類標籤**：請判斷類別（例如：收納技巧、清潔妙招、廚房好物、生活智慧）。
    2. **內文撰寫**：分成三段，語氣要溫馨、實用，像是在教朋友怎麼過更有質感的生活。
    3. **推銷植入**：文末加入按鈕。
    
    【回傳格式 (JSON)】：
    {{
        "category": "這裡填分類",
        "html_body": "這裡填 HTML 內容"
    }}
    
    【按鈕格式】：
    <br><div style="text-align:center;margin:30px;"><a href="{shopee_link}" style="background:#ee4d2d;color:white;padding:15px 30px;text-decoration:none;border-radius:50px;font-weight:bold;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🔥 看看這個生活好物 (蝦皮優惠)</a></div>
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
        # 備用方案
        return "生活新知", f"<p>{summary}</p><br><div style='text-align:center'><a href='{shopee_link}'>點此查看詳情</a></div>"

# ================= 7. 寄信 =================
def send_email(subject, category, body_html):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = BLOGGER_EMAIL
    
    # 加入 #標籤 讓 Blogger 自動分類
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
        print("❌ 錯誤：請檢查 Secrets 設定 (API Key 或 Gmail)")
        exit(1)

    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        # 抓最新的一篇
        entry = feed.entries[0]
        print(f"📄 處理文章：{entry.title}")
        
        # 1. 選連結
        my_link = get_best_link(entry.title, getattr(entry, 'summary', ''))
        
        # 2. 產圖
        img_html = get_home_image(entry.title)
        
        # 3. 寫文
        category, text_html = ai_process_article(entry.title, getattr(entry, 'summary', ''), my_link)
        
        if text_html:
            final_html = img_html + text_html
            send_email(entry.title, category, final_html)
    else:
        print("📭 無新文章")
