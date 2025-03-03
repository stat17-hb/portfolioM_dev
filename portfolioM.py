import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import platform

# 한글 폰트 설정
if platform.system() == 'Windows':
    font_family = "Malgun Gothic"
elif platform.system() == 'Darwin':  # macOS
    font_family = "AppleGothic"
else:  # Linux
    font_family = "NanumGothic"

# 스트림릿 페이지 설정
st.set_page_config(page_title="포트폴리오 성과 분석", layout="wide")

# 스타일 설정
plt_style = {
    'template': 'plotly_dark',
    'font_family': font_family,
    'background_color': '#131722',
    'paper_bgcolor': '#131722',
    'plot_bgcolor': '#131722',
    'grid_color': '#363c4e',
    'text_color': '#D9D9D9'  # 텍스트 색상 추가
}

def read_file(file_path):
    # 파일 확장자 추출
    file_extension = file_path.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            df = pd.read_csv(file_path)
        elif file_extension == 'txt':
            df = pd.read_csv(file_path, sep='\t')  # tab으로 구분된 텍스트 파일 가정
        elif file_extension == 'xlsx':
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_extension}")
        
        return df
    
    except Exception as e:
        st.error(f"파일 읽기 오류: {str(e)}")
        return None

st.title("주식 포트폴리오 성과 분석")

# 샘플 데이터 형식 안내
st.subheader("📋 필요한 데이터 형식")
st.write("업로드하는 파일은 다음과 같은 열(컬럼)을 포함해야 합니다:")

# 샘플 데이터 생성
sample_data = {
    'Date': ['2024-01-02', '2024-01-05', '2024-01-10', '2024-01-15', '2024-01-20'],
    'Symbol': ['AAPL', 'TSLA', 'AAPL', 'MSFT', 'TSLA'],
    'Type': ['Buy', 'Buy', 'Sell', 'Buy', 'Sell'],
    'Quantity': [10, 5, 5, 8, 2],
    'Price': [150, 700, 160, 300, 750],
    'Total Value': [1500, 3500, 800, 2400, 1500],
    'Portfolio Value': [5000, 9000, 10000, 12500, 14000]
}
sample_df = pd.DataFrame(sample_data)

# 데이터 형식 설명
col1, col2 = st.columns([1, 2])
with col1:
    st.write("필수 컬럼:")
    st.markdown("""
    - **Date**: 거래일자 (YYYY-MM-DD 형식)
    - **Symbol**: 종목 코드
    - **Type**: 거래 유형 (Buy/Sell)
    - **Quantity**: 거래 수량
    - **Price**: 거래 단가
    - **Total Value**: 거래 금액
    - **Portfolio Value**: 포트폴리오 총 가치
    """)
with col2:
    st.write("샘플 데이터:")
    st.dataframe(sample_df, hide_index=True)

# 구분선 추가
st.markdown("---")

# 파일 업로드
uploaded_file = st.file_uploader("거래 데이터를 업로드하세요 (CSV, Excel, TXT 파일 지원)", type=["csv", "xlsx", "txt"])

# 지원 파일 형식 안내
st.caption("지원되는 파일 형식:")
st.caption("• CSV 파일 (.csv)")
st.caption("• Excel 파일 (.xlsx)")
st.caption("• 텍스트 파일 (.txt) - 탭으로 구분된 데이터")

if uploaded_file:
    df = read_file(uploaded_file)  # read_file 함수 사용
    st.write("업로드된 데이터 미리보기:")
    st.dataframe(df)

def calculate_portfolio_performance(df, start_date=None, end_date=None):
    if start_date is not None and end_date is not None:
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
    
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(by="Date")

    # 일간 수익률 계산 개선
    df["Daily Return"] = df["Portfolio Value"].pct_change().fillna(0)
    
    # 누적 수익률 계산
    initial_value = df["Portfolio Value"].iloc[0]
    final_value = df["Portfolio Value"].iloc[-1]
    cumulative_return = (final_value - initial_value) / initial_value
    
    # 연간 거래일 수 계산
    days = (df["Date"].max() - df["Date"].min()).days
    annualization_factor = 252 / days if days > 0 else 252
    
    # 성과 지표 계산
    annualized_return = (1 + cumulative_return) ** annualization_factor - 1
    volatility = df["Daily Return"].std() * np.sqrt(252)
    risk_free_rate = 0.02  # 무위험 수익률 (예: 2%)
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility != 0 else 0

    # 최대 낙폭 (MDD) 계산
    rolling_max = df["Portfolio Value"].expanding().max()
    drawdown = (df["Portfolio Value"] - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return {
        "시작일": df["Date"].min().strftime("%Y-%m-%d"),
        "종료일": df["Date"].max().strftime("%Y-%m-%d"),
        "누적 수익률": cumulative_return,
        "연율화 수익률": annualized_return,
        "샤프 비율": sharpe_ratio,
        "최대 낙폭 (MDD)": max_drawdown
    }

def calculate_stock_weights(df):
    # 마지막 거래 날짜 확인
    last_date = df['Date'].max()
    
    # 각 종목별 누적 포지션 계산
    positions = []
    for symbol in df['Symbol'].unique():
        symbol_trades = df[df['Symbol'] == symbol]
        net_quantity = sum([
            row['Quantity'] if row['Type'] == 'Buy' else -row['Quantity']
            for _, row in symbol_trades.iterrows()
        ])
        
        if net_quantity != 0:  # 순포지션이 있는 경우만
            # 해당 종목의 마지막 거래가격 사용
            last_price = symbol_trades.iloc[-1]['Price']
            current_value = net_quantity * last_price
            
            positions.append({
                'Symbol': symbol,
                'Net Quantity': net_quantity,
                'Price': last_price,
                'Current Value': current_value
            })
    
    # 데이터프레임 생성
    positions_df = pd.DataFrame(positions)
    
    if not positions_df.empty:
        # 총 포트폴리오 가치 계산
        total_portfolio_value = positions_df['Current Value'].abs().sum()
        
        # 비중 계산
        positions_df['Weight'] = positions_df['Current Value'].abs() / total_portfolio_value
        
        # 인덱스 설정
        positions_df.set_index('Symbol', inplace=True)
        
        return positions_df[['Net Quantity', 'Price', 'Current Value', 'Weight']]
    
    return pd.DataFrame(columns=['Net Quantity', 'Price', 'Current Value', 'Weight'])

if uploaded_file:
    # 전체 기간 성과 분석
    total_results = calculate_portfolio_performance(df)
    
    # 연도별 성과 분석
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    years = sorted(df['Year'].unique())
    yearly_results = {}
    
    for year in years:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        yearly_results[year] = calculate_portfolio_performance(df, start_date, end_date)

    # 전체 기간 성과 표시
    st.subheader("📊 전체 기간 포트폴리오 성과")
    st.write(f"분석 기간: {total_results['시작일']} ~ {total_results['종료일']}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("누적 수익률", f"{total_results['누적 수익률']:.2%}")
    with col2:
        st.metric("연율화 수익률", f"{total_results['연율화 수익률']:.2%}")
    with col3:
        st.metric("샤프 비율", f"{total_results['샤프 비율']:.2f}")
    with col4:
        st.metric("최대 낙폭 (MDD)", f"{total_results['최대 낙폭 (MDD)']:.2%}")

    # 연도별 성과 표시
    st.subheader("📅 연도별 포트폴리오 성과")
    
    # 연도별 데이터를 데이터프레임으로 변환
    yearly_data = []
    for year, results in yearly_results.items():
        # 해당 연도에 거래가 있는 경우만 추가
        if df[df['Year'] == year].shape[0] > 0:
            yearly_data.append({
                "연도": year,
                "누적 수익률": f"{results['누적 수익률']:.2%}",
                "연율화 수익률": f"{results['연율화 수익률']:.2%}",
                "샤프 비율": f"{results['샤프 비율']:.2f}",
                "최대 낙폭 (MDD)": f"{results['최대 낙폭 (MDD)']:.2%}"
            })
    
    yearly_df = pd.DataFrame(yearly_data)
    yearly_df.set_index("연도", inplace=True)
    
    # 스타일이 적용된 데이터프레임 표시
    if not yearly_df.empty:
        st.dataframe(
            yearly_df,
            height=min(400, len(yearly_df) * 35 + 38),  # 행 개수에 따라 높이 조정
            use_container_width=True
        )
    else:
        st.write("표시할 연도별 성과 데이터가 없습니다.")

    # 종목별 비중 분석
    st.subheader("📊 종목별 비중 분석")
    weights_df = calculate_stock_weights(df)
    
    # 표와 차트를 나란히 배치
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("종목별 보유 현황")
        # 데이터프레임 포맷팅
        formatted_df = weights_df.copy()
        formatted_df['Weight'] = formatted_df['Weight'].apply(lambda x: f"{x:.2%}")
        formatted_df['Current Value'] = formatted_df['Current Value'].apply(lambda x: f"{x:,.0f}")
        formatted_df['Price'] = formatted_df['Price'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(formatted_df)
    
    with col2:
        st.write("종목별 비중")
        # 파이 차트 생성
        fig = go.Figure(data=[go.Pie(
            labels=weights_df.index,
            values=weights_df['Current Value'].abs(),
            hole=0.4,
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(
                size=14,
                color='white'
            ),
            marker=dict(
                colors=[
                    '#8BB8FF',  # 부드러운 파란색
                    '#FFB7B7',  # 부드러운 빨간색
                    '#A8E6CF',  # 부드러운 초록색
                    '#FFD3B6',  # 부드러운 주황색
                    '#D4A5FF'   # 부드러운 보라색
                ],
                line=dict(color='#131722', width=2)
            ),
            hovertemplate="<b>%{label}</b><br>" +
                         "비중: %{percent}<br>" +
                         "포지션: %{customdata:,.0f}<extra></extra>",
            customdata=weights_df['Current Value']
        )])
        
        fig.update_layout(
            template=plt_style['template'],
            font=dict(
                family=plt_style['font_family'],
                color=plt_style['text_color'],
                size=12
            ),
            paper_bgcolor=plt_style['background_color'],
            plot_bgcolor=plt_style['plot_bgcolor'],
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.15,  # 위치 상향 조정
                xanchor="center",  # 중앙 정렬
                x=0.5,  # 중앙 위치
                font=dict(
                    size=14,  # 폰트 크기 증가
                    color='#FFFFFF'  # 흰색으로 변경
                ),
                bgcolor='rgba(19, 23, 34, 0.8)',  # 배경색 진하게
                bordercolor='rgba(255, 255, 255, 0.3)',  # 테두리 색상
                borderwidth=1
            ),
            height=500,  # 전체 높이 증가
            width=800,   # 전체 너비 설정
            margin=dict(t=100, b=50),  # 상하 여백 조정
            annotations=[
                dict(
                    text=f"총 포트폴리오 가치: {weights_df['Current Value'].abs().sum():,.0f}",
                    showarrow=False,
                    font=dict(size=14, color=plt_style['text_color']),
                    x=0.5,
                    y=-0.15
                )
            ]
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # TradingView 스타일의 차트 생성
    st.subheader("📈 포트폴리오 가치 변화")
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Portfolio Value"],
            name="포트폴리오 가치",
            line=dict(
                color='#8BB8FF',  # 부드러운 파란색으로 변경
                width=2
            ),
            fill='tozeroy',  # 영역 채우기 추가
            fillcolor='rgba(139, 184, 255, 0.1)'  # 채우기 색상 (투명도 0.1)
        )
    )

    fig.update_layout(
        template=plt_style['template'],
        font=dict(
            family=plt_style['font_family'],
            color=plt_style['text_color']
        ),
        paper_bgcolor=plt_style['background_color'],
        plot_bgcolor=plt_style['plot_bgcolor'],
        xaxis=dict(
            gridcolor=plt_style['grid_color'],
            showgrid=True,
            title="날짜",
            tickfont=dict(color=plt_style['text_color']),
            title_font=dict(color=plt_style['text_color'])
        ),
        yaxis=dict(
            gridcolor=plt_style['grid_color'],
            showgrid=True,
            title="가치",
            tickfont=dict(color=plt_style['text_color']),
            title_font=dict(color=plt_style['text_color'])
        ),
        showlegend=True,
        legend=dict(
            font=dict(color=plt_style['text_color'])
        ),
        height=600,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def save_file(df, output_path):
    # 파일 확장자 추출
    file_extension = output_path.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            df.to_csv(output_path, index=False)
        elif file_extension == 'txt':
            df.to_csv(output_path, sep='\t', index=False)
        elif file_extension == 'xlsx':
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_extension}")
            
        print(f"파일이 성공적으로 저장되었습니다: {output_path}")
        
    except Exception as e:
        print(f"파일 저장 오류: {str(e)}")