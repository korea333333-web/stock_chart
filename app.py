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

# 페이지 기본 설정
st.set_page_config(
    page_title="프리미엄 주식 분석 & AI 타점 어드바이저",
    page_icon="✨",
    layout="wide"
)

def main():
    config = load_config()
    
    # CSS 인젝션 (처음 보여준 이미지 스타일 구현)
    st.markdown("""
    <style>
        /* 기본 폰트 및 스타일링 */
        html, body, [class*="css"], .stApp {
            font-family: 'Pretendard', 'Malgun Gothic', sans-serif !important;
            color: #333333;
        }
        
        /* 중앙 정렬 헤더 */
        .main-header {
            text-align: center;
            margin-bottom: 40px;
            padding-top: 20px;
        }
        .main-title {
            color: #1E3A8A; /* 진한 네이비/블루 */
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .main-subtitle {
            font-size: 1.1rem;
            color: #4B5563;
            margin-bottom: 10px;
        }
        .main-sub-subtitle {
            font-size: 0.95rem;
            color: #10B981; /* 초록색 포인트 */
        }
        .main-sub-subtitle span {
            color: #6B7280; /* 그레이 텍스트 */
        }
        
        /* 섹션 타이틀 서식 */
        .custom-section-title {
            font-size: 1.6rem;
            font-weight: bold;
            color: #1F2937;
            margin-top: 30px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* 글로벌 지수 메트릭 컨테이너 스타일링 (깔끔한 라인) */
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: bold !important;
            color: #374151 !important;
        }
        
        /* 마지막 데이터 수집 시간 배너 */
        .info-banner {
            background-color: #EFF6FF; /* 연한 파란색 배경 */
            color: #1D4ED8; /* 파란색 텍스트 */
            padding: 15px 20px;
            border-radius: 8px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 40px;
            border: 1px solid #BFDBFE;
        }
        
        /* 빨간색 검색 버튼 */
        div[data-testid="stButton"] > button {
            background-color: #EF4444 !important; /* 선명한 빨강 */
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            padding: 15px 0 !important;
            box-shadow: 0 4px 6px rgba(239, 68, 68, 0.2) !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #DC2626 !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 10px rgba(239, 68, 68, 0.3) !important;
        }
        
        /* 성공 메시지 (초록 박스) */
        .success-banner {
            background-color: #ECFCCB;
            color: #166534;
            padding: 15px 20px;
            border-radius: 8px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 15px;
            border: 1px solid #D9F99D;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* 가이드라인 (Legend) 회색 박스 */
        .legend-banner {
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            color: #374151;
            font-size: 0.95rem;
        }
        .legend-title {
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* 하단 시스템 리뷰 파란 박스 */
        .system-review-box {
            background-color: #F0FDF4;
            border: 1px solid #BBF7D0;
            padding: 20px;
            border-radius: 8px;
            color: #166534;
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            height: 100%;
        }
        .system-review-box-blue {
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            padding: 20px;
            border-radius: 8px;
            color: #1D4ED8;
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            min-height: 100px;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 1. 중앙 정렬 헤더
    st.markdown("""
    <div class="main-header">
        <div class="main-title">
            <span style="font-size:2.8rem;">✨</span> 프리미엄 주식 분석 & AI 타점 어드바이저
        </div>
        <div class="main-subtitle">
            📊 대표님의 투자 철학(A~G)을 완벽하게 계량화하여 최적의 매수 타점을 실시간으로 찾아냅니다.
        </div>
        <div class="main-sub-subtitle">
            맨 아래 [수신 설정]에 이메일과 텔레그램 ID를 기입해 두시면 봇이 다른 분들에게도 분석 리포트를 알아서 발송해 드립니다! 🚀
        </div>
    </div>
    <hr style="border:0; border-top:1px solid #E5E7EB; margin-bottom: 40px;">
    """, unsafe_allow_html=True)
    
    # 2. 글로벌 & 국내 주요 증시 현황
    st.markdown("<div class='custom-section-title'>🌍 오늘의 주요 증시 현황</div>", unsafe_allow_html=True)
    
    try:
        indices = engine.get_global_indices()
        if indices:
            i_cols = st.columns(4)
            for idx, (col, (name, data)) in enumerate(zip(i_cols, indices.items())):
                with col:
                    diff_val = data['diff']
                    pct_val = data['pct']
                    if diff_val > 0:
                        delta_color = "normal"
                    elif diff_val < 0:
                        delta_color = "inverse"
                    else:
                        delta_color = "off"
                        
                    st.metric(
                        label=name, 
                        value=f"{data['close']:,.2f}", 
                        delta=f"{diff_val:,.2f} ({pct_val:.2f}%)",
                        delta_color=delta_color
                    )
        else:
            st.info("실시간 증시 데이터를 불러오는 중입니다.")
    except Exception as e:
        st.warning("증시 데이터를 불러오지 못했습니다.")
        
    current_time_str = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    st.markdown(f"""
    <div class="info-banner">
        마지막 데이터 수집 시간: {current_time_str}
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 실시간 검색 결과
    st.markdown("<div class='custom-section-title'>📈 실시간 검색 결과</div>", unsafe_allow_html=True)
    
    start_search = st.button("🚀 지금 실시간 검색 돌리기", type="primary", use_container_width=True)
        
    if start_search:
        st.info("상위 시가총액 종목을 스캔 중입니다... 잠시만 기다려주세요.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, current_ticker_name):
            percent = int((current / total) * 100)
            progress_bar.progress(percent)
            status_text.text(f"스캔 중... {current}/{total} (분석 중: {current_ticker_name})")
            
        df = engine.scan_hot_stocks(limit=30, progress_callback=update_progress)
        
        progress_bar.empty()
        status_text.empty()
        
        st.session_state['search_result'] = df
        st.rerun()
            
    if 'search_result' in st.session_state:
        df = st.session_state['search_result']
        if not df.empty:
            # 성공 배너 렌더링
            st.markdown("""
            <div class="success-banner">
                <span>✅</span> 종목 스캔 완료! (점수순으로 정렬되었습니다)
            </div>
            """, unsafe_allow_html=True)
            
            # 가이드라인 (Legend) 렌더링
            st.markdown("""
            <div class="legend-banner">
                <div class="legend-title">💡 점수별 투자 가이드라인 (Legend)</div>
                <div style="line-height:1.8;">
                    <span style="color:#16A34A; font-weight:bold;">🟢 85점 이상: 당장 분석 후 강력 매수 고려 (조건 완벽 일치)</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span style="color:#D97706; font-weight:bold;">🟡 70점 이상: 좋은 흐름, 분할 매수 및 관심 주시</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span style="color:#DC2626; font-weight:bold;">🔴 50점 미만: 아직 무르익지 않음 (관망)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 데이터프레임
            df['종목표시'] = df['종목명'] + " (" + df['적합도 점수'].astype(str) + "점)"
            
            st.dataframe(
                df[['종목코드', '종목명', '현재가(원)', '등락률(%)', '영업이익(억)', '시가총액(억)', '적합도 점수', '조건만족', '종목표시']], 
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # 4. 상세 분석 UI
            st.markdown("<div class='custom-section-title'>📊 개별 종목 정밀 차트 분석</div>", unsafe_allow_html=True)
            
            st.markdown("<p style='font-weight:600; color:#4B5563; margin-bottom:5px;'>분석할 종목을 선택하세요 (높은 점수순 정렬):</p>", unsafe_allow_html=True)
            selected_display = st.selectbox("", df['종목표시'].tolist(), label_visibility="collapsed")
            
            if selected_display:
                target_row = df[df['종목표시'] == selected_display].iloc[0]
                total_sc = target_row['적합도 점수']
                tk_name = target_row['종목명']
                
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.markdown(f"<p style='font-weight:bold; color:#1F2937; margin-bottom:0;'>🎯 [{tk_name}] 투자 적기 (조건 부합도)</p>", unsafe_allow_html=True)
                    st.markdown(f"<h1 style='color:#111827; font-size:3.5rem; margin-top:0;'>{total_sc}%</h1>", unsafe_allow_html=True)
                
                with col_right:
                    st.markdown(f"""
                    <div class="system-review-box-blue">
                        <span>💡</span> <b>시스템 한줄평:</b> 이 종목은 오늘 기준으로 대표님의 철학에 {total_sc}% 만큼 가까워진 타점입니다.
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                chart_df_d = target_row['_chart_df']
                chart_df_w = target_row.get('_chart_w', pd.DataFrame())
                chart_df_m = target_row.get('_chart_m', pd.DataFrame())
                
                if not chart_df_d.empty:
                    tab_daily, tab_weekly, tab_monthly = st.tabs(["일봉 차트", "주봉 차트", "월봉 차트"])
                    
                    def create_candlestick(df_data, show_ma=False):
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=df_data.index, open=df_data['Open'], high=df_data['High'], low=df_data['Low'], close=df_data['Close'], name='가격'
                        ))
                        if show_ma and 'MA20' in df_data.columns:
                            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA20'], line=dict(color='#F59E0B', width=2), name='20일 이평선'))
                        
                        fig.update_layout(
                            xaxis_rangeslider_visible=False,
                            margin=dict(l=0, r=0, t=10, b=0),
                            height=400,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F3F4F6')
                        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F3F4F6')
                        return fig

                    with tab_daily:
                        st.plotly_chart(create_candlestick(chart_df_d, show_ma=True), use_container_width=True)
                    with tab_weekly:
                        if not chart_df_w.empty:
                            st.plotly_chart(create_candlestick(chart_df_w, show_ma=False), use_container_width=True)
                    with tab_monthly:
                        if not chart_df_m.empty:
                            st.plotly_chart(create_candlestick(chart_df_m, show_ma=False), use_container_width=True)
                
        else:
            st.warning("현재 지정된 조건식(A~G)에 해당하는 종목이 발견되지 않았습니다.")
    else:
        st.info("💡 위의 빨간색 [🚀 지금 실시간 검색 돌리기] 버튼을 클릭하시면 즉시 전국장 스캔 모델이 가동됩니다.")
    
    st.markdown("<br><hr style='border:0; border-top:1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
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
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 5. 주요 뉴스 연동
    st.markdown("<div class='custom-section-title'>📰 오늘의 주요 증시 뉴스</div>", unsafe_allow_html=True)
    with st.spinner("최신 글로벌 뉴스를 불러오는 중입니다..."):
        news_data = engine.get_latest_news()
        
    if news_data:
        tabs = st.tabs(list(news_data.keys()))
        for tab, (category, items) in zip(tabs, news_data.items()):
            with tab:
                if items:
                    for item in items:
                        st.markdown(f"- **[{item['source']}]** <a href='{item['link']}' target='_blank' style='text-decoration:none; color:#1D4ED8; font-weight:600;'>{item['title']}</a> <span style='color:#9CA3AF; font-size:0.85rem;'>({item['date']})</span>", unsafe_allow_html=True)
                        if item.get("title_ko") and item.get("title_ko") != "(번역 실패)":
                            st.markdown(f"<div style='margin-left:20px; color:#059669; font-size:0.9rem;'>🇰🇷 {item['title_ko']}</div>", unsafe_allow_html=True)
                else:
                    st.info("관련 최신 뉴스가 없습니다.")
    else:
        st.warning("뉴스 검색 서버에 연결할 수 없습니다.")
        
    st.markdown("<br><hr style='border:0; border-top:1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
    
    # 6. 수신 정보 설정
    st.markdown("<div class='custom-section-title'>⚙️ 알람 봇 수신 채널 설정</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#4B5563; margin-bottom:20px;'>💡 이메일 주소나 텔레그램 아이디를 입력해 두시면 조건부합 종목 분석 시 리포트를 전송해 드립니다.</p>", unsafe_allow_html=True)
    
    col_em, col_tg = st.columns(2)
    with col_em:
        current_emails = config.get("emails", [])
        email_text_val = "\n".join(current_emails) if current_emails and isinstance(current_emails[0], str) else ""
        emails_str = st.text_area("✉️ 이메일 주소 (줄바꿈 구분으로 여러 개 입력 가능)", value=email_text_val, height=120, placeholder="ceo@company.com")
        config["emails"] = [e.strip() for e in emails_str.split("\n") if e.strip()]
        
    with col_tg:
        current_chat_ids = config.get("telegram", {}).get("chat_ids", [])
        tg_text_val = "\n".join(current_chat_ids) if current_chat_ids and isinstance(current_chat_ids[0], str) else ""
        chat_ids_str = st.text_area("🚀 텔레그램 아이디 (줄바꿈 구분으로 여러 개 입력 가능)", value=tg_text_val, height=120, placeholder="@your_id")
        bot_token = config.get("telegram", {}).get("bot_token", "")
        config["telegram"] = {"bot_token": bot_token, "chat_ids": [cid.strip() for cid in chat_ids_str.split("\n") if cid.strip()]}
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("수신 설정 저장하기", type="secondary"):
        save_config(config)
        st.success("알림 채널 정보가 성공적으로 저장되었습니다.")
            
    st.markdown("""
    <br><br><br>
    <div style='text-align: center; color: #9CA3AF; border-top: 1px solid #E5E7EB; padding-top: 20px; font-size: 0.85rem;'>
        <b>Disclaimer:</b> 본 분석 시스템은 투자 참고용이며, 최종 투자 판단과 책임은 본인에게 있습니다.<br>
        Copyright © 2026. 나만의 주식 분석 & AI 타점 어드바이저 All Rights Reserved.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
