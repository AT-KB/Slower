import sys
import os
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

import types
import pandas as pd
import core.analysis as analysis


def test_analyze_stock_candlestick_no_index():
    df = pd.DataFrame({"open": [1.1, 2.2], "close": [3.3, 4.4]}, index=pd.date_range("2020-01-01", periods=2))
    html = analysis.analyze_stock_candlestick(df)
    assert "2020-01-01" not in html
    assert ">1<" in html and ">3<" in html


def test_predict_future_moves_gradient():
    df = pd.DataFrame({"銘柄": ["AAA"], "上昇確率": [0.75]})
    html = analysis.predict_future_moves(df)
    assert "background-color" in html


def test_load_fundamentals(monkeypatch):
    class DummyTicker:
        def __init__(self, info):
            self.info = info

    def dummy(symbol):
        return DummyTicker({"trailingPE": 10, "priceToBook": 1.2})

    monkeypatch.setattr(analysis.yf, "Ticker", dummy)
    data = analysis._load_fundamentals("AAA")
    assert data["trailingPE"] == 10
    assert data["priceToBook"] == 1.2


def test_load_fundamentals_missing(monkeypatch):
    class DummyTicker:
        def __init__(self, info):
            self.info = info

    def dummy(symbol):
        return DummyTicker({})

    monkeypatch.setattr(analysis.yf, "Ticker", dummy)
    data = analysis._load_fundamentals("AAA")
    assert data["trailingPE"] == "N/A"
    assert data["priceToBook"] == "N/A"
