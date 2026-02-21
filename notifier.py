import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import requests

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def send_email(subject, body, to_emails, sender_email, sender_password):
    """SMTP를 이용해 이메일을 발송합니다."""
    if not to_emails:
        return False, "수신할 이메일 주소가 없습니다."
        
    try:
        # 이 예제는 Gmail의 SMTP 서버를 사용한다고 가정합니다.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        # 앱 비밀번호 사용 필요 (계정 비밀번호 X)
        server.login(sender_email, sender_password)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(to_emails)  # 여러 명에게 한번에 발송
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        server.send_message(msg)
            
        server.quit()
        return True, "이메일 발송 성공"
    except Exception as e:
        return False, f"이메일 발송 실패: {str(e)}"

def send_telegram_message(text, bot_token, chat_ids):
    """Telegram 봇 API를 이용해 메시지를 발송합니다."""
    if not bot_token or not chat_ids:
        return False, "텔레그램 설정이 비어있습니다."
        
    try:
        success_count = 0
        for chat_id in chat_ids:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                success_count += 1
                
        if success_count > 0:
            return True, f"텔레그램 발송 성공 ({success_count}건)"
        return False, "텔레그램 발송 요청 실패"
    except Exception as e:
        return False, f"텔레그램 통신 오류: {str(e)}"

def send_kakao_message(text, access_token):
    """Kakao API (나에게 보내기) 예시입니다. 복잡한 토큰 갱신 로직이 필요합니다."""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "http://localhost:8501",
                "mobile_web_url": "http://localhost:8501"
            },
            "button_title": "대시보드 확인하기"
        })
    }
    
    try:
        res = requests.post(url, headers=headers, data=payload)
        if res.status_code == 200:
            return True, "카카오톡 발송 성공"
        return False, f"카카오톡 발송 실패: {res.text}"
    except Exception as e:
        return False, f"카카오톡 통신 오류: {str(e)}"
