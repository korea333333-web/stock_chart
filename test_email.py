import notifier
import json
import os

CONFIG_FILE = "config.json"

def test_email():
    print("이메일 발송 테스트를 시작합니다...")
    
    # 1. 설정 파일 읽기
    if not os.path.exists(CONFIG_FILE):
        print("config.json 파일이 없습니다. 설정을 먼저 확인하세요.")
        return
        
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    sender_email = config.get("sender", {}).get("email", "")
    sender_pwd = config.get("sender", {}).get("app_password", "")
    to_emails = config.get("emails", [])
    
    if not sender_email or not sender_pwd:
        print("발신자 이메일 또는 앱 비밀번호가 설정되지 않았습니다.")
        return
        
    if not to_emails:
        print("수신할 이메일 주소가 없습니다.")
        return
        
    print(f"발신자: {sender_email}")
    print(f"수신자: {', '.join(to_emails)}")
    
    # 2. 메일 내용 작성
    subject = "[주식비서] 테스트 알림 메일입니다 🚀"
    body = """
    <h2>축하합니다! 메일 연동이 성공했습니다.</h2>
    <p>대표님의 주식 자동화 비서 시스템에서 보내는 첫 번째 테스트 메일입니다.</p>
    <p>앞으로 조건에 맞는 종목이 포착되면 이렇게 예쁜 리포트로 안내해 드릴 예정입니다!</p>
    <br>
    <a href="http://localhost:8501" style="padding:10px 20px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:5px;">대시보드 바로가기</a>
    """
    
    # 3. 발송 시도
    success, msg = notifier.send_email(subject, body, to_emails, sender_email, sender_pwd)
    
    if success:
        print("✅ 이메일 성공: " + msg)
    else:
        print("❌ 이메일 실패: " + msg)

    # 4. 텔레그램 발송 시도
    telegram_bot_token = config.get("telegram", {}).get("bot_token", "")
    telegram_chat_ids = config.get("telegram", {}).get("chat_ids", [])
    
    if telegram_bot_token and telegram_chat_ids:
        print("\n텔레그램 발송 테스트를 시작합니다...")
        텔레그램_내용 = "🤖 <b>[주식비서 텔레그램 연결 성공!]</b>\n\n대표님, 텔레그램 봇과 대화방 ID가 완벽하게 연결되었습니다.\n앞으로 조건 검색에 맞는 핵심 주식이 포착되면 이곳으로 가장 빠르게 알림을 쏴 드리겠습니다! 🚀"
        t_success, t_msg = notifier.send_telegram_message(텔레그램_내용, telegram_bot_token, telegram_chat_ids)
        if t_success:
            print("✅ 텔레그램 성공: " + t_msg)
        else:
            print("❌ 텔레그램 실패: " + t_msg)

if __name__ == "__main__":
    test_email()
