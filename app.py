from flask import Flask, render_template, jsonify
import requests
from threading import Lock

app = Flask(__name__)
lock = Lock()

YAHOO_GAINERS_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=20&scrIds=day_gainers"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gainers")
def gainers():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/116.0 Safari/537.36"
        }
        with lock:
            res = requests.get(YAHOO_GAINERS_URL, headers=headers, timeout=5)

        if res.status_code != 200:
            return jsonify([])

        data = res.json()

        if "finance" not in data or not data["finance"].get("result"):
            return jsonify([])

        quotes = data["finance"]["result"][0]["quotes"]
        top_gainers = []
        for q in quotes[:20]:
            top_gainers.append({
                "symbol": q.get("symbol", ""),
                "name": q.get("shortName", ""),
                "price": q.get("regularMarketPrice", 0),
                "changePercent": q.get("regularMarketChangePercent", 0),
                "volume": q.get("regularMarketVolume", 0)
            })
        return jsonify(top_gainers)
    except Exception as e:
        print("Error:", e)
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
