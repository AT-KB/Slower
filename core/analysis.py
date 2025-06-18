import pandas as pd
import yfinance as yf
from pandas.io.formats.style import Styler


def analyze_stock_candlestick(df: pd.DataFrame) -> str:
    """Return HTML table for candlestick analysis with integer values."""
    df_int = df.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x)
    return df_int.to_html(index=False)


def predict_future_moves(df: pd.DataFrame) -> str:
    """Return styled HTML highlighting the '上昇確率' column."""
    styler: Styler = df.style
    if "上昇確率" in df.columns:
        try:
            import matplotlib  # noqa: F401
        except Exception:
            pass
        else:
            styler = styler.background_gradient(
                cmap="RdYlGn",
                subset=["上昇確率"],
                vmin=0.5,
                vmax=1.0,
            )
    return styler.to_html()


def _load_fundamentals(ticker_symbol: str) -> dict:
    """Load fundamentals using yfinance with fallbacks."""
    ticker = yf.Ticker(ticker_symbol)
    info = getattr(ticker, "info", {}) or {}
    trailing_pe = info.get("trailingPE")
    price_to_book = info.get("priceToBook")
    return {
        "trailingPE": trailing_pe if trailing_pe is not None else "N/A",
        "priceToBook": price_to_book if price_to_book is not None else "N/A",
    }
