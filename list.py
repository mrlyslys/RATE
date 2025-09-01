import requests
import json
import statistics
import datetime
from time import sleep
import os

class OrderData:
    def __init__(self, price: float, amount: float):
        self.price = price
        self.amount = amount

class RatAnalyzer:
    def __init__(self, fiat, trade_type):
        self.fiat = fiat.upper()
        self.trade_type = trade_type.upper()
        self.orders = []

    def fetch_data(self, asset="USDT"):
        url = "https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        headers = {"Content-Type": "application/json"}
        page, rows = 1, 20

        while True:
            payload = {
                "page": page,
                "rows": rows,
                "payTypes": [],
                "asset": asset,
                "fiat": self.fiat,
                "tradeType": self.trade_type
            }
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                break
            data = response.json().get("data", [])
            if not data:
                break

            for ad in data:
                adv = ad["adv"]
                price = float(adv["price"])
                amount = float(adv["surplusAmount"])
                self.orders.append(OrderData(price, amount))

            page += 1
            sleep(0.3)  # 防止请求过快

    def get_summary(self):
        if not self.orders:
            return None

        prices = [o.price for o in self.orders]
        amounts = [o.amount for o in self.orders]

        q1, q3 = statistics.quantiles(prices, n=4)[0], statistics.quantiles(prices, n=4)[2]
        q2 = statistics.median(prices)

        return {
            "median": q2,
            "totalVolume": sum(amounts),
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "min": min(prices),
            "max": max(prices)
        }


if __name__ == '__main__':
    currencies = [
        "AED", "AUD"#, "COP", "EUR", "HKD", "IDR", "INR", "KHR",
        #"LAK", "MXN", "PKR", "TRY", "TZS", "USD", "VND", "ZAR"
    ]

    results = {}

    for fiat in currencies:
        # 买数据
        buy_analyzer = RatAnalyzer(fiat, "BUY")
        buy_analyzer.fetch_data()
        buy_stats = buy_analyzer.get_summary()

        # 卖数据
        sell_analyzer = RatAnalyzer(fiat, "SELL")
        sell_analyzer.fetch_data()
        sell_stats = sell_analyzer.get_summary()

        if buy_stats and sell_stats:
            results[fiat.lower()] = {
                "buy": f"{buy_stats['median']:.2f}",
                "sell": f"{sell_stats['median']:.2f}",
                "buyVolume": f"{buy_stats['totalVolume']:.2f}",
                "sellVolume": f"{sell_stats['totalVolume']:.2f}",
                "buyStats": {
                    "Q1": round(buy_stats['q1'], 2),
                    "Q2": round(buy_stats['q2'], 2),
                    "Q3": round(buy_stats['q3'], 2),
                    "min": round(buy_stats['min'], 2),
                    "max": round(buy_stats['max'], 2)
                },
                "sellStats": {
                    "Q1": round(sell_stats['q1'], 2),
                    "Q2": round(sell_stats['q2'], 2),
                    "Q3": round(sell_stats['q3'], 2),
                    "min": round(sell_stats['min'], 2),
                    "max": round(sell_stats['max'], 2)
                }
            }

        sleep(2)  # 每个币种等一会

    # 输出成 JS 格式
    output_html = "index.html"  # 你的 HTML 文件路径

    with open(output_html, "r", encoding="utf-8") as f:
        html = f.read()

    # 新的数据
    new_rates = f"const rates = {json.dumps(results, indent=2)};"

    # 用正则替换掉原来的 const rates = {...};
    import re

    html = re.sub(r'const rates\s*=\s*{.*?};', new_rates, html, flags=re.S)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ index.html 已更新")
