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
    

    # --- 시안 기반 커스텀 프리미엄 CSS 주입 ---
    st.markdown("""
    <style>
        /* 기본 폰트 변경 및 전체 배경색 덮어쓰기 (크림색 베이지 톤) */
        html, body, [class*="css"], .stApp {
            font-family: 'Times New Roman', Times, serif !important;
            background-color: #f7f6f2 !important; 
        }
        
        /* 헤더 글로벌 배너 스타일 (Streamlit 경계선을 뚫고 나가는 Full-width 트릭) */
        .premium-header {
            width: 100vw;
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            background-color: #1A3626; /* 딥그린 */
            padding: 50px 20px 60px 20px;
            margin-top: -4rem; /* 기본 여백 상쇄 */
            margin-bottom: 40px;
            text-align: center;
        }
        
        .header-title {
            color: #FFFFFF;
            font-size: 3.2rem;
            font-weight: bold;
            letter-spacing: 1px;
            margin: 0 0 10px 0;
            font-family: 'Times New Roman', Times, serif;
        }
        
        .header-title span.the {
            color: #D4AF37; /* 골드 */
            font-style: italic;
        }
        
        .header-subtitle {
            color: #A3B8A8;
            font-size: 1.1rem;
            font-style: italic;
            margin: 0 0 20px 0;
            letter-spacing: 0.5px;
        }
        
        .header-badge {
            display: inline-block;
            background-color: #234731;
            color: #D4AF37; /* 골드 */
            padding: 6px 18px;
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid #3A5F48;
        }
        
        /* 메인 버튼 스타일 (프리미엄 딥그린) */
        div[data-testid="stButton"] > button {
            background-color: #1A3626 !important;
            color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 5px !important;
            font-weight: bold !important;
            font-family: 'Times New Roman', Times, serif !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #D4AF37 !important;
            color: #1A3626 !important;
            border: 1px solid #1A3626 !important;
        }
        
        /* 섹션 제목 스타일 */
        .section-title {
            color: #1A3626;
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 20px;
            border-bottom: 2px solid #D4AF37; /* 밑줄을 골드 색상으로 */
            padding-bottom: 10px;
            font-family: 'Times New Roman', Times, serif;
        }
        
        /* 메트릭 카드(증시 현황) 등 주요 박스를 흰색으로 빼고 그림자 부여 */
        .market-card {
            background-color: #FFFFFF !important;
            padding: 20px !important;
            border-radius: 12px !important;
            border: 1px solid #EAEAEA !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # 1. 헤더 영역 (시안 기반 딥그린 + 골드 배너)
    st.markdown("""
    <div class="premium-header">
        <div style="font-size: 2rem; color: #D4AF37; margin-bottom: 10px;">🏛️</div>
        <h1 class="header-title"><span class="the">The</span> Premium Stock Advisor</h1>
        <p class="header-subtitle">"An English Library Approach to Market Analysis"</p>
        <div class="header-badge">투자 철학 계량화 & 실시간 타점 분석 시스템</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1.5 글로벌 & 국내 주요 증시 현황 위젯 추가
    st.markdown("<div class='section-title'>📈 Market Overview</div>", unsafe_allow_html=True)
    try:
        indices = engine.get_global_indices()
        if indices:
            i_col1, i_col2, i_col3, i_col4 = st.columns(4)
            for idx, (col, (name, data)) in enumerate(zip([i_col1, i_col2, i_col3, i_col4], indices.items())):
                with col:
                    diff_val = data['diff']
                    pct_val = data['pct']
                    if diff_val > 0:
                        txt_color = "#EF4444" # 빨강 (한국형 상승)
                        arrow = "▲"
                    elif diff_val < 0:
                        txt_color = "#3B82F6" # 파랑 (한국형 하락)
                        arrow = "▼"
                    else:
                        txt_color = "#6B7280" # 회색 (보합)
                        arrow = "-"
                        
                    st.markdown(f"""
                    <div class='market-card'>
                        <p style='margin:0; font-size:14px; color:#6B7280; font-weight:600; letter-spacing:1px;'>{name}</p>
                        <h3 style='margin:10px 0; color:#111827; font-size:1.8rem;'>{data['close']:,.2f}</h3>
                        <p style='margin:0; font-size:14px; font-weight:bold; color:{txt_color};'>
                            {arrow} {abs(diff_val):,.2f} ({pct_val:.2f}%) <span>Since Open</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("실시간 증시 데이터를 불러오는 중입니다.")
    except Exception as e:
        st.warning("증시 데이터를 불러오지 못했습니다.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. 실시간 주식 데이터 검색 (엔진 연동)
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown("<div class='section-title' style='margin-bottom: 0px; border: none; padding: 0;'>🔍 Real-time Analysis</div>", unsafe_allow_html=True)
    with col_btn:
        start_search = st.button("🚀 SCAN MARKET", type="primary", use_container_width=True)
        
    if start_search:
        st.info("Scanning Top Market Cap Stocks... Please wait.")
        
        # 진행 상태를 표시할 빈 공간(영역) 생성
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 콜백 함수: 엔진이 종목 하나를 분석할 때마다 이 함수를 눌러서 화면 갱신
        def update_progress(current, total, current_ticker_name):
            percent = int((current / total) * 100)
            progress_bar.progress(percent)
            status_text.text(f"Scanning... {current}/{total} (Analyzing: {current_ticker_name})")
            
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
            st.markdown("""
            <div style='background-color: #F8F9FA; border-left: 4px solid #D4AF37; padding: 10px 15px; margin-bottom: 20px;'>
                <b style='color: #1A3626;'>Analysis Complete</b><br>
                <span style='color: #6B7280; font-size: 14px;'>Stocks are sorted by compatibility score based on your investment philosophy.</span>
            </div>
            """, unsafe_allow_html=True)
            
            # 🟢🟡🔴 직관적인 적합도 점수 상태 가이드라인 (범례) - 영문 시안 버전 적용
            st.markdown("""
            <div style='background-color: #FFFFFF; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #EAEAEA; box-shadow: 0 2px 5px rgba(0,0,0,0.02);'>
                <p style='margin: 0 0 10px 0; font-size: 13px; font-weight: bold; color: #1A3626;'>📜 SCORE LEGEND</p>
                <span style='color: #065F46; font-weight: bold;'>◆ 85+</span> <span style='color:#555; font-size:14px;'>Strong Buy</span> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
                <span style='color: #D4AF37; font-weight: bold;'>◆ 70+</span> <span style='color:#555; font-size:14px;'>Accumulate</span> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
                <span style='color: #991B1B; font-weight: bold;'>◆ &lt; 50</span> <span style='color:#555; font-size:14px;'>Hold / Watch</span>
            </div>
            """, unsafe_allow_html=True)
            
            # ========================================================
            # 표 렌더링 (Custom HTML Table to match the exact mockup design)
            # ========================================================
            table_html = """
            <style>
            .premium-table { width: 100%; border-collapse: collapse; font-family: 'Times New Roman', serif; font-size: 14px; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .premium-table th { background-color: #1A3626; color: white; padding: 12px 15px; text-align: left; font-weight: normal; letter-spacing: 1px; font-size: 12px; }
            .premium-table td { padding: 12px 15px; border-bottom: 1px solid #F0F0F0; color: #333; vertical-align: middle; }
            .premium-table tr:last-child td { border-bottom: none; }
            .score-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-weight: bold; border: 1px solid #CCC; color: #555; }
            .score-high { color: #065F46; border-color: #065F46; background-color: #E8F5E9; }
            .score-mid { color: #92400E; border-color: #D4AF37; background-color: #FEF3C7; }
            .score-low { color: #991B1B; border-color: #991B1B; background-color: #FEE2E2; }
            .cond-badge { display: inline-block; background-color: #F8F9FA; border: 1px solid #E5E7EB; color: #6B7280; padding: 2px 7px; border-radius: 3px; font-size: 11px; margin-right: 4px; }
            </style>
            <table class="premium-table">
            <thead>
                <tr>
                    <th>CODE</th>
                    <th>NAME</th>
                    <th>PRICE (KRW)</th>
                    <th>CHANGE</th>
                    <th>OP. PROFIT</th>
                    <th>MARKET CAP</th>
                    <th>SCORE</th>
                    <th>CONDITIONS</th>
                </tr>
            </thead>
            <tbody>
            """
            for idx, row in df.iterrows():
                score = row['적합도 점수']
                if score >= 85: score_class = "score-high"
                elif score >= 70: score_class = "score-mid"
                else: score_class = "score-low"
                
                change_val = row['등락률(%)']
                if change_val > 0: change_str = f"<span style='color: #EF4444; font-weight: bold;'>{change_val:.2f}%</span>"
                elif change_val < 0: change_str = f"<span style='color: #3B82F6; font-weight: bold;'>{change_val:.2f}%</span>"
                else: change_str = f"<span style='color: #6B7280;'>0.00%</span>"
                
                cond_str = ""
                for c in row['조건만족'].split(','):
                    if c.strip() != 'None':
                        cond_str += f"<span class='cond-badge'>{c.strip()}</span>"
                
                table_html += f"""
                <tr>
                    <td style='color: #888;'>{row['종목코드']}</td>
                    <td style='font-weight: bold; color: #111;'>{row['종목명']}</td>
                    <td>{row['현재가(원)']:,.0f}</td>
                    <td>{change_str}</td>
                    <td style='color: #999;'>Pending</td>
                    <td>{int(row['시가총액(억)']):,}</td>
                    <td><span class='score-badge {score_class}'>{score:.1f}</span></td>
                    <td>{cond_str}</td>
                </tr>
                """
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
            
            # 발송 테스트 연동용 코드 (나중에 자동화 시 활용)
            high_score_items = df[df['적합도 점수'] >= 90]
            if not high_score_items.empty and st.button("🔔 90점 이상 종목 알림 발송하기 (수동)"):
                st.info("이 기능은 4단계 자동화에서 완벽하게 통합될 예정입니다!", icon="ℹ️")
                
            st.markdown("---")
            
            # ========================================================
            # Deep Dive Analysis UI (시안 완벽 매칭 2단 레이아웃)
            # ========================================================
            st.markdown("""
            <div style='display: flex; align-items: center; margin-top: 40px; margin-bottom: 20px;'>
                <div class='section-title' style='margin-bottom: 0px; border: none; padding: 0;'>📊 Deep Dive Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            
            df['종목표시'] = df['종목명'] + " (Score: " + df['적합도 점수'].astype(str) + ")"
            
            # 전체를 좌우 1:2 비율로 나눔
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #333; margin-bottom: 5px; letter-spacing: 1px;'>SELECT STOCK</p>", unsafe_allow_html=True)
                selected_display = st.selectbox("", df['종목표시'].tolist(), label_visibility="collapsed")
                
                if selected_display:
                    target_row = df[df['종목표시'] == selected_display].iloc[0]
                    total_sc = target_row['적합도 점수']
                    
                    # 딥그린 컴패티빌리티 스코어 박스
                    st.markdown(f"""
                    <div style='background-color: #1A3626; color: white; padding: 25px 20px; border-radius: 8px; margin-top: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); position: relative; overflow: hidden;'>
                        <p style='margin: 0; font-size: 11px; font-weight: normal; letter-spacing: 1px; color: #A3B8A8;'>COMPATIBILITY SCORE</p>
                        <h2 style='margin: 10px 0; font-size: 3rem; color: #FFFFFF;'>{total_sc}<span style='color: #D4AF37; font-size: 1.5rem;'>%</span></h2>
                        <div style='width: 30px; border-top: 2px solid #D4AF37; margin-bottom: 15px;'></div>
                        <p style='margin: 0; font-size: 13px; color: #E5E7EB; line-height: 1.5;'>
                            "Based on your criteria, this asset is currently showing a strong alignment with your portfolio strategy."
                        </p>
                        <div style='position: absolute; right: -20px; bottom: -20px; font-size: 8rem; opacity: 0.05;'>🎯</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 시스템 평가 (체크리스트)
                    st.markdown("""
                    <div style='background-color: #F8F9FA; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #EAEAEA;'>
                        <p style='margin: 0 0 15px 0; font-size: 12px; font-weight: bold; color: #1A3626; letter-spacing: 1px;'>☑ SYSTEM EVALUATION</p>
                    """, unsafe_allow_html=True)
                    
                    details = target_row.get('_details', {})
                    check_list_html = ""
                    # 주요 조건 3개만 샘플 노출
                    key_map = {'A': 'Price Range Condition', 'B': 'Volume Threshold', 'D': 'Momentum (Spike)'}
                    for k, label in key_map.items():
                        status = details.get(k, "")
                        if "Pass" in status:
                            check_list_html += f"<p style='margin: 8px 0; color: #333; font-size: 14px;'><span style='color: #065F46;'>✔</span> {label} <span style='color:#888; font-size:12px;'>({status.replace('Pass', '')})</span></p>"
                        else:
                            check_list_html += f"<p style='margin: 8px 0; color: #999; font-size: 14px;'><span style='color: #EF4444;'>✘</span> {label}</p>"
                            
                    st.markdown(check_list_html + """
                        <hr style='border: none; border-top: 1px solid #EAEAEA; margin: 15px 0;'>
                        <button style='width: 100%; background: transparent; border: 1px solid #CCC; padding: 8px; border-radius: 4px; color: #333; font-size: 11px; font-weight: bold; letter-spacing: 1px;'>VIEW FULL CHECKLIST</button>
                    </div>
                    """, unsafe_allow_html=True)
                    
            with col_right:
                if selected_display:
                    tk_name = target_row['종목명']
                    chart_df_d = target_row['_chart_df']
                    chart_df_w = target_row.get('_chart_w', pd.DataFrame())
                    chart_df_m = target_row.get('_chart_m', pd.DataFrame())
                    markers = target_row['_markers']
                    
                    if not chart_df_d.empty:
                        # 차트 타이틀을 탭과 통합
                        st.markdown(f"""
                        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px; margin-top: 25px;'>
                            <h3 style='margin: 0; color: #333; font-size: 1.2rem;'>Technical Chart: {tk_name}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        tab_daily, tab_weekly, tab_monthly = st.tabs(["Daily", "Weekly", "Monthly"])
                        
                        def create_candlestick(df_data, show_overlay=False):
                            fig = go.Figure()
                            fig.add_trace(go.Candlestick(
                                x=df_data.index, open=df_data['Open'], high=df_data['High'], low=df_data['Low'], close=df_data['Close'], name='Price',
                                increasing_line_color='#1A3626', decreasing_line_color='#D4AF37', # 시안 느낌의 고급 배색 (딥그린/골드)
                                increasing_fillcolor='#1A3626', decreasing_fillcolor='#D4AF37'
                            ))
                            if show_overlay and 'MA5' in df_data.columns:
                                fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA20'], line=dict(color='#D4AF37', width=2), name='MA20'))
                            
                            fig.update_layout(
                                yaxis_title="", xaxis_rangeslider_visible=False,
                                template="plotly_white", height=450, margin=dict(l=0, r=0, t=10, b=0),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                hovermode='x unified'
                            )
                            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                            return fig

                        with tab_daily:
                            st.plotly_chart(create_candlestick(chart_df_d, show_overlay=True), use_container_width=True)
                        with tab_weekly:
                            if not chart_df_w.empty:
                                st.plotly_chart(create_candlestick(chart_df_w, show_overlay=False), use_container_width=True)
                        with tab_monthly:
                            if not chart_df_m.empty:
                                st.plotly_chart(create_candlestick(chart_df_m, show_overlay=False), use_container_width=True)
                
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
        
    # ==============================================================
    # 5.5 주요 글로벌/국내 경제 뉴스 클리핑 영역
    # ==============================================================
    st.markdown("---")
    st.markdown("<h3 style='color: #4B5563;'>📰 오늘의 주요 경제/증시 뉴스 (국내 및 외신 큐레이션)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>한국과 미국의 핵심 뉴스를 국내 언론 시각과 유력 외신(NYT 등) 시각으로 나누어 엄선된 5개씩 제공합니다.</p>", unsafe_allow_html=True)
    
    with st.spinner("최신 글로벌 뉴스를 실시간으로 수집하고 있습니다... (약 1~2초 소요)"):
        news_data = engine.get_latest_news()
        
    if news_data:
        # 뉴스 카테고리별로 탭 생성
        tabs = st.tabs(list(news_data.keys()))
        for tab, (category, items) in zip(tabs, news_data.items()):
            with tab:
                if items:
                    for item in items:
                        # 번역본이 존재하는 외신 기사일 경우 처리
                        ko_title_html = ""
                        translated_text = item.get("title_ko", "")
                        if translated_text and translated_text != "(번역 실패)":
                            ko_title_html = f"<div style='margin-left:5px; color:#2563EB; font-weight:bold; font-size:0.95rem;'>🇰🇷 {translated_text}</div>"
                            
                        # 깔끔한 하이퍼링크 리스트 형태로 출력
                        st.markdown(f"""
                        <div style='margin-bottom: 12px;'>
                            🏢 **[{item['source']}]** &nbsp;&nbsp; 
                            <a href='{item['link']}' target='_blank' style='text-decoration:none; color:#1F2937; font-weight:500;'>{item['title']}</a> 
                            &nbsp;&nbsp; <span style='color:#9CA3AF; font-size:0.8rem;'>{item['date']}</span>
                            {ko_title_html}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("현재 시간 기준으로 관련 최신 뉴스를 불러오지 못했습니다.")
    else:
        st.warning("뉴스 검색 서버 상태가 불안정합니다.")
        
    # ==============================================================
    # 6. 알림 수신 설정 영역 (Concierge Notifications - Design match)
    # ==============================================================
    st.markdown("""
    <style>
    .concierge-section {
        background-color: #1A3626;
        padding: 40px;
        border-radius: 8px;
        margin-top: 50px;
        margin-bottom: 30px;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .concierge-title {
        color: #D4AF37;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
        font-family: 'Times New Roman', Times, serif;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .concierge-desc {
        color: #E5E7EB;
        font-size: 0.95rem;
        margin-bottom: 30px;
        line-height: 1.6;
    }
    .footer-block {
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        background-color: #1A3626;
        padding: 40px 20px;
        text-align: center;
        margin-top: 50px;
        margin-bottom: -100px;
    }
    .footer-text {
        color: #A3B8A8;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    .footer-quote {
        color: #D4AF37;
        font-style: italic;
        margin-bottom: 15px;
    }
    /* 텍스트 영역 테마 덮어쓰기 (다크 그린 배경용) */
    .dark-inputs div[data-testid="stTextArea"] textarea {
        background-color: #11281A !important;
        color: white !important;
        border: 1px solid #3A5F48 !important;
    }
    .dark-inputs label {
        color: #D4AF37 !important;
        font-family: 'Times New Roman', Times, serif !important;
        letter-spacing: 1px;
    }
    </style>
    <div class="concierge-section">
        <div class="concierge-title">
            <span style="background-color:#D4AF37; color:#1A3626; padding:5px 8px; border-radius:5px; font-size:1.2rem;">🔔</span> 
            Concierge Notifications
        </div>
        <div class="concierge-desc">
            Securely configure your dispatch channels. Your analysis reports will be delivered with the discretion and reliability of a private courier.
        </div>
    """, unsafe_allow_html=True)
    
    # 이 입력 칸들이 dark-inputs 클래스의 영향을 받게 하려면 Streamlit 컨테이너를 직접 쓸 수밖에 없음
    # CSS에서 부모/형제 결합자를 통해 스타일을 덮어씀 (위 style 태그 참고)
    st.markdown('<div class="dark-inputs">', unsafe_allow_html=True)
    
    col_em, col_tg = st.columns(2)
    with col_em:
        st.markdown("**✉ EMAIL ADDRESS**", unsafe_allow_html=True)
        # 만약 기존에 딕셔너리가 아닌 단순 문자열 리스트로 저장되어 있을 경우를 대비한 파싱 로직
        current_emails = config.get("emails", [])
        if current_emails and isinstance(current_emails[0], str):
            email_text_val = "\n".join(current_emails)
        else:
            email_text_val = ""
            
        emails_str = st.text_area(
            label="EMAIL ADDRESS", 
            value=email_text_val, 
            height=80,
            placeholder="e.g. your.name@domain.com",
            label_visibility="collapsed"
        )
        # 그냥 주소만 적어도, 이름: 주소 형태로 적어도 모두 사용 가능하게 처리
        config["emails"] = [e.strip() for e in emails_str.split("\n") if e.strip()]
        
    with col_tg:
        st.markdown("**✈ TELEGRAM ID**", unsafe_allow_html=True)
        current_chat_ids = config.get("telegram", {}).get("chat_ids", [])
        if current_chat_ids and isinstance(current_chat_ids[0], str):
            tg_text_val = "\n".join(current_chat_ids)
        else:
            tg_text_val = ""
            
        chat_ids_str = st.text_area(
            label="TELEGRAM ID", 
            value=tg_text_val,
            height=80,
            placeholder="e.g. @username",
            label_visibility="collapsed"
        )
        bot_token = config.get("telegram", {}).get("bot_token", "") # 토큰은 기존 값 그대로 유지 (숨김)
        config["telegram"] = {"bot_token": bot_token, "chat_ids": [cid.strip() for cid in chat_ids_str.split("\n") if cid.strip()]}
        
    # CSS div 닫기
    st.markdown("</div>", unsafe_allow_html=True)

    col_empty, col_save = st.columns([3, 1])
    with col_save:
        if st.button("💾 Save Preferences", type="primary", use_container_width=True):
            save_config(config)
            st.success("Preferences Saved Successfully.")
            
    # CSS div 닫기 (concierge-section 구역 종료)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 7. 푸터 구역 (Footer)
    st.markdown("""
    <div class="footer-block">
        <div style="font-size: 2rem; color: #D4AF37; margin-bottom: 10px;">🏛️</div>
        <p class="footer-quote">"Trust is the currency of the gentleman's market."</p>
        <p class="footer-text">
            © 2026 The Premium Stock Advisor. All rights reserved.<br>
            This service serves as a reference for investment judgment, and the actual responsibility for investment lies with the investor.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
