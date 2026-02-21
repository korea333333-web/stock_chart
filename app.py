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
    

    # 1. 헤더 영역 (제목 및 설명: 프리미엄 디자인)
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>✨ 프리미엄 주식 분석 & AI 타점 어드바이저</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 1.1rem;'>📊 대표님의 투자 철학(A~G)을 완벽하게 계량화하여 최적의 매수 타점을 실시간으로 찾아냅니다.</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #10B981; font-size: 1.0rem;'>맨 아래 <b>[수신 설정]</b>에 이메일과 텔레그램 ID를 기입해 두시면 봇이 다른 분들에게도 분석 리포트를 알아서 발송해 드립니다! 🚀</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 1.5 글로벌 & 국내 주요 증시 현황 위젯 추가
    st.subheader("🌎 오늘의 주요 증시 현황")
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
                    <div style='background-color: #FAFAFA; padding: 15px; border-radius: 10px; border: 1px solid #E5E7EB; text-align: center;'>
                        <p style='margin:0; font-size:14px; color:#4B5563; font-weight:600;'>{name}</p>
                        <h3 style='margin:5px 0 0 0; color:#1F2937;'>{data['close']:,.2f}</h3>
                        <p style='margin:5px 0 0 0; font-size:15px; font-weight:bold; color:{txt_color};'>
                            {arrow} {abs(diff_val):,.2f} ({pct_val:.2f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("실시간 증시 데이터를 불러오는 중입니다.")
    except Exception as e:
        st.warning("증시 데이터를 불러오지 못했습니다.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. 검색 시간 정보 표시
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    st.info(f"마지막 데이터 수집 시간: **{current_time}**")
    
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
            st.success("✅ 종목 스캔 완료! (점수순으로 정렬되었습니다)")
            
            # 🟢🟡🔴 직관적인 적합도 점수 상태 가이드라인 (범례)
            st.markdown("""
            <div style='background-color: #F3F4F6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                <b>🛡️ 점수별 투자 가이드라인 (Legend)</b><br>
                <span style='color: green;'>🟢 <b>85점 이상:</b> 당장 분석 후 강력 매수 고려 (조건 완벽 일치)</span> &nbsp;|&nbsp; 
                <span style='color: orange;'>🟡 <b>70점 이상:</b> 좋은 흐름, 분할 매수 및 관심 주시</span> &nbsp;|&nbsp; 
                <span style='color: red;'>🔴 <b>50점 미만:</b> 아직 무르익지 않음 (관망)</span>
            </div>
            """, unsafe_allow_html=True)
            
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
                chart_df_d = target_row['_chart_df']
                chart_df_w = target_row.get('_chart_w', pd.DataFrame())
                chart_df_m = target_row.get('_chart_m', pd.DataFrame())
                markers = target_row['_markers']
                tk_name = target_row['종목명']
                total_sc = target_row['적합도 점수']
                
                # 투자 적기 계산용 (우리의 만점 기준 100점에 대한 달성도)
                # 80점 이상이면 매우 좋음, 60점 이상이면 보통 등
                if total_sc >= 85:
                    timing_status = "🔥 **매우 강력한 투자 적기** (모든 조건 완벽 부합)"
                    color_theme = "normal"
                elif total_sc >= 70:
                    timing_status = "✅ **좋은 투자 적기** (조정장 매수 고려)"
                    color_theme = "normal"
                elif total_sc >= 50:
                    timing_status = "⚠️ **관망 필요** (일부 조건만 부합, 아직 무르익지 않음)"
                    color_theme = "off"
                else:
                    timing_status = "❄️ **투자 부적합** (현재 우리가 원하는 타점이 아님)"
                    color_theme = "inverse"
                
                # 요약 대시보드 표시
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric(label=f"🎯 [{tk_name}] 투자 적기 (조건 부합도)", value=f"{total_sc}%", delta=timing_status, delta_color=color_theme)
                with col2:
                    st.info(f"💡 시스템 한줄평: 이 종목은 오늘 기준으로 대표님의 철학에 **{total_sc}%** 만큼 가까워진 타점입니다.")
                
                if not chart_df_d.empty:
                    # 멀티 프레임 차트 탭 구성
                    tab_daily, tab_weekly, tab_monthly = st.tabs(["📈 단기 흐름 (일봉)", "📊 중기 흐름 (주봉)", "📅 장기 흐름 (월봉)"])
                    
                    # --- 공통 차트 생성 함수 ---
                    def create_candlestick(df_data, title_ext, show_overlay=False):
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=df_data.index, open=df_data['Open'], high=df_data['High'], low=df_data['Low'], close=df_data['Close'], name='주가',
                            increasing_line_color='#EF4444', decreasing_line_color='#3B82F6', # 한국형 점등 (빨강/파랑)
                            increasing_fillcolor='#EF4444', decreasing_fillcolor='#3B82F6'
                        ))
                        # 이동평균선(MA는 일봉에만 제공 중이므로 일봉 탭에만 그림)
                        if show_overlay and 'MA5' in df_data.columns:
                            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA5'], line=dict(color='magenta', width=1.5), name='5일선'))
                            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA20'], line=dict(color='orange', width=1.5), name='20일선'))
                            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA60'], line=dict(color='green', width=1.5), name='60일선'))
                            
                            # 조건 발생 지점 오버레이 마커 (일봉 전용)
                            for condition_key, marker_info in markers.items():
                                m_date, m_price, m_text = marker_info
                                fig.add_annotation(
                                    x=m_date, y=m_price, text=m_text, showarrow=True, arrowhead=2, arrowsize=1.5,
                                    arrowcolor="Black" if condition_key != 'D_Spike' else "Red",
                                    font=dict(color="White", size=12),
                                    bgcolor="Blue" if condition_key == 'C_Low' else ("Red" if condition_key == 'D_Spike' else "Purple"),
                                    bordercolor="Black", borderwidth=1, ay=-40
                                )
                                
                        fig.update_layout(
                            title=f"<b>{tk_name}</b> {title_ext}", yaxis_title="주가 (원)", xaxis_rangeslider_visible=False,
                            template="plotly_white", height=500, margin=dict(l=20, r=20, t=50, b=20)
                        )
                        return fig

                    # 각 탭에 차트 렌더링
                    with tab_daily:
                        st.plotly_chart(create_candlestick(chart_df_d, "단기 150일 (일봉) 차트 및 타점 분석", show_overlay=True), use_container_width=True)
                    with tab_weekly:
                        if not chart_df_w.empty:
                            st.plotly_chart(create_candlestick(chart_df_w, "중기 (주봉) 흐름", show_overlay=False), use_container_width=True)
                        else:
                            st.info("주봉 데이터를 표시할 수 없습니다.")
                    with tab_monthly:
                        if not chart_df_m.empty:
                            st.plotly_chart(create_candlestick(chart_df_m, "장기 (월봉) 흐름", show_overlay=False), use_container_width=True)
                        else:
                            st.info("월봉 데이터를 표시할 수 없습니다.")
                    
                    # 상세 점수 내역 (왜 이 점수를 받았는가?)
                    with st.expander(f"📊 {tk_name} 종목의 총점 {target_row['적합도 점수']}점 획득 내역 자세히 보기", expanded=True):
                        st.markdown("이 종목이 각 카테고리에서 **어떻게 미세 점수를 획득(또는 감점)** 당했는지에 대한 상세 분석 내용입니다.")
                        
                        desc_map = {
                            'A': "주가범위 (1천원~5만원 완벽 시 10점, 5만원 초과 시 차감)",
                            'B': "거래대금 (100억 이상부터 점수 부여, 200억 달성 시 15점 만점)",
                            'C': "바닥 지지력 (저점 대비 안 올랐을수록 15점 만점, 35% 이상부터 0점)",
                            'D': "최근 급등력 (10% 상승부터 점수 부여, 25% 급등 시 15점 만점)",
                            'E': "고점 지지율 (전고점 대비 85% 지지 시 점수 부여, 완벽 지지 시 15점)",
                            'F': "이평선 정배열 (기본 10점 + 5일선 우상향 각도에 따라 최대 +5점 가산)",
                            'G': "5일선 이격도 (95~105% 구간에서 중심(100%)에 오차 없이 완벽 밀착할수록 15점 만점)"
                        }
                        
                        scores_details = target_row.get('_details', {})
                        for key, desc in desc_map.items():
                            status = scores_details.get(key, "미달(0점)")
                            if "Pass" in status:
                                st.success(f"**조건 {key}** [{desc}] ➔ 획득 점수: **{status.replace('Pass', '')}**")
                            else:
                                st.error(f"**조건 {key}** [{desc}] ➔ 획득 점수: 0점 (조건 미달)")
                
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
        
    # ==============================================================
    # 6. 알림 수신 설정 영역 (사이드바에서 화면 최하단으로 이동 및 깔끔하게 개편)
    # ==============================================================
    st.markdown("---")
    st.markdown("<h3 style='color: #4B5563;'>🔔 자동 알림 수신자 설정 (이메일 & 텔레그램)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; margin-bottom: 20px;'>대표님뿐만 아니라 팀원, 지인들도 이 자동 분석 리포트를 받아볼 수 있도록 수신처를 쉽게 관리하세요. (발신 비밀번호 등은 내부에 안전하게 저장되어 숨겨져 있습니다.)</p>", unsafe_allow_html=True)
    
    col_em, col_tg = st.columns(2)
    with col_em:
        st.markdown("**📧 리포트를 받을 이메일 주소**")
        st.caption("작성 예시: `홍길동: hong@gmail.com`")
        
        # 만약 기존에 딕셔너리가 아닌 단순 문자열 리스트로 저장되어 있을 경우를 대비한 파싱 로직
        current_emails = config.get("emails", [])
        if current_emails and isinstance(current_emails[0], str):
            email_text_val = "\n".join(current_emails)
        else:
            email_text_val = ""
            
        emails_str = st.text_area(
            label="이메일 (엔터로 줄바꿈하여 여러 명 입력 가능)", 
            value=email_text_val, 
            height=120,
            label_visibility="collapsed"
        )
        # 그냥 주소만 적어도, 이름: 주소 형태로 적어도 모두 사용 가능하게 처리
        config["emails"] = [e.strip() for e in emails_str.split("\n") if e.strip()]
        
    with col_tg:
        st.markdown("**✈️ 리포트를 받을 텔레그램 ID**")
        st.caption("작성 예시: `김대표: 8367558795`")
        
        current_chat_ids = config.get("telegram", {}).get("chat_ids", [])
        if current_chat_ids and isinstance(current_chat_ids[0], str):
            tg_text_val = "\n".join(current_chat_ids)
        else:
            tg_text_val = ""
            
        chat_ids_str = st.text_area(
            label="텔레그램 ID (엔터로 줄바꿈하여 여러 명 입력 가능)", 
            value=tg_text_val,
            height=120,
            label_visibility="collapsed"
        )
        bot_token = config.get("telegram", {}).get("bot_token", "") # 토큰은 기존 값 그대로 유지 (숨김)
        config["telegram"] = {"bot_token": bot_token, "chat_ids": [cid.strip() for cid in chat_ids_str.split("\n") if cid.strip()]}
        
    # 발신자 정보는 UI 노출 없이 기존 값 그대로 유지
    sender_email = config.get("sender", {}).get("email", "")
    sender_pw = config.get("sender", {}).get("app_password", "")
    config["sender"] = {"email": sender_email, "app_password": sender_pw}
    
    if st.button("💾 위 이메일과 텔레그램 리스트를 최종 수신자로 저장하기", type="primary", use_container_width=True):
        save_config(config)
        st.success("✅ 수신자 명단이 완벽하게 저장되었습니다! 이제 설정된 사람들에게 발송됩니다.")

if __name__ == "__main__":
    main()
