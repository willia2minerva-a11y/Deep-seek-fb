from flask import Flask, request, jsonify
import requests
import os
import random
import json

app = Flask(__name__)

FACEBOOK_PAGE_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')

print("🚀 Bot started with LOCAL responses only")

# ردود ذكية محلية
def get_local_response(message):
    message_lower = message.lower()
    
    # قاموس الردود
    responses = {
        'greeting': [
            "مرحباً بك! 😊 أنا بوت مساعد. كيف يمكنني مساعدتك اليوم؟",
            "أهلاً وسهلاً! 🤖 أنا هنا لمساعدتك في أي استفسار.",
            "مرحبا! سعيد برؤيتك. ما الذي يمكنني مساعدتك فيه؟"
        ],
        'thanks': [
            "العفو! 😊 سعيد لأنني استطعت المساعدة.",
            "لا شكر على واجب! تفضل بأي سؤال آخر.",
            "شكراً لك! أنا هنا دائماً لمساعدتك."
        ],
        'help': [
            "يمكنني مساعدتك في:\n• الإجابة على الأسئلة\n• تقديم معلومات مفيدة\n• المساعدة في مواضيع متنوعة",
            "أنا بوت ذكي يمكنه:\n• مشاركة المعرفة\n• المساعدة في البحث\n• الإجابة على استفساراتك"
        ],
        'question': [
            "هذا سؤال مثير للاهتمام! 🤔 حالياً أعمل في وضع أساسي، لكنني أتطور لأكون أكثر ذكاءً.",
            "سؤال جميل! يمكنني مساعدتك في مواضيع أخرى أيضاً.",
            "أفكر في إجابتك... في الوقت الحالي، هل لديك أسئلة أخرى؟"
        ],
        'default': [
            "شكراً على رسالتك! 📝 أنا هنا لمساعدتك في المواضيع المفيدة.",
            "أهلاً! يمكنني مساعدتك في العديد من المجالات. ما الذي يهمك؟",
            "شكراً لتواصلك معي! 😊 كيف يمكنني خدمتك اليوم؟"
        ]
    }
    
    # تحديد نوع الرسالة
    if any(word in message_lower for word in ["مرحبا", "اهلا", "السلام", "hello", "hi", "اهلين"]):
        return random.choice(responses['greeting'])
    
    elif any(word in message_lower for word in ["شكرا", "thanks", "مشكور", "يعطيك العافية"]):
        return random.choice(responses['thanks'])
    
    elif any(word in message_lower for word in ["مساعدة", "مساعده", "help", "ماذا تستطيع"]):
        return random.choice(responses['help'])
    
    elif "?" in message or any(word in message_lower for word in ["كيف", "لماذا", "متى", "أين", "ما هو"]):
        return random.choice(responses['question'])
    
    else:
        return random.choice(responses['default'])

def send_facebook_message(recipient_id, message_text):
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={FACEBOOK_PAGE_TOKEN}"
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=data)
        print(f"✅ Sent to user {recipient_id}: {message_text}")
    except Exception as e:
        print(f"❌ Facebook send error: {str(e)}")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token_sent = request.args.get('hub.verify_token')
        if token_sent == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Verification token mismatch'
    
    else:
        data = request.get_json()
        print(f"📩 Received message: {json.dumps(data)}")
        
        if data.get('object') == 'page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '')
                        
                        print(f"👤 User {sender_id} said: {message_text}")
                        
                        # الحصول على الرد المحلي
                        response_text = get_local_response(message_text)
                        
                        # إرسال الرد
                        send_facebook_message(sender_id, response_text)
                        
        return 'EVENT_RECEIVED'

@app.route('/')
def home():
    return 'Facebook AI Bot is Running with LOCAL responses!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
