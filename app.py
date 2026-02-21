import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import plotly.graph_objects as go
import engine

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "sender": {"email": "", "app_password": ""},
        "emails": [], 
        "telegram": {"bot_token": "", "chat_ids": []}
    }

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

# 페이지 기본 설정 (가장 상단에 위치)
st.set_page_config(
    page_title="나만의 주식 비서 - 조건 검색 결과",
    page_icon="📈",
    layout="wide"
)

def main():
    config = load_config()
    
    # --- 사이드바: 알림 설정 관리 ---
    with st.sidebar:
        st.header("⚙️ 알림 수신 설정")
        st.markdown("여기에서 알림을 받을 이메일과 텔레그램 대화방(Chat ID)을 관리할 수 있습니다.")
        
        # 보내는 사람 설정 (이메일 발송용)
        st.subheader("📤 발송자 설정 (구글)")
        st.markdown("알림을 '보낼' 구글 계정과 앱 비밀번호를 입력하세요.")
        sender_email = st.text_input("발신용 구글 이메일", value=config.get("sender", {}).get("email", ""))
        sender_passwd = st.text_input("앱 비밀번호 (16자리)", value=config.get("sender", {}).get("app_password", ""), type="password")

        # 이메일 설정란
        st.subheader("📧 수신 이메일 목록")
        st.markdown("알림을 '받을' 이메일 주소들입니다.")
        emails_text = st.text_area("수신 이메일 (줄바꿈 구분)", value="\n".join(config.get("emails", [])), height=100)
        
        # 텔레그램 설정란 (숨김 또는 유지 - 현재 카톡 제외, 이메일 중심)
        with st.expander("💬 텔레그램 설정 (선택사항)"):
            bot_token = st.text_input("Bot Token", value=config.get("telegram", {}).get("bot_token", ""))
            chat_ids_text = st.text_area("Chat IDs", value="\n".join(config.get("telegram", {}).get("chat_ids", [])), height=70)
        
        # 저장 버튼
        if st.button("설정 저장하기", use_container_width=True):
            new_emails = [e.strip() for e in emails_text.split('\n') if e.strip()]
            new_chat_ids = [c.strip() for c in chat_ids_text.split('\n') if c.strip()]
            
            config["sender"] = {"email": sender_email.strip(), "app_password": sender_passwd.strip()}
            config["emails"] = new_emails
            if "telegram" not in config:
                config["telegram"] = {}
            config["telegram"]["bot_token"] = bot_token.strip()
            config["telegram"]["chat_ids"] = new_chat_ids
            
            save_config(config)
            st.success("설정이 성공적으로 저장되었습니다!")

    # 1. 헤더 영역 (제목 및 설명)
    st.title("📈 자동화 주식 검색 및 알림 대시보드")
    st.markdown("---")
    st.markdown("이 웹페이지는 대표님의 투자 철학(A~G조건 및 펀더멘털)에 부합하는 종목을 실시간/정해진 시간에 검색하여 보여주는 개인용 대시보드입니다.")
    st.markdown("👈 왼쪽의 **[알림 수신 설정]** 탭에서 지정하신 이메일과 텔레그램으로 봇이 알림을 쏴 드립니다!")
    
    # 2. 검색 시간 정보 표시
    st.subheader("최근 검색 결과 (모의 데이터 테스트 중입니다)")
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    st.info(f"마지막 검색 시간: **{current_time}**")
    
    # 3. 실시간 주식 데이터 검색 (엔진 연동)
    st.subheader("📈 실시간 검색 결과")
    
    if st.button("🚀 지금 실시간 검색 돌리기", type="primary", use_container_width=True):
        st.info("코스피/코스닥 시가총액 상위 종목들을 스캔 중입니다... (속도를 위해 상위 30종목 1차 스캔)")
        
        # 진행 상태를 표시할 빈 공간(영역) 생성
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 콜백 함수: 엔진이 종목 하나를 분석할 때마다 이 함수를 눌러서 화면 갱신
        def update_progress(current, total, current_ticker_name):
            percent = int((current / total) * 100)
            progress_bar.progress(percent)
            status_text.text(f"스캔 진행 중... {current}/{total} (현재 분석 중: {current_ticker_name})")
            
        # 엔진 실행 (limit=30 으로 조정하여 속도 향상, 콜백 함수 연결)
        df = engine.scan_hot_stocks(limit=30, progress_callback=update_progress)
        
        # 검색이 다 끝나면 프로그레스 바 흔적 지우기
        progress_bar.empty()
        status_text.empty()
        
        st.session_state['search_result'] = df
        st.rerun()
            
    if 'search_result' in st.session_state:
        df = st.session_state['search_result']
        if not df.empty:
            st.success("검색 완료! (조건 일치 점수가 높은 순으로 정렬됩니다)")
            
            def highlight_high_score(val):
                color = '#d4edda' if isinstance(val, (int, float)) and val >= 90 else ''
                return f'background-color: {color}'
            
            # ========================================================
            # 표 렌더링 (숨김 컬럼 제외)
            # ========================================================
            display_columns = [col for col in df.columns if not col.startswith('_')]
            df_display = df[display_columns]
            
            st.dataframe(
                df_display.style.map(highlight_high_score, subset=['적합도 점수']),
                hide_index=True
            )
            
            # 발송 테스트 연동용 코드 (나중에 자동화 시 활용)
            high_score_items = df[df['적합도 점수'] >= 90]
            if not high_score_items.empty and st.button("🔔 90점 이상 종목 알림 발송하기 (수동)"):
                st.info("이 기능은 4단계 자동화에서 완벽하게 통합될 예정입니다!", icon="ℹ️")
                
            st.markdown("---")
            
            # ========================================================
            # 시각적 차트 분석 UI (Plotly 캔들스틱 & 오버레이)
            # ========================================================
            st.subheader("📊 개별 종목 정밀 차트 분석")
            
            # 콤보박스에 종목 표시 (종목명 + 점수)
            df['종목표시'] = df['종목명'] + " (" + df['적합도 점수'].astype(str) + "점)"
            
            selected_display = st.selectbox("분석할 종목을 선택하세요 (높은 점수순 정렬):", df['종목표시'].tolist())
            
            if selected_display:
                # 선택된 행(Row) 정보 추출
                target_row = df[df['종목표시'] == selected_display].iloc[0]
                chart_df = target_row['_chart_df']
                markers = target_row['_markers']
                tk_name = target_row['종목명']
                
                if not chart_df.empty:
                    # Plotly 차트 객체 캔버스 생성
                    fig = go.Figure()
                    
                    # 1. 캔들스틱 메인 차트 그리기
                    fig.add_trace(go.Candlestick(
                        x=chart_df.index,
                        open=chart_df['Open'],
                        high=chart_df['High'],
                        low=chart_df['Low'],
                        close=chart_df['Close'],
                        name='주가'
                    ))
                    
                    # 2. 이동평균선(5, 20, 60일선) 오버레이
                    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['MA5'], line=dict(color='magenta', width=1.5), name='5일선'))
                    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['MA20'], line=dict(color='orange', width=1.5), name='20일선'))
                    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['MA60'], line=dict(color='green', width=1.5), name='60일선'))
                    
                    # 3. 주요 조건 발생 지점에 텍스트 오버레이(주석/마커) 추가
                    # markers 딕셔너리에 {'B_Vol': (날짜, 가격, 내용), ...} 형태로 들어있음
                    for condition_key, marker_info in markers.items():
                        m_date, m_price, m_text = marker_info
                        fig.add_annotation(
                            x=m_date,
                            y=m_price,
                            text=m_text,
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1.5,
                            arrowwidth=2,
                            arrowcolor="Black" if condition_key != 'D_Spike' else "Red",
                            font=dict(color="White", size=12),
                            bgcolor="Blue" if condition_key == 'C_Low' else ("Red" if condition_key == 'D_Spike' else "Purple"),
                            bordercolor="Black",
                            borderwidth=1,
                            ay=-40 # 화살표 길이
                        )
                        
                    # 차트 레이아웃(디자인) 설정
                    fig.update_layout(
                        title=f"<b>{tk_name}</b> 기술적 분석 차트 및 타점 오버레이",
                        yaxis_title="주가 (원)",
                        xaxis_rangeslider_visible=False, # 하단 거추장스러운 슬라이더 숨김
                        template="plotly_white",
                        height=600,
                        margin=dict(l=20, r=20, t=50, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 하단 코멘트
                    st.info(f"💡 분석 코멘트: {tk_name} 달성 조건 ➔ {target_row['조건만족']}")
                    
                else:
                    st.warning("차트를 그리기 위한 과거 데이터가 부족합니다.")
                
        else:
            st.warning("현재 A~G 조건을 만족하거나 점수를 획득한 종목이 없습니다.")
    else:
        st.info("위에 있는 시작 버튼을 눌러 조건 검색을 가동해 보세요.")
    
    # 5. 상세 조건 설명 토글 (접었다 폈다 할 수 있는 기능)
    with st.expander("👉 적용된 조건 검색식(A~G) 자세히 보기"):
        st.markdown(
            """
            * **A [주가범위]:** 0일전 종가가 1,000원 ~ 50,000원
            * **B [기간내 거래대금]:** 0일전 5일 이내 20,000백만(200억) 이상
            * **C [기간내 주가위치]:** 5봉전 20봉 이내 '기간내 최저가' 발생 (저점 횡보)
            * **D [주가비교]:** 10봉전 종가 < 10봉전 고가 (15% 이상 상승봉 존재)
            * **E [주가비교]:** 0일전 종가 > 10봉전 고가 * 0.9 (상단 지지)
            * **F [주가이평배열]:** 5 > 20 > 60 (정배열)
            * **G [이동평균이격도]:** 5일선에 98% ~ 102% 이내로 바짝 붙음 (눌림목 타점)
            * **+알파 [펀더멘털]:** 영업이익 10억 이상 & 시가총액 500억 이상
            """
        )

if __name__ == "__main__":
    main()
