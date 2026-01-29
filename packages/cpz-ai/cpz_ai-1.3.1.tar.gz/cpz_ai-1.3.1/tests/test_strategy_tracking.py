"""Tests for strategy tracking methods."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cpz.common.cpz_ai import CPZAIClient


@pytest.fixture
def mock_client():
    """Create a mock CPZAIClient for testing."""
    with patch.object(CPZAIClient, '__init__', lambda self, **kwargs: None):
        client = CPZAIClient()
        client.url = "https://api-ai.cpz-lab.com/cpz"
        client.api_key = "test_key"
        client.secret_key = "test_secret"
        client.user_id = "test_user"
        client.is_admin = False
        client.logger = Mock()
        return client


class TestGetOrdersByStrategy:
    """Tests for get_orders_by_strategy method."""

    def test_requires_strategy_id(self, mock_client):
        """Should raise ValueError if strategy_id is not provided."""
        with pytest.raises(ValueError, match="strategy_id is required"):
            mock_client.get_orders_by_strategy("")

    @patch('requests.get')
    def test_returns_orders_list(self, mock_get, mock_client):
        """Should return list of orders for strategy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "AAPL", "side": "buy", "filled_quantity": 10},
            {"symbol": "GOOGL", "side": "sell", "filled_quantity": 5},
        ]
        mock_get.return_value = mock_response
        
        result = mock_client.get_orders_by_strategy("test-strategy")
        
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"

    @patch('requests.get')
    def test_returns_empty_on_error(self, mock_get, mock_client):
        """Should return empty list on error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = mock_client.get_orders_by_strategy("test-strategy")
        
        assert result == []


class TestGetPositionsByStrategy:
    """Tests for get_positions_by_strategy method."""

    def test_requires_strategy_id(self, mock_client):
        """Should raise ValueError if strategy_id is not provided."""
        with pytest.raises(ValueError, match="strategy_id is required"):
            mock_client.get_positions_by_strategy("")

    @patch('requests.get')
    def test_returns_positions_list(self, mock_get, mock_client):
        """Should return list of positions for strategy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "AAPL", "qty": 100, "unrealized_pl": 500.0},
        ]
        mock_get.return_value = mock_response
        
        result = mock_client.get_positions_by_strategy("test-strategy")
        
        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"


class TestGetStrategyPerformance:
    """Tests for get_strategy_performance method."""

    def test_requires_strategy_id(self, mock_client):
        """Should raise ValueError if strategy_id is not provided."""
        with pytest.raises(ValueError, match="strategy_id is required"):
            mock_client.get_strategy_performance("")

    def test_returns_performance_dict(self, mock_client):
        """Should return performance metrics dictionary."""
        with patch.object(mock_client, 'get_orders_by_strategy', return_value=[]):
            with patch.object(mock_client, 'get_positions_by_strategy', return_value=[]):
                result = mock_client.get_strategy_performance("test-strategy")
        
        assert "strategy_id" in result
        assert "total_trades" in result
        assert "win_rate" in result
        assert "net_pl" in result
        assert result["strategy_id"] == "test-strategy"

    def test_calculates_win_rate(self, mock_client):
        """Should calculate win rate from orders."""
        orders = [
            {"symbol": "AAPL", "side": "buy", "filled_quantity": 10, "average_fill_price": 100, "filled_at": "2026-01-01"},
            {"symbol": "AAPL", "side": "sell", "filled_quantity": 10, "average_fill_price": 110, "filled_at": "2026-01-02"},
        ]
        with patch.object(mock_client, 'get_orders_by_strategy', return_value=orders):
            with patch.object(mock_client, 'get_positions_by_strategy', return_value=[]):
                result = mock_client.get_strategy_performance("test-strategy")
        
        assert result["winning_trades"] == 1
        assert result["losing_trades"] == 0
        assert result["win_rate"] == 100.0
        assert result["total_realized_pl"] == 100.0  # (110-100) * 10
