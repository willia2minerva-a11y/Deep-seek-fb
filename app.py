from flask import Flask, request, jsonify
import requests
import os
import json
from config.banned_words import banned_words
from config.safe_responses import safe_responses

app = Flask(__name__)

# المتغيرات البيئية
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
FACEBOOK_PAGE_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')

# نظام الفلترة
def filter_content(text):
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            return False, "content_not_allowed"
    return True, text

# الاتصال بـ DeepSeek
def get_ai_response(message):
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return "عذراً، حدث خطأ في النظام. حاول مرة أخرى."
    except:
        return "عذراً، الخدمة غير متاحة حالياً."

# إرسال رد لفيسبوك
def send_facebook_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={FACEBOOK_PAGE_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, json=data)

# ويبهوك فيسبوك
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token_sent = request.args.get('hub.verify_token')
        if token_sent == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Verification token mismatch'
    
    else:
        data = request.get_json()
        if data.get('object') == 'page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '')
                        
                        # فلترة الرسالة
                        is_safe, filtered_msg = filter_content(message_text)
                        
                        if not is_safe:
                            response_text = safe_responses["high_risk"]
                        else:
                            response_text = get_ai_response(message_text)
                            # فلترة رد الذكاء الاصطناعي أيضاً
                            is_safe, final_response = filter_content(response_text)
                            if not is_safe:
                                response_text = safe_responses["confused"]
                        
                        send_facebook_message(sender_id, response_text)
        return 'EVENT_RECEIVED'

@app.route('/')
def home():
    return 'Facebook AI Bot is Running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
