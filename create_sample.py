import yfinance as yf
import pandas as pd
import numpy as np
import time

# 설정
np.random.seed(42)
tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]  # 5개 종목
start_date = "2022-01-01"
end_date = "2024-12-31"

def download_with_retry(tickers, start_date, end_date, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"주가 데이터 다운로드 시도 {attempt + 1}/{max_retries}...")
            stock_data = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]
            
            if not stock_data.empty and not stock_data.isna().all().all():
                print("데이터 다운로드 성공!")
                return stock_data
                
        except Exception as e:
            print(f"다운로드 실패: {str(e)}")
            
        print("30초 후 재시도합니다...")
        time.sleep(30)  # 30초 대기
    
    return None

# 데이터 다운로드 시도
stock_data = download_with_retry(tickers, start_date, end_date)

if stock_data is None:
    print("샘플 데이터를 생성합니다.")
    # 샘플 주가 데이터 생성
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 영업일 기준
    stock_data = pd.DataFrame(index=dates)
    for ticker in tickers:
        base_price = np.random.randint(100, 1000)
        prices = np.random.normal(loc=0, scale=0.02, size=len(dates))
        prices = base_price * (1 + np.cumsum(prices))
        stock_data[ticker] = prices

# 거래 데이터 생성
dates = pd.date_range(start=start_date, end=end_date, freq="W-FRI")  # 매주 금요일 기준
num_trades = len(dates)
trade_types = ["Buy", "Sell"]

trade_data = []
portfolio_value = 10000  # 초기 포트폴리오 가치
holdings = {ticker: 0 for ticker in tickers}  # 각 종목별 보유 수량 추적

for i in range(num_trades):
    date = dates[i]
    symbol = np.random.choice(tickers)
    
    # 해당 날짜의 주가 가져오기 (가장 가까운 이전 거래일 사용)
    nearest_date = stock_data.index[stock_data.index <= date][-1]
    price = stock_data.loc[nearest_date, symbol]
    
    # 매수/매도 결정 (보유 수량이 0이면 무조건 매수)
    if holdings[symbol] == 0:
        trade_type = "Buy"
    else:
        trade_type = np.random.choice(trade_types)
    
    if trade_type == "Buy":
        quantity = np.random.randint(1, 20)  # 1~20주 랜덤 매수
        holdings[symbol] += quantity
        total_value = quantity * price
        portfolio_value += total_value
    else:
        max_sell = holdings[symbol]  # 현재 보유 수량까지만 매도 가능
        quantity = np.random.randint(1, max_sell + 1)  # 1주부터 보유 수량까지 랜덤 매도
        holdings[symbol] -= quantity
        total_value = quantity * price
        portfolio_value -= total_value

    trade_data.append([
        date.strftime("%Y-%m-%d"), 
        symbol, 
        trade_type, 
        quantity, 
        round(price, 2), 
        round(total_value, 2), 
        round(portfolio_value, 2)
    ])

# 데이터프레임 생성
trade_df = pd.DataFrame(
    trade_data, 
    columns=["Date", "Symbol", "Type", "Quantity", "Price", "Total Value", "Portfolio Value"]
)

# CSV 파일 저장
csv_filename = "sample_trade_data.csv"
trade_df.to_csv(csv_filename, index=False)

print(f"샘플 거래 데이터가 {csv_filename}로 저장되었습니다.")
