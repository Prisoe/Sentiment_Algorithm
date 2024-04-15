# Import form Lumibot Alpaca for Broker, YahooData for Backtesting, Trader for trading, Strategy for backtesting. 

from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime 
from alpaca_trade_api import REST 
from timedelta import Timedelta 
from finbert_utils import estimate_sentiment


# API Info
API_KEY = "#"  Add your Api Key
API_SECRET = "Vm3ul2E5w8GCN5S8UhMUCf0hyMV9orL5rSUkXNs6" 
BASE_URL = "https://paper-api.alpaca.markets"

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}


# Create a trading class to store fucntions 
class MLTrader(Strategy):
    # Ask for Trading Ticker
    # symbol = input("What are we trading today??: ")
    # Initialze with symbol  
    def initialize(self, symbol:str="AAPL", cash_at_risk:float=.5): 
        self.symbol = symbol
        self.sleeptime = "24H" 
        self.last_trade = None 
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)


    # Determine the Amount to trade
    def position_sizing(self): 
        cash = self.get_cash() 
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price,0)
        return cash, last_price, quantity


    # Determine date
    def get_dates(self): 
        today = self.get_datetime()
        five_days_prior = today - Timedelta(days=5)
        return today.strftime('%Y-%m-%d'), five_days_prior.strftime('%Y-%m-%d')


    # From finbert_utils, get Sentiment model value
    def get_sentiment(self): 
        today, five_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, 
                                 start=five_days_prior, 
                                 end=today) 
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment 


    # Trading Strategy
    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing() 
        probability, sentiment = self.get_sentiment()

        if cash > last_price: 
            if sentiment == "positive" and probability > .999: 
                if self.last_trade == "sell": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type="bracket", 
                    take_profit_price=last_price*1.20, 
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order) 
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > .999: 
                if self.last_trade == "buy": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell", 
                    type="bracket", 
                    take_profit_price=last_price*.8, 
                    stop_loss_price=last_price*1.05
                )
                self.submit_order(order) 
                self.last_trade = "sell"

start_date = datetime(2022,1,1)
end_date = datetime(2024,1,31) 
broker = Alpaca(ALPACA_CREDS) 
strategy = MLTrader(name='mlstrat', broker=broker, 
                    parameters={"symbol":"AAPL", 
                                "cash_at_risk":.5})
strategy.backtest(
    YahooDataBacktesting, 
    start_date, 
    end_date, 
    parameters={f"symbol":"AAPL", "cash_at_risk":.5}
)
# trader = Trader()
# trader.add_strategy(strategy)
# trader.run_all()
