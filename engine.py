import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import warnings

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
        
        # [A조건] 주가범위: 0일전 종가가 1,000원 ~ 50,000원 (10점)
        if 1000 <= current_close <= 50000:
            score += 10
            details['A'] = "Pass"
            pass_points.append('A')
        else:
            details['A'] = "Fail"
            
        # [B조건] 기간내 거래대금: 5일 이내 어느 하루라도 200억 이상 (15점)
        try:
            recent_5 = df.iloc[-5:]
            max_trade_val = (recent_5['Volume'] * recent_5['Close']).max()
            if max_trade_val >= 20_000_000_000:
                score += 15
                details['B'] = "Pass"
                pass_points.append('B')
            else:
                details['B'] = "Fail"
        except:
            details['B'] = "Error"
            
        # [C조건] 기간내 주가위치: 5봉전 포함 이전 20봉 이내 '최저가' 발생 (15점)
        # 즉, 최근 20일 최저가가 최근 5일(0,1,2,3,4봉전)에는 나타나지 않는다 (최저점 찍고 올라오는 중)
        try:
            recent_20_lows = df['Low'].iloc[-20:]
            # 최솟값을 가진 인덱스의 상대적 위치 (0 ~ 19)
            # 19가 가장 최신(0봉전), 0이 19봉전
            min_pos = np.argmin(recent_20_lows)
            if min_pos <= 14: # 0봉~4봉 이전(즉 5봉전 이전)에 최저가
                score += 15
                details['C'] = "Pass"
                pass_points.append('C')
            else:
                details['C'] = "Fail"
        except:
            details['C'] = "Error"
            
        # [D조건] 주가비교: 10봉 이내 15% 이상 상승봉 존재 (15점)
        try:
            recent_10 = df.iloc[-11:] # 어제비교 위해 11개
            spike_found = False
            for i in range(1, len(recent_10)):
                last_c = recent_10['Close'].iloc[i-1]
                curr_h = recent_10['High'].iloc[i]
                if last_c > 0 and (curr_h / last_c) >= 1.15:
                    spike_found = True
                    break
            if spike_found:
                score += 15
                details['D'] = "Pass"
                pass_points.append('D')
            else:
                details['D'] = "Fail"
        except:
            details['D'] = "Error"
            
        # [E조건] 주가비교: 0일전 종가 > 10봉전 고가 * 0.9 (상단 지지) (15점)
        try:
            max_high_10 = df['High'].iloc[-10:].max()
            if current_close > (max_high_10 * 0.9):
                score += 15
                details['E'] = "Pass"
                pass_points.append('E')
            else:
                details['E'] = "Fail"
        except:
             details['E'] = "Error"
             
        # [F조건] 주가이평배열: 5 > 20 > 60 정배열 (15점)
        try:
            ma5 = df['MA5'].iloc[-1]
            ma20 = df['MA20'].iloc[-1]
            ma60 = df['MA60'].iloc[-1]
            if ma5 > ma20 and ma20 > ma60:
                score += 15
                details['F'] = "Pass"
                pass_points.append('F')
            else:
                details['F'] = "Fail"
        except:
             details['F'] = "Error"
             
        # [G조건] 이동평균이격도: 5일선에 98% ~ 102% 이내로 바짝 붙음 (눌림목 타점) (15점)
        try:
            ma5 = df['MA5'].iloc[-1]
            ratio = current_close / ma5
            if 0.98 <= ratio <= 1.02:
                score += 15
                details['G'] = "Pass"
                pass_points.append('G')
            else:
                details['G'] = "Fail"
        except:
             details['G'] = "Error"
             
        pass_str = ",".join(pass_points) if pass_points else "None"
        
        return score, details, current_close, current_chg_pct, pass_str
        
    except Exception as e:
        return 0, {}, 0, 0, "Error"

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
        score, details, price, chg_pct, pass_str = run_strategy(tk)
        
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
                '조건만족': pass_str
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
