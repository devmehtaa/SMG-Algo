import backtrader as bt
import pandas as pd
import yfinance as yf
import requests

# -------------------------------
# 1. Get S&P 500 tickers
# -------------------------------
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(url, headers=headers)
tables = pd.read_html(response.text)
tickers = tables[0]['Symbol'].tolist()

# -------------------------------
# 2. Backtrader setup
# -------------------------------
cerebro = bt.Cerebro()
cerebro.broker.setcash(100000)  # total capital

# -------------------------------
# 3. Strategy
# -------------------------------
class HourlyTrendBreakout(bt.Strategy):
    params = dict(
        ema_period=20,
        bb_period=20,
        bb_dev=2,
        rsi_period=14,
        atr_period=14,
        atr_min=0.5,
        risk_atr_multiplier=0.5,
        profit_target_pct=0.2,
        cash_per_trade=10000,  
        max_position_pct=0.05  # allocate $10k per trade
    )

    def __init__(self):
        # Create dictionaries to hold indicators for each data feed
        self.ema = dict()
        self.bb = dict()
        self.rsi = dict()
        self.atr = dict()
        self.entry_price = dict()
        self.stop_price = dict()
        self.take_price = dict()

        for d in self.datas:
            self.ema[d] = bt.indicators.ExponentialMovingAverage(d.close, period=self.params.ema_period)
            self.bb[d] = bt.indicators.BollingerBands(d.close, period=self.params.bb_period, devfactor=self.params.bb_dev)
            self.rsi[d] = bt.indicators.RSI(d.close, period=self.params.rsi_period)
            self.atr[d] = bt.indicators.ATR(d, period=self.params.atr_period)
            self.entry_price[d] = None
            self.stop_price[d] = None
            self.take_price[d] = None

            

    def next(self):
        for d in self.datas:
            close = d.close[0]
            ema = self.ema[d][0]
            bb_top = self.bb[d].lines.top[0]
            bb_bot = self.bb[d].lines.bot[0]
            rsi = self.rsi[d][0]
            atr = self.atr[d][0]

            # Skip if ATR is not yet available
            if atr is None or atr < self.params.atr_min:
                continue

            trend_up = close > ema
            trend_down = close < ema
            breakout_up = close > bb_top
            breakout_down = close < bb_bot
            rsi_ok = rsi < 70

            account_value = self.broker.getvalue()
            size = int((account_value * self.params.max_position_pct) / close)
            if size < 1:
                size = 1 

            # -------------------
            # Entry
            # -------------------
            if not self.getposition(d):
                # Long
                if trend_up and breakout_up and rsi_ok:
                    self.entry_price[d] = close
                    self.stop_price[d] = close - atr * self.params.risk_atr_multiplier
                    self.take_price[d] = close * (1 + self.params.profit_target_pct)
                    # size = self.params.cash_per_trade / close
                    self.buy(data=d, size=size)
                    print(f"{d._name} {self.data.datetime.datetime(0)} BUY at {close:.2f}, Stop: {self.stop_price[d]:.2f}, Target: {self.take_price[d]:.2f}")

                # Short
                elif trend_down and breakout_down:
                    self.entry_price[d] = close
                    self.stop_price[d] = close + atr * self.params.risk_atr_multiplier
                    self.take_price[d] = close * (1 - self.params.profit_target_pct)
                    # size = self.params.cash_per_trade / close
                    self.sell(data=d, size=size)
                    print(f"{d._name} {self.data.datetime.datetime(0)} SELL at {close:.2f}, Stop: {self.stop_price[d]:.2f}, Target: {self.take_price[d]:.2f}")

            # -------------------
            # Manage open position
            # -------------------
            pos = self.getposition(d)
            if pos:
                # Long
                if pos.size > 0:
                    if self.stop_price[d] is None:  # <-- ADD THIS
                        self.stop_price[d] = close - atr * self.params.risk_atr_multiplier
                    self.stop_price[d] = max(self.stop_price[d], close - atr * self.params.risk_atr_multiplier)
                    if self.stop_price[d] is not None and close <= self.stop_price[d]:
                        self.close(data=d)
                        print(f"{d._name} {self.data.datetime.datetime(0)} CLOSE long at {close:.2f} (Stop triggered)")
                        self.entry_price[d] = self.stop_price[d] = self.take_price[d] = None
                        
                        
                    elif self.take_price[d] is not None and close >= self.take_price[d]:
                        self.close(data=d)
                        print(f"{d._name} {self.data.datetime.datetime(0)} CLOSE long at {close:.2f} (Profit target hit)")
                        self.entry_price[d] = self.stop_price[d] = self.take_price[d] = None
                # Short
                elif pos.size < 0:
                    if self.stop_price[d] is None:  # <-- ADD THIS
                        self.stop_price[d] = close + atr * self.params.risk_atr_multiplier
                    self.stop_price[d] = min(self.stop_price[d], close + atr * self.params.risk_atr_multiplier)
                    if self.stop_price[d] is not None and close >= self.stop_price[d]:
                        self.close(data=d)
                        print(f"{d._name} {self.data.datetime.datetime(0)} CLOSE short at {close:.2f} (Stop triggered)")
                        self.entry_price[d] = self.stop_price[d] = self.take_price[d] = None
                    elif self.take_price[d] is not None and close <= self.take_price[d]:
                        self.close(data=d)
                        print(f"{d._name} {self.data.datetime.datetime(0)} CLOSE short at {close:.2f} (Profit target hit)")
                        self.entry_price[d] = self.stop_price[d] = self.take_price[d] = None

# -------------------------------
# 4. Download data & add feeds
# -------------------------------
for ticker in tickers[:100]:  # limit first 50 for speed; remove [:50] for all 500
    try:
        data = yf.download(ticker, period='3mo', interval='60m', auto_adjust=False)
        if data.empty:
            continue
        data.columns = ['datetime', 'close', 'high', 'low', 'open', 'volume']
        # Reorder columns for Backtrader
        data = data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        data['datetime'] = pd.to_datetime(data['datetime']).dt.tz_localize(None)

        # Reset index to make datetime a column
        data.reset_index(inplace=True)

        # Rename columns for Backtrader
        data.rename(columns={
            'Datetime': 'datetime',  # for some versions
            'Date': 'datetime',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }, inplace=True)

        print(data.head())
        data_feed = bt.feeds.PandasData(
            dataname=data,
            datetime='datetime',
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )

        cerebro.adddata(data_feed, name=ticker)
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        continue

# -------------------------------
# 5. Run strategy
# -------------------------------
print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
starting_cash = cerebro.broker.getvalue()
cerebro.addstrategy(HourlyTrendBreakout)
cerebro.run()
final_value = cerebro.broker.getvalue()
print(f"Final Portfolio Value: {final_value:.2f}")
returns_pct = ((final_value - starting_cash) / starting_cash) * 100
print(f"Total Return: {returns_pct:.2f}%")
