import pandas as pd
import backtrader as bt

ticker = "AAPL"

# Load CSV without header
df = pd.read_csv(f"{ticker}.csv", header=None)

# Assign column names
df.columns = ['datetime', 'close', 'high', 'low', 'open', 'volume']

# Reorder columns for Backtrader
df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

# Convert datetime and strip timezone
df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize(None)

# Save cleaned CSV
clean_csv = f"{ticker}_clean.csv"
df.to_csv(clean_csv, index=False)

# Load into Backtrader
data_feed = bt.feeds.GenericCSVData(
    dataname=clean_csv,
    dtformat='%Y-%m-%d %H:%M:%S',  # now matches the cleaned datetime
    timeframe=bt.TimeFrame.Minutes,
    compression=60,
    openinterest=-1
)

# Backtrader setup
cerebro = bt.Cerebro()
cerebro.adddata(data_feed)
cerebro.broker.setcash(100000)

# Simple SMA Strategy
class SmaCross(bt.Strategy):
    def __init__(self):
        self.sma_fast = bt.indicators.SMA(self.data.close, period=10)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=30)

    def next(self):
        if self.sma_fast[0] > self.sma_slow[0] and self.position.size == 0:
            self.buy()
        elif self.sma_fast[0] < self.sma_slow[0] and self.position.size > 0:
            self.close()

cerebro.addstrategy(SmaCross)

print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
cerebro.run()
print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
cerebro.plot()
