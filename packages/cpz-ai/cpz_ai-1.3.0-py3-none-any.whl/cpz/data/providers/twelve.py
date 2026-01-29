"""Twelve Data provider for stocks, forex, crypto, and technical indicators.

Supports:
- Real-time and historical stock data
- Forex pairs (100+ currency pairs)
- Cryptocurrency data
- ETFs and Indices
- 100+ Technical Indicators

Docs: https://twelvedata.com/docs
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

import requests

from ..models import Bar, Quote, TimeFrame


class TwelveDataProvider:
    """Twelve Data market data provider.
    
    Usage:
        provider = TwelveDataProvider()
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=100)
        forex = provider.get_forex_quote("EUR/USD")
    """
    
    name = "twelve"
    supported_assets = ["stocks", "forex", "crypto", "etfs", "indices"]
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Twelve Data provider.
        
        Args:
            api_key: Twelve Data API key (automatically fetched from CPZAI platform or env var)
        """
        self._api_key = api_key or os.getenv("TWELVE_DATA_API_KEY", "")
        
        # If still no key, try to fetch from CPZAI platform
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="twelve")
                self._api_key = creds.get("twelve_api_key", "")
            except Exception:
                pass
        
        if not self._api_key:
            raise ValueError(
                "Twelve Data API key not found. Options:\n"
                "1. Add Twelve Data credentials in CPZAI platform at: https://ai.cpz-lab.com/data/connections\n"
                "2. Set TWELVE_DATA_API_KEY environment variable\n"
                "3. Get a free API key at: https://twelvedata.com/account/api-keys"
            )
    
    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Twelve Data API."""
        params["apikey"] = self._api_key
        
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if data.get("status") == "error":
            raise ValueError(f"Twelve Data API error: {data.get('message', 'Unknown error')}")
        
        return data
    
    def _convert_timeframe(self, tf: TimeFrame) -> str:
        """Convert TimeFrame to Twelve Data interval string."""
        mapping = {
            TimeFrame.MINUTE_1: "1min",
            TimeFrame.MINUTE_5: "5min",
            TimeFrame.MINUTE_15: "15min",
            TimeFrame.MINUTE_30: "30min",
            TimeFrame.HOUR_1: "1h",
            TimeFrame.HOUR_4: "4h",
            TimeFrame.DAY: "1day",
            TimeFrame.WEEK: "1week",
            TimeFrame.MONTH: "1month",
        }
        return mapping.get(tf, "1day")
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        exchange: Optional[str] = None,
    ) -> List[Bar]:
        """Get historical bars for stocks, forex, or crypto.
        
        Args:
            symbol: Symbol (e.g., "AAPL", "EUR/USD", "BTC/USD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars to return (max 5000)
            exchange: Exchange code (optional)
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": min(limit, 5000),
        }
        
        if start:
            params["start_date"] = start.strftime("%Y-%m-%d %H:%M:%S")
        if end:
            params["end_date"] = end.strftime("%Y-%m-%d %H:%M:%S")
        if exchange:
            params["exchange"] = exchange
        
        data = self._request("time_series", params)
        
        bars: List[Bar] = []
        for item in data.get("values", []):
            bars.append(Bar(
                symbol=symbol,
                timestamp=datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S") 
                    if " " in item["datetime"] 
                    else datetime.strptime(item["datetime"], "%Y-%m-%d"),
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item.get("volume", 0)),
            ))
        
        # Twelve Data returns newest first, reverse for chronological order
        bars.reverse()
        return bars
    
    def get_quote(self, symbol: str, exchange: Optional[str] = None) -> Quote:
        """Get latest quote for a symbol.
        
        Args:
            symbol: Symbol (e.g., "AAPL", "EUR/USD")
            exchange: Exchange code (optional)
            
        Returns:
            Quote object
        """
        params: Dict[str, Any] = {"symbol": symbol}
        if exchange:
            params["exchange"] = exchange
        
        data = self._request("quote", params)
        
        return Quote(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bid=float(data.get("close", 0)),  # Twelve Data doesn't have bid/ask in quote
            ask=float(data.get("close", 0)),
            bid_size=float(data.get("volume", 0)),
            ask_size=0.0,
        )
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for multiple symbols.
        
        Args:
            symbols: List of symbols
            
        Returns:
            List of Quote objects
        """
        return [self.get_quote(symbol) for symbol in symbols]
    
    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol.
        
        Args:
            symbol: Symbol (e.g., "AAPL")
            
        Returns:
            Current price
        """
        data = self._request("price", {"symbol": symbol})
        return float(data.get("price", 0))
    
    def get_forex_quote(self, symbol: str) -> Dict[str, Any]:
        """Get forex pair quote with detailed info.
        
        Args:
            symbol: Forex pair (e.g., "EUR/USD")
            
        Returns:
            Detailed forex quote data
        """
        data = self._request("quote", {"symbol": symbol})
        return {
            "symbol": symbol,
            "open": float(data.get("open", 0)),
            "high": float(data.get("high", 0)),
            "low": float(data.get("low", 0)),
            "close": float(data.get("close", 0)),
            "change": float(data.get("change", 0)),
            "percent_change": float(data.get("percent_change", 0)),
            "timestamp": data.get("datetime"),
        }
    
    def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Get cryptocurrency quote.
        
        Args:
            symbol: Crypto pair (e.g., "BTC/USD")
            
        Returns:
            Crypto quote data
        """
        return self.get_forex_quote(symbol)
    
    # --- Technical Indicators ---
    
    def get_sma(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Simple Moving Average.
        
        Args:
            symbol: Symbol
            timeframe: Bar timeframe
            period: SMA period
            limit: Number of data points
            
        Returns:
            List of SMA values with timestamps
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("sma", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "sma": float(v["sma"])}
            for v in data.get("values", [])
        ]
    
    def get_ema(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ema", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "ema": float(v["ema"])}
            for v in data.get("values", [])
        ]
    
    def get_rsi(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Relative Strength Index."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("rsi", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "rsi": float(v["rsi"])}
            for v in data.get("values", [])
        ]
    
    def get_macd(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get MACD (Moving Average Convergence Divergence)."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("macd", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
            "outputsize": limit,
        })
        
        return [
            {
                "datetime": v["datetime"],
                "macd": float(v["macd"]),
                "macd_signal": float(v["macd_signal"]),
                "macd_hist": float(v["macd_hist"]),
            }
            for v in data.get("values", [])
        ]
    
    def get_bbands(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        std_dev: float = 2.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Bollinger Bands."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("bbands", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "sd": std_dev,
            "outputsize": limit,
        })
        
        return [
            {
                "datetime": v["datetime"],
                "upper_band": float(v["upper_band"]),
                "middle_band": float(v["middle_band"]),
                "lower_band": float(v["lower_band"]),
            }
            for v in data.get("values", [])
        ]
    
    def get_indicator(
        self,
        indicator: str,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
        **params: Any,
    ) -> List[Dict[str, Any]]:
        """Get any technical indicator.
        
        Args:
            indicator: Indicator name (e.g., "stoch", "adx", "atr")
            symbol: Symbol
            timeframe: Bar timeframe
            limit: Number of data points
            **params: Additional indicator parameters
            
        Returns:
            List of indicator values
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        request_params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
            **params,
        }
        
        data = self._request(indicator.lower(), request_params)
        return data.get("values", [])
    
    # --- Reference Data ---
    
    def get_stocks_list(
        self,
        exchange: Optional[str] = None,
        country: Optional[str] = None,
        type_filter: Optional[str] = None,  # "stock", "etf", "fund"
    ) -> List[Dict[str, str]]:
        """Get list of available stocks.
        
        Args:
            exchange: Filter by exchange
            country: Filter by country code
            type_filter: Filter by type
            
        Returns:
            List of stock metadata
        """
        params: Dict[str, Any] = {}
        if exchange:
            params["exchange"] = exchange
        if country:
            params["country"] = country
        if type_filter:
            params["type"] = type_filter
        
        data = self._request("stocks", params)
        return data.get("data", [])
    
    def get_forex_pairs(self) -> List[Dict[str, str]]:
        """Get list of available forex pairs."""
        data = self._request("forex_pairs", {})
        return data.get("data", [])
    
    def get_cryptocurrencies(self) -> List[Dict[str, str]]:
        """Get list of available cryptocurrencies."""
        data = self._request("cryptocurrencies", {})
        return data.get("data", [])
    
    def get_exchanges(self, type_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of supported exchanges.
        
        Args:
            type_filter: "stock", "etf", "index"
            
        Returns:
            List of exchange metadata
        """
        params: Dict[str, Any] = {}
        if type_filter:
            params["type"] = type_filter
        
        data = self._request("exchanges", params)
        return data.get("data", [])
    
    def get_market_state(self, exchange: str) -> Dict[str, Any]:
        """Get market state (open/closed) for an exchange.
        
        Args:
            exchange: Exchange code (e.g., "NYSE", "NASDAQ")
            
        Returns:
            Market state info
        """
        data = self._request("market_state", {"exchange": exchange})
        return data
    
    def get_earliest_timestamp(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
    ) -> datetime:
        """Get earliest available timestamp for a symbol.
        
        Args:
            symbol: Symbol
            timeframe: Bar timeframe
            
        Returns:
            Earliest available datetime
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("earliest_timestamp", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
        })
        
        return datetime.strptime(data["datetime"], "%Y-%m-%d")


# Popular forex pairs for convenience
FOREX_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD",
    "EUR/GBP", "EUR/JPY", "GBP/JPY",
]

# Popular crypto pairs
CRYPTO_PAIRS = [
    "BTC/USD", "ETH/USD", "BNB/USD", "XRP/USD",
    "SOL/USD", "ADA/USD", "DOGE/USD", "DOT/USD",
]
