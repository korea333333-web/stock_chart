import json
import os
from datetime import datetime
import pandas as pd
import engine
import notifier

def main():
    print(f"[{datetime.now()}] 자동화 봇 스크립트 시작")
    config = notifier.load_config()
    
    # 1. 대상 종목 스캔 (우선순위 상위 50종목 스캔)
    print("종목 스캔 중...")
    # 프로모션용 제한을 풀 수 있지만 우선 빠른 속도를 위해 limit=50 유지
    df = engine.scan_hot_stocks(limit=50)
    
    if df.empty:
        print("검색된 종목이 없습니다.")
        return
        
    # 2. 투자 적기 70점 이상 종목 필터링
    hot_stocks = df[df['적합도 점수'] >= 70].copy()
    
    if hot_stocks.empty:
        print("조건(70점 이상)을 만족하는 우수한 종목이 없어 알림 발송을 생략합니다.")
        return
        
    print(f"총 {len(hot_stocks)}개의 투자 적기 종목 발견!")
    
    # 3. 알림 내용 구성
    # 이메일용 HTML 본문 생성
    body_html = f"<h2>🔥 오늘의 강력 매수 추천 종목 (총 {len(hot_stocks)}개)</h2>"
    body_html += "<table border='1' cellpadding='10' cellspacing='0' style='border-collapse: collapse;'>"
    body_html += "<tr style='background-color: #f2f2f2;'><th>종목명</th><th>현재가</th><th>등락률</th><th>적합도 점수</th><th>만족조건</th></tr>"
    
    # 텔레그램용 텍스트 본문 생성
    tg_text = f"🚨 <b>[주식 로봇 AI 알림]</b> 🚨\n\n대표님, 현재 <b>{len(hot_stocks)}개</b>의 우량 종목이 투자 적기(70점 이상)에 도달했습니다!\n\n"
    
    for _, row in hot_stocks.iterrows():
        name = row['종목명']
        price = row['현재가(원)']
        chg = row['등락률(%)']
        score = row['적합도 점수']
        cond = row['조건만족']
        
        # 이메일 행 추가
        body_html += f"<tr><td><b>{name}</b></td><td>{price:,.0f}원</td><td>{chg}%</td><td><b>{score}점</b></td><td>{cond}</td></tr>"
        
        # 텔레그램 내용 추가
        tg_text += f"🎯 <b>{name}</b> ({price:,.0f}원 / {chg}%)\n"
        tg_text += f"✔️ 총점: <b>{score}점</b>\n"
        tg_text += f"✔️ 비고: {cond}\n\n"
        
    body_html += "</table><br><p>자세한 차트 분석 및 타점 확인은 대시보드 웹사이트에서 바로 확인하세요!</p>"
    
    # 텔레그램 하단 버튼 (Streamlit URL 접속 유도)
    tg_text += "👉 <a href='https://korea333333-web-stock-chart.streamlit.app'>대시보드로 이동하여 상세 차트 보기</a>"
    
    # 4. 이메일 자동 발송
    emails = config.get("emails", [])
    sender = config.get("sender", {})
    if emails and sender.get("email") and sender.get("app_password"):
        print(f"이메일 발송 시도: {emails}")
        success, msg = notifier.send_email(
            subject=f"[주식 AI] 🎯 {datetime.now().strftime('%m/%d')} 강력 매수 적기 종목 알림 ({len(hot_stocks)}건)",
            body=body_html,
            to_emails=emails,
            sender_email=sender["email"],
            sender_password=sender["app_password"]
        )
        print(f"이메일 발송 결과: {msg}")
    
    # 5. 텔레그램 자동 발송
    telegram = config.get("telegram", {})
    bot_token = telegram.get("bot_token")
    chat_ids = telegram.get("chat_ids", [])
    
    if bot_token and chat_ids:
        print(f"텔레그램 발송 시도: {chat_ids}")
        success, msg = notifier.send_telegram_message(tg_text, bot_token, chat_ids)
        print(f"텔레그램 발송 결과: {msg}")

if __name__ == "__main__":
    main()
