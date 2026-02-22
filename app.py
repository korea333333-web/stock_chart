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
    
    # CSS 인젝션 (Shadcn/ui 라이트모드 모던 디자인)
    st.markdown("""
    <style>
        /* 기본 폰트 및 스타일링 */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        html, body, [class*="css"], .stApp {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
            color: #0f172a;
            background-color: #ffffff;
        }
        
        /* 중앙 정렬 헤더 */
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-top: 1.5rem;
        }
        .main-title {
            color: #0f172a; 
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        .main-subtitle {
            font-size: 1.125rem;
            color: #475569;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .main-sub-subtitle {
            font-size: 0.875rem;
            color: #64748b;
        }
        
        /* 섹션 타이틀 서식 */
        .custom-section-title {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            color: #0f172a;
            margin-top: 2rem;
            margin-bottom: 1.25rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* 글로벌 지수 메트릭 컨테이너 스타일링 */
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
            letter-spacing: -0.025em !important;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.875rem !important;
            font-weight: 500 !important;
        }
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            padding: 1.25rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        /* 마지막 데이터 수집 시간 배너 */
        .info-banner {
            background-color: #f8fafc;
            color: #475569;
            padding: 0.75rem 1rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            font-weight: 500;
            margin-top: 1rem;
            margin-bottom: 2rem;
            border: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
        }
        
        /* 검색 버튼 (Shadcn Primary) */
        div[data-testid="stButton"] > button {
            background-color: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #0f172a !important;
            border-radius: 0.375rem !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            width: 100% !important;
            transition: all 0.15s ease-in-out !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #1e293b !important;
            border-color: #1e293b !important;
        }
        div[data-testid="stButton"] > button:focus:not(:focus-visible) {
            color: #f8fafc !important;
        }
        
        /* Secondary Button */
        div[data-testid="stButton"] > button[kind="secondaryFormSubmit"],
        div[data-testid="stButton"] > button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        }
        div[data-testid="stButton"] > button[kind="secondaryFormSubmit"]:hover,
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #e2e8f0 !important;
            color: #0f172a !important;
        }
        
        /* 성공 메시지 (Alert 느낌) */
        .success-banner {
            background-color: #f0fdf4;
            color: #166534;
            padding: 1rem 1.25rem;
            border-radius: 0.375rem;
            font-weight: 500;
            font-size: 0.875rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #bbf7d0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        /* 가이드라인 (Legend) */
        .legend-banner {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            border-radius: 0.5rem;
            color: #334155;
            font-size: 0.875rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        .legend-title {
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* 하단 시스템 리뷰 파란 박스 */
        .system-review-box, .system-review-box-blue {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 1rem 1.25rem;
            border-radius: 0.375rem;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 500;
            font-size: 0.875rem;
            margin-top: 0.5rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            min-height: 80px;
        }
        
        /* 위젯 테두리 및 섀도우 개선 */
        .stSelectbox > div[data-baseweb="select"] > div {
            border: 1px solid #e2e8f0 !important;
            border-radius: 0.375rem !important;
            background-color: #ffffff !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        }
        .stTextArea > div[data-baseweb="textarea"] > div, .stTextInput > div[data-baseweb="input"] > div {
            border: 1px solid #e2e8f0 !important;
            border-radius: 0.375rem !important;
            background-color: #ffffff !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        }
        .stTextArea textarea, .stTextInput input {
            color: #0f172a !important;
        }
        
        /* Expander (Accordion 디자인) */
        .streamlit-expanderHeader {
            font-weight: 500 !important;
            color: #0f172a !important;
            background-color: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 0.375rem !important;
        }
        div[data-testid="stExpander"] {
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Tabs 컴포넌트 커스텀 */
        button[data-baseweb="tab"] {
            font-weight: 500 !important;
            color: #64748b !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #0f172a !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #0f172a !important;
        }
        
        /* DataFrame Header & Cells */
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        hr {
            border-top: 1px solid #e2e8f0 !important;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 1. 중앙 정렬 헤더
    st.markdown("""
    <div class="main-header">
        <div class="main-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trending-up" style="margin-right: 8px;"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
            프리미엄 주식 분석 & AI 타점 어드바이저
        </div>
        <div class="main-subtitle">
            투자 철학(A~G)을 계량화한 초정밀 실시간 타점 스캐너
        </div>
        <div class="main-sub-subtitle">
            하단 수신 설정에 이메일과 텔레그램 ID를 기입하면 정기 리포트를 자동 전송합니다.
        </div>
    </div>
    <hr style="border:0; border-top:1px solid #e2e8f0; margin-bottom: 2rem;">
    """, unsafe_allow_html=True)
    
    # 2. 글로벌 & 국내 주요 증시 현황
    st.markdown("<div class='custom-section-title'>오늘의 주요 증시 현황</div>", unsafe_allow_html=True)
    
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
    st.markdown("<div class='custom-section-title'>실시간 검색 결과</div>", unsafe_allow_html=True)
    
    start_search = st.button("지금 실시간 검색 돌리기", type="primary", use_container_width=True)
        
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
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-circle-2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
                종목 스캔 완료! (점수순으로 정렬되었습니다)
            </div>
            """, unsafe_allow_html=True)
            
            # 가이드라인 (Legend) 렌더링
            st.markdown("""
            <div class="legend-banner">
                <div class="legend-title">투자 가이드라인</div>
                <div style="line-height:1.8;">
                    <span style="color:#16a34a; font-weight:600;">🟢 85점 이상: 강력 매수 고려 (조건 완벽 일치)</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span style="color:#d97706; font-weight:600;">🟡 70점 이상: 분할 매수 및 관심 주시</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span style="color:#dc2626; font-weight:600;">🔴 50점 미만: 관망 (조건 불일치)</span>
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
            st.markdown("<div class='custom-section-title'>개별 종목 정밀 차트 분석</div>", unsafe_allow_html=True)
            
            st.markdown("<p style='font-weight:500; color:#475569; margin-bottom:5px; font-size: 0.875rem;'>분석할 종목을 선택하세요 (높은 점수순 정렬):</p>", unsafe_allow_html=True)
            selected_display = st.selectbox("", df['종목표시'].tolist(), label_visibility="collapsed")
            
            if selected_display:
                target_row = df[df['종목표시'] == selected_display].iloc[0]
                total_sc = target_row['적합도 점수']
                tk_name = target_row['종목명']
                
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.markdown(f"<p style='font-weight:600; color:#0f172a; margin-bottom:0; font-size: 0.875rem;'>[{tk_name}] 투자 적기 (조건 부합도)</p>", unsafe_allow_html=True)
                    st.markdown(f"<h1 style='color:#0f172a; font-size:3rem; font-weight:800; letter-spacing:-0.025em; margin-top:0;'>{total_sc}%</h1>", unsafe_allow_html=True)
                
                with col_right:
                    st.markdown(f"""
                    <div class="system-review-box-blue">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/></svg>
                        <b>시스템 한줄평:</b> 이 종목은 오늘 기준으로 투자 철학에 {total_sc}% 만큼 부합합니다.
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
        st.info("실시간 검색 돌리기 버튼을 클릭하시면 전체 시장 스캔 모델이 가동됩니다.")
    
    st.markdown("<br><hr style='border:0; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
    
    with st.expander("적용된 조건 검색식(A~G) 자세히 보기"):
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
    st.markdown("<div class='custom-section-title'>🌍 테마별 핵심 뉴스 브리핑</div>", unsafe_allow_html=True)
    with st.spinner("최신 글로벌 뉴스를 실시간으로 수집 중입니다..."):
        news_data = engine.get_latest_news()
        
    if news_data:
        tabs = st.tabs(list(news_data.keys()))
        for tab, (category, items) in zip(tabs, news_data.items()):
            with tab:
                if items:
                    for item in items:
                        st.markdown(f"- **[{item['source']}]** <a href='{item['link']}' target='_blank' style='text-decoration:none; color:#1D4ED8; font-weight:500;'>{item['title']}</a> <span style='color:#64748b; font-size:0.8rem;'>({item['date']})</span>", unsafe_allow_html=True)
                        if item.get("title_ko") and item.get("title_ko") != "(번역 실패)":
                            st.markdown(f"<div style='margin-left:20px; color:#0f766e; font-size:0.85rem; margin-top: 4px; margin-bottom: 8px;'>🇰🇷 {item['title_ko']}</div>", unsafe_allow_html=True)
                else:
                    st.info("현재 이 카테고리의 최신 뉴스를 불러오지 못했습니다.")
    else:
        st.warning("뉴스 검색 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        
    st.markdown("<br><hr style='border:0; border-top:1px solid #e2e8f0;'><br>", unsafe_allow_html=True)
    
    # 6. 수신 정보 설정
    st.markdown("<div class='custom-section-title'>알람 봇 수신 채널 설정</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569; margin-bottom:20px; font-weight:500;'>이메일 주소나 텔레그램 아이디를 입력해 두시면 분석 리포트를 전송해 드립니다.</p>", unsafe_allow_html=True)
    
    col_em, col_tg = st.columns(2)
    with col_em:
        current_emails = config.get("emails", [])
        email_text_val = "\n".join(current_emails) if current_emails and isinstance(current_emails[0], str) else ""
        emails_str = st.text_area("이메일 주소 (줄바꿈 구분)", value=email_text_val, height=120, placeholder="ceo@company.com")
        config["emails"] = [e.strip() for e in emails_str.split("\n") if e.strip()]
        
    with col_tg:
        current_chat_ids = config.get("telegram", {}).get("chat_ids", [])
        tg_text_val = "\n".join(current_chat_ids) if current_chat_ids and isinstance(current_chat_ids[0], str) else ""
        chat_ids_str = st.text_area("텔레그램 아이디 (줄바꿈 구분)", value=tg_text_val, height=120, placeholder="@your_id")
        bot_token = config.get("telegram", {}).get("bot_token", "")
        config["telegram"] = {"bot_token": bot_token, "chat_ids": [cid.strip() for cid in chat_ids_str.split("\n") if cid.strip()]}
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("수신 설정 저장하기", type="secondary"):
        save_config(config)
        st.success("알림 채널 정보가 성공적으로 저장되었습니다.")
            
    st.markdown("""
    <br><br><br>
    <div style='text-align: center; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 0.875rem;'>
        <b>Disclaimer:</b> 본 분석 시스템은 투자 참고용이며, 최종 투자 판단과 책임은 본인에게 있습니다.<br>
        Copyright © 2026. 프리미엄 주식 분석 & AI 타점 어드바이저. All Rights Reserved.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
