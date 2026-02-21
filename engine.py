import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from pykrx import stock
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def get_candidate_tickers(date_str=None):
    """
    지정일 기준 KOSPI, KOSDAQ 시장에서 시가총액 500억 이상인 종목의 
    종목코드와 종목명, 시가총액(억) 목록 데이터프레임을 리턴합니다.
    """
    if date_str is None:
        # 주말인 경우를 대비해 가장 최근 영업일 (보통 fdr.StockListing을 쓰거나 pykrx의 가장 최근 영업일 사용)
        t = datetime.today()
        # 주말 피하기
        if t.weekday() == 5: t = t - timedelta(days=1)
        elif t.weekday() == 6: t = t - timedelta(days=2)
        date_str = t.strftime("%Y%m%d")
        
    try:
        df_kospi = stock.get_market_cap_by_ticker(date_str, market="KOSPI")
        df_kosdaq = stock.get_market_cap_by_ticker(date_str, market="KOSDAQ")
        df_cap = pd.concat([df_kospi, df_kosdaq])
        
        # 500억 = 50,000,000,000 원
        df_filtered = df_cap[df_cap['시가총액'] >= 50000000000]
        
        # 종목코드, 시가총액 억 단위로 변환
        result_df = df_filtered.copy()
        result_df['시가총액(억)'] = result_df['시가총액'] // 100000000
        
        return result_df
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

def scan_hot_stocks(limit=50):
    """
    개발 편의를 위해 전체 종목 중 거래대금 상위 종목 일부만 샘플링하여 
    빠르게 엔진을 테스트하는 함수입니다. (시가총액 500억 이상 기본 조건)
    """
    df_cap = get_candidate_tickers()
    if df_cap.empty:
        return pd.DataFrame()
        
    # pykrx의 정보 중 하나인 거래대금으로 정렬해서 "살아있는" 상위 50~100 종목만 뽑아 테스트 시간 단축
    # 오늘은 간단하게 테스트 목적이므로 그냥 랜덤이나 시가총액 상위로 일부 추출합니다. (나중엔 전체)
    # 실제로는 전체 df_cap.index.tolist() 에 돌리되, 시간상 상위 N개만 진행.
    tickers = list(df_cap.index)[:limit]
    
    results = []
    
    # fdr로 종목 이름 가져오기
    krx_names = fdr.StockListing('KRX')[['Code', 'Name']].set_index('Code')['Name'].to_dict()
    
    for tk in tickers:
        score, details, price, chg_pct, pass_str = run_strategy(tk)
        
        if score > 0:
            name = krx_names.get(tk, tk)
            market_cap_100m = df_cap.loc[tk, '시가총액(억)'] if tk in df_cap.index else 0
            
            results.append({
                '종목코드': tk,
                '종목명': name,
                '현재가(원)': price,
                '등락률(%)': chg_pct,
                '영업이익(억)': '크롤링대기',  # 나중에 실시간 크롤링 모듈로 업데이트
                '시가총액(억)': market_cap_100m,
                '적합도 점수': score,
                '조건만족': pass_str
            })
            
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by='적합도 점수', ascending=False).reset_index(drop=True)
    return df_res

if __name__ == "__main__":
    print("엔진 테스트 시작... 시가총액 상위 50개 종목을 대상으로 A~G 필터링을 1차 검증합니다.")
    df_result = scan_hot_stocks(limit=50)
    print("\n[검증 완료 - 고득점 종목 탑 5]")
    print(df_result.head(5))
