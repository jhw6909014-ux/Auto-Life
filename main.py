import os
import smtplib
import feedparser
import time
import urllib.parse
import random
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")

SHOPEE_LINKS = {
    "default": "https://s.shopee.tw/50Rnwvlxuj", 
    "tissue": "https://s.shopee.tw/4q8NkcmbFi", "paper": "https://s.shopee.tw/4q8NkcmbFi",
    "clean": "https://s.shopee.tw/4foxYJnEah", "wash": "https://s.shopee.tw/4foxYJnEah", "soap": "https://s.shopee.tw/4foxYJnEah",
    "storage": "https://s.shopee.tw/4VVXM0nrvg", "box": "https://s.shopee.tw/4VVXM0nrvg", "organize": "https://s.shopee.tw/4VVXM0nrvg",
    "kitchen": "https://s.shopee.tw/4LC79hoVGf", "cook": "https://s.shopee.tw/4LC79hoVGf", "pan": "https://s.shopee.tw/4LC79hoVGf",
    "home": "https://s.shopee.tw/9pX3hrs8IE", "decor": "https://s.shopee.tw/9pX3hrs8IE", "bed": "https://s.shopee.tw/9pX3hrs8IE",
    "furniture": "https://s.shopee.tw/9fDdVYsldD", "chair": "https://s.shopee.tw/9fDdVYsldD", "desk": "https://s.shopee.tw/9fDdVYsldD"
}

genai.configure(api_key=GOOGLE_API_KEY)
def get_valid_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name: return genai.GenerativeModel(m.name)
    except: return None
model = get_valid_model()
RSS_URL = "https://news.google.com/rss/search?q=home+organization+cleaning+hacks+interior+design&hl=en-US&gl=US&ceid=US:en"

def get_home_image(title):
    magic_prompt = f"{title}, modern interior design, bright natural lighting, cozy home atmosphere, 8k resolution, photorealistic"
    safe_prompt = urllib.parse.quote(magic_prompt)
    seed = int(time.time())
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=600&nologo=true&seed={seed}&model=flux"
    return f'<div style="text-align:center; margin-bottom:20px;"><img src="{img_url}" style="width:100%; max-width:800px; border-radius:12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"></div>'

def get_best_link(title, content):
    text_to_check = (title + " " + content).lower()
    for keyword, link in SHOPEE_LINKS.items():
        if keyword in text_to_check and keyword != "default": return link
    return SHOPEE_LINKS["default"]

def ai_process_article(title, summary, shopee_link):
    if not model: return None, None
    
    # === 居家人格轉盤 ===
    styles = [
        "風格：一位『收納強迫症』的媽媽，看到亂七八糟就受不了，極度推崇整潔和秩序。",
        "風格：一位『超級懶人』，只喜歡用最輕鬆、最省力的方式做家事，推薦的神器都要能讓人偷懶。",
        "風格：一位『生活美學家』，講話優雅，重視儀式感，覺得家裡的每個角落都要美美的。",
        "風格：一位『精明的主婦』，非常會比價，知道哪裡買衛生紙最便宜，強調囤貨的重要性。"
    ]
    selected_style = random.choice(styles)
    print(f"🤖 AI 今日人格：{selected_style}")

    prompt = f"""
    任務：將以下英文新聞改寫成「居家生活」部落格文章。
    【標題】{title}
    【摘要】{summary}
    
    【寫作指令】
    1. **請嚴格扮演此角色**：{selected_style}
    2. **SEO標題**：必須包含「收納技巧、生活智慧、清潔妙招、租屋族必看」其中之一。
    3. **中段導購**：在第二段結束後，自然插入一句「💡 租屋族/收納控必備好物 (點此查看)」，並設為超連結({shopee_link})。
    
    【回傳 JSON】：{{"category": "生活智慧", "html_body": "HTML內容"}}
    【文末按鈕】：<br><div style="text-align:center;margin:30px;"><a href="{shopee_link}" style="background:#ee4d2d;color:white;padding:15px 30px;text-decoration:none;border-radius:50px;font-weight:bold;">🏠 質感生活好物 (蝦皮優惠)</a></div>
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        data = json.loads(raw_text[start:end])
        return data.get("category", "生活智慧"), data.get("html_body", "")
    except: return "生活新知", f"<p>{summary}</p><br><div style='text-align:center'><a href='{shopee_link}'>點此查看詳情</a></div>"

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
        print(f"✅ 發布成功：{category}")
    except: pass

if __name__ == "__main__":
    if not GMAIL_APP_PASSWORD or not model: exit(1)
    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        entry = feed.entries[0]
        my_link = get_best_link(entry.title, getattr(entry, 'summary', ''))
        img_html = get_home_image(entry.title)
        category, text_html = ai_process_article(entry.title, getattr(entry, 'summary', ''), my_link)
        if text_html: send_email(entry.title, category, img_html + text_html)
    else: print("📭 無新文章")
