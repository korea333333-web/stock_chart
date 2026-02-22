import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import warnings
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
from deep_translator import GoogleTranslator

warnings.filterwarnings('ignore')

def get_candidate_tickers(date_str=None):
    """
    FinanceDataReader를 활용하여 KOSPI, KOSDAQ 시장에서 시가총액 500억 이상인 종목의 
    종목코드와 종목명, 시가총액(억) 목록 데이터프레임을 리턴합니다.
    """
    try:
        # FinanceDataReader 한국 증시 (KRX) 전체 종목 리스트 
        df = fdr.StockListing('KRX')
        
        # 'Code', 'Market', 'Marcap' (시가총액, 원), 'Name' 등 컬럼 존재
        # KOSPI, KOSDAQ 종목만 취합
        df_filtered = df[(df['Market'].str.contains('KOSPI') | df['Market'].str.contains('KOSDAQ'))]
        
        # 시가총액 500억 = 50,000,000,000 원
        df_filtered = df_filtered[df_filtered['Marcap'] >= 50000000000].copy()
        
        # 종목코드 코드를 인덱스로
        df_filtered = df_filtered.set_index('Code')
        
        # 종목코드별 시가총액 억 단위로 변환해 새 컬럼에 넣기
        df_filtered['시가총액(억)'] = df_filtered['Marcap'] // 100000000
        
        return df_filtered
    except Exception as e:
        print(f"시가총액 데이터 수집 실패: {e}")
        return pd.DataFrame()

def get_global_indices():
    """
    KOSPI(KS11), KOSDAQ(KQ11), S&P500(US500), NASDAQ(IXIC) 
    4개 주요 글로벌 지수의 최근 등락 정보를 가져옵니다.
    """
    indices = {
        'KOSPI': 'KS11',
        'KOSDAQ': 'KQ11',
        'S&P 500': 'US500', 
        'NASDAQ': 'IXIC'
    }
    
    results = {}
    today = datetime.today()
    start_date = today - timedelta(days=7) # 주말/휴일 고려 7일치
    
    for name, code in indices.items():
        try:
            df = fdr.DataReader(code, start_date, today)
            if len(df) >= 2:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                results[name] = {"close": curr, "diff": diff, "pct": pct}
            else:
                results[name] = {"close": 0, "diff": 0, "pct": 0}
        except Exception as e:
            results[name] = {"close": 0, "diff": 0, "pct": 0}
            
    return results

def get_latest_news():
    """Google News RSS를 활용하여 주요 키워드별 최신 기사를 5개씩 가져옵니다."""
    results = {}
    
    # 카테고리별 검색어 (검색어, hl, gl, ceid) - 주요 기사 및 퀄리티 위주로 큐레이션 개선
    queries = {
        "🇰🇷 국내 증시 주요뉴스": ("국내 증시 주요뉴스 OR 코스피 시황", "ko", "KR", "KR:ko"),
        "🇰🇷 국내 경제 핫이슈": ("한국 경제 주요기사 OR 경제 동향", "ko", "KR", "KR:ko"),
        "🇺🇸 글로벌 증시 마감/시황": ("미국 증시 주요뉴스 OR 뉴욕증시 마감", "ko", "KR", "KR:ko"),
        "🇺🇸 연준/금리/거시경제": ("Fed 금리 주요뉴스 OR 연준 미국 경제", "ko", "KR", "KR:ko"),
        "🌎 글로벌 경제 오피니언 (외신)": ("global economy major news OR Wall Street stock market analysis", "en-US", "US", "US:en")
    }
    
    # SSL 우회 설정 (특정 환경 오류 방지)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    import requests
    for title, (q, hl, gl, ceid) in queries.items():
        encoded_q = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid={ceid}"
        
        try:
            # RSS 크롤링 안정성 확보를 위한 세션 및 헤더 위장
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/'
            }
            # Timeout을 넉넉하게 7초로 설정하고, verify=False 로 SSL 깐깐함 완화
            res = session.get(url, headers=headers, timeout=7, verify=False)
            res.raise_for_status() # 400, 500 에러 발생 시 except로 던짐
            
            root = ET.fromstring(res.text)
            translator = GoogleTranslator(source='auto', target='ko')
            
            items = []
            for item in root.findall('.//item')[:5]: # 기사는 딱 5개만 제한
                news_title = item.find('title').text
                news_link = item.find('link').text
                
                # 출처(source) 요소 찾기
                source_node = item.find('source')
                source_name = source_node.text if source_node is not None else "Unknown"
                
                # 퍼블리시 시간
                pub_date = item.find('pubDate')
                pub_text = pub_date.text if pub_date is not None else ""
                
                # ' - 출처' 형태가 제목에 붙어있는 경우 정리
                if f" - {source_name}" in news_title:
                    news_title = news_title.replace(f" - {source_name}", "")
                    
                # [추가] 외신 채널의 경우 한국어 번역본 제공
                translated_title = ""
                if "외신" in title or "US" in gl:
                    try:
                        translated_title = translator.translate(text=news_title)
                    except Exception as trans_e:
                        translated_title = "(번역 실패)"
                        
                items.append({
                    "title": news_title, 
                    "title_ko": translated_title,
                    "link": news_link, 
                    "source": source_name, 
                    "date": pub_text
                })
            
            results[title] = items
        except Exception as e:
            print(f"Error fetching news for {title}: {e}")
            results[title] = [] # 에러 시 빈 리스트
            
    return results

def run_strategy(ticker, today=None):
    """
    단일 종목에 대해 A~G 조건을 평가하여 점수(score, 100점 만점)와 
    세부 내역(details), 현재가 등의 기본 정보를 리턴합니다.
    """
    if today is None:
        today = datetime.today()
        
    start_date = today - timedelta(days=150) # MA60 여유 있게 구하기 위해 150일 분량 조회
    
    try:
        # fdr로 데이터 수집
        df = fdr.DataReader(ticker, start_date, today)
        if len(df) < 60:
            return 0, {}, 0, 0 # 데이터 너무 적음
            
        # 이평선 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 최신 데이터
        current_close = int(df['Close'].iloc[-1])
        # 등락률 계산 (전일 종가 대비)
        prev_close = int(df['Close'].iloc[-2])
        # 혹시 0 분모 에러 방지
        current_chg_pct = round(((current_close - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0
        
        score = 0
        details = {}
        pass_points = []
        markers = {}  # 차트 오버레이(표시)용 이벤트 좌표 저장
        
        # [A조건] 주가범위: 0일전 종가가 1,000원 ~ 50,000원 (10점 만점)
        if 1000 <= current_close:
            pct_score = min(10, 10 - ((current_close - 50000)/5000) if current_close > 50000 else 10)
            if pct_score > 0:
                score += pct_score
                details['A'] = f"Pass({pct_score:.1f}점)"
                pass_points.append('A')
            else:
                details['A'] = "Fail"
        else:
            details['A'] = "Fail"
            
        # [B조건] 기간내 거래대금: 5일 이내 200억 이상 유무 (15점 만점)
        # 200억을 넘는 비율에 따라 최대 15점까지 가중치 부여
        try:
            recent_5 = df.iloc[-5:]
            trade_vals = recent_5['Volume'] * recent_5['Close']
            max_trade_val = trade_vals.max()
            max_date = trade_vals.idxmax()
            
            if max_trade_val >= 10_000_000_000: # 최소 100억부터 점수 인정 시작
                ratio = min(1.0, max_trade_val / 20_000_000_000)
                b_score = 15.0 * ratio
                score += b_score
                details['B'] = f"Pass({b_score:.1f}점)"
                pass_points.append('B')
                markers['B_Vol'] = (max_date, recent_5.loc[max_date, 'Close'], "최대거래량")
            else:
                details['B'] = "Fail"
        except:
            details['B'] = "Error"
            
        # [C조건] 기간내 주가위치: 5봉전 20봉 이내 '최저가' (15점 만점)
        # 최저점 대비 현재가가 얼마나 올라왔는지(너무 많이 오르지 않아야 고득점)
        try:
            recent_20_lows = df['Low'].iloc[-25:-5] # 정확히 5봉전~25봉전 사이의 데이터
            min_val = recent_20_lows.min()
            min_date = recent_20_lows.idxmin()
            
            # 현재가가 바닥 대비 30% 이내에 머물러 있을 때 점수 부여 (바닥권 횡보 확인)
            rise_ratio = (current_close - min_val) / min_val
            if rise_ratio <= 0.35: 
                c_score = 15.0 * (1.0 - (rise_ratio / 0.35))
                score += c_score
                details['C'] = f"Pass({c_score:.1f}점)"
                pass_points.append('C')
                markers['C_Low'] = (min_date, min_val, "기간최저가")
            else:
                details['C'] = "Fail(너무오름)"
        except:
            details['C'] = "Error"
            
        # [D조건] 주가비교: 10봉 이내 15% 이상 상승봉 (15점 만점)
        # 상승 조건의 크기가 클수록 고득점 계산
        try:
            recent_11 = df.iloc[-11:] 
            max_spike = 0
            spike_date = None
            spike_price = 0
            
            for i in range(1, len(recent_11)):
                last_c = recent_11['Close'].iloc[i-1]
                curr_h = recent_11['High'].iloc[i]
                if last_c > 0:
                    spike_pct = curr_h / last_c
                    if spike_pct > max_spike:
                        max_spike = spike_pct
                        spike_date = recent_11.index[i]
                        spike_price = curr_h
                        
            if max_spike >= 1.10: # 10% 이상부터 부분 점수, 25%면 만점
                score_ratio = min(1.0, (max_spike - 1.10) / 0.15)
                d_score = 15.0 * score_ratio
                score += d_score
                details['D'] = f"Pass({d_score:.1f}점)"
                pass_points.append('D')
                if max_spike >= 1.15:
                    markers['D_Spike'] = (spike_date, spike_price, f"{((max_spike-1)*100):.1f}%급등")
            else:
                details['D'] = "Fail"
        except:
            details['D'] = "Error"
            
        # [E조건] 주가상단 지지 여부: 0일전 종가 > 10봉 고가 * 0.9 (15점 만점)
        try:
            max_high_10 = df['High'].iloc[-10:].max()
            retention_ratio = current_close / max_high_10
            if retention_ratio > 0.85: # 85% 이상 지지부터 부분 점수 
                e_score = 15.0 * min(1.0, (retention_ratio - 0.85) / 0.15)
                score += e_score
                details['E'] = f"Pass({e_score:.1f}점)"
                pass_points.append('E')
            else:
                details['E'] = "Fail"
        except:
             details['E'] = "Error"
             
        # [F조건] 주가이평배열: 5 > 20 > 60 가중치 점수 (15점 만점)
        # 이평선 역배열이어도 5일선이 고개를 들고 각도가 가파르면 점수 부여 (각도 계산)
        try:
            ma5 = df['MA5'].iloc[-1]
            ma20 = df['MA20'].iloc[-1]
            ma60 = df['MA60'].iloc[-1]
            
            # 5일선 3일 전 대비 상승 각도(비율)
            ma5_prev = df['MA5'].iloc[-4]
            ma5_angle = (ma5 - ma5_prev) / ma5_prev * 100
            
            f_score = 0
            if ma5 > ma20 and ma20 > ma60:
                f_score += 10 # 기본 정배열 점수
            if ma5_angle > 0: # 5일선이 위로 꺾임 (각도 가산점 최대 5점)
                f_score += min(5.0, ma5_angle) 
                
            if f_score > 0:
                score += f_score
                details['F'] = f"Pass({f_score:.1f}점)"
                pass_points.append('F')
            else:
                details['F'] = "Fail"
        except:
             details['F'] = "Error"
             
        # [G조건] 이동평균이격도: 5일선에 98% ~ 102% 이내로 바짝 붙음 (15점 만점)
        # 1.0(100%)에 완벽하게 일치할수록 15점 만점, 멀어질수록 깎임
        try:
            ma5 = df['MA5'].iloc[-1]
            ratio = current_close / ma5
            diff_from_center = abs(1.0 - ratio) # 0에 가까울수록 완벽
            
            if diff_from_center <= 0.05: # 95% ~ 105% 사이면 점수 배분
                g_score = 15.0 * (1.0 - (diff_from_center / 0.05))
                score += g_score
                details['G'] = f"Pass({g_score:.1f}점)"
                pass_points.append('G')
                markers['G_MA5'] = (df.index[-1], current_close, "5일선 밀착")
            else:
                details['G'] = "Fail"
        except:
             details['G'] = "Error"
             
             
        pass_str = ",".join(pass_points) if pass_points else "None"
        
        # 주식 차트 멀티 프레임을 위한 주봉(Weekly), 월봉(Monthly) 데이터 리샘플링 생성
        df_weekly = df.resample('W-Fri').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
        df_monthly = df.resample('M').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
        
        return round(score, 1), details, current_close, current_chg_pct, pass_str, df, df_weekly, df_monthly, markers
        
    except Exception as e:
        return 0, {}, 0, 0, "Error", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def scan_hot_stocks(limit=50, progress_callback=None):
    """
    개발 편의를 위해 전체 종목 중 거래대금 상위 종목 일부만 샘플링하여 
    빠르게 엔진을 테스트하는 함수입니다. (시가총액 500억 이상 기본 조건)
    """
    df_cap = get_candidate_tickers()
    if df_cap.empty:
        return pd.DataFrame()
        
    # 시간 절약을 위해 시가총액 상위 일부 종목만 테스트 진행
    tickers = list(df_cap.index)[:limit]
    results = []
    
    # fdr로 종목 이름 맵핑 
    # df_cap 안의 'Name' 컬럼 활용
    names_dict = df_cap['Name'].to_dict()
    
    for i, tk in enumerate(tickers):
        score, details, price, chg_pct, pass_str, df_chart, df_w, df_m, markers = run_strategy(tk)
        
        name = names_dict.get(tk, tk)
        
        if score > 0:
            market_cap_100m = df_cap.loc[tk, '시가총액(억)'] if tk in df_cap.index else 0
            
            results.append({
                '종목코드': tk,
                '종목명': name,
                '현재가(원)': price,
                '등락률(%)': chg_pct,
                '영업이익(억)': '실시간계산대기',
                '시가총액(억)': market_cap_100m,
                '적합도 점수': score,
                '조건만족': pass_str,
                '_chart_df': df_chart,         # 일별(단기) 차트
                '_chart_w': df_w,              # 주별(중기) 차트
                '_chart_m': df_m,              # 월별(장기) 차트
                '_markers': markers,           # 오버레이 마커용 
                '_details': details            # 점수 산정 세부 내역 
            })
            
        if progress_callback:
            progress_callback(i + 1, len(tickers), name)
            
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by='적합도 점수', ascending=False).reset_index(drop=True)
    return df_res

if __name__ == "__main__":
    print("엔진 테스트 시작... 시가총액 상위 50개 종목을 대상으로 A~G 필터링을 1차 검증합니다.")
    df_result = scan_hot_stocks(limit=50)
    print("\n[검증 완료 - 고득점 종목 탑 5]")
    print(df_result.head(5))
