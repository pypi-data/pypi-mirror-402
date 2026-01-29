"""
Price Oracle System for AILOOS Marketplace.
Provides dynamic pricing for datasets based on multiple factors.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics
import hashlib

from ..core.logging import get_logger
from ..blockchain.dracma_token import get_token_manager
from .data_listing import DataCategory

logger = get_logger(__name__)


class OracleSource(Enum):
    """Sources for price data."""
    MARKET_TRANSACTIONS = "market_transactions"
    FEDERATED_CONTRIBUTIONS = "federated_contributions"
    EXTERNAL_APIS = "external_apis"
    COMMUNITY_VOTES = "community_votes"
    AI_PREDICTIONS = "ai_predictions"


@dataclass
class PriceDataPoint:
    """Individual price data point."""
    dataset_hash: str
    category: DataCategory
    price: float
    volume: int
    timestamp: datetime
    source: OracleSource
    confidence: float  # 0-1 confidence score


@dataclass
class OraclePrice:
    """Aggregated price from oracle."""
    category: DataCategory
    base_price: float
    market_price: float
    suggested_price: float
    confidence: float
    last_updated: datetime
    data_points: int
    volatility: float


class PriceOracle:
    """
    Price Oracle for dynamic dataset pricing.
    Aggregates data from multiple sources to provide fair market prices.
    """

    def __init__(self):
        self.price_history: Dict[str, List[PriceDataPoint]] = {}
        self.category_prices: Dict[DataCategory, OraclePrice] = {}
        self.token_manager = get_token_manager()

        # Configuration
        self.history_window_days = 30
        self.min_data_points = 5
        self.max_volatility = 0.5  # 50% max price swing
        self.update_interval_seconds = 300  # 5 minutes

        # Initialize base prices for categories
        self._initialize_base_prices()

        logger.info("💰 Price Oracle initialized")

    def _initialize_base_prices(self):
        """Initialize base prices for data categories."""
        base_prices = {
            DataCategory.IMAGE_DATA: 50.0,
            DataCategory.TEXT_DATA: 30.0,
            DataCategory.AUDIO_DATA: 75.0,
            DataCategory.TABULAR_DATA: 40.0,
            DataCategory.TIME_SERIES: 60.0,
            DataCategory.MEDICAL_DATA: 200.0,
            DataCategory.FINANCIAL_DATA: 150.0,
            DataCategory.IoT_DATA: 45.0,
        }

        for category, base_price in base_prices.items():
            self.category_prices[category] = OraclePrice(
                category=category,
                base_price=base_price,
                market_price=base_price,
                suggested_price=base_price,
                confidence=0.5,
                last_updated=datetime.now(),
                data_points=0,
                volatility=0.0
            )

    async def get_price_estimate(self, category: DataCategory,
                               data_quality: float = 0.5,
                               data_size_mb: float = 1.0,
                               demand_factor: float = 1.0) -> Dict[str, Any]:
        """
        Get price estimate for a dataset.

        Args:
            category: Data category
            data_quality: Quality score (0-1)
            data_size_mb: Size in MB
            demand_factor: Current demand multiplier

        Returns:
            Price estimate with confidence
        """
        try:
            oracle_price = self.category_prices.get(category)
            if not oracle_price:
                return {"error": f"No price data for category {category.value}"}

            # Calculate dynamic price based on factors
            base_price = oracle_price.market_price

            # Quality multiplier (0.5x to 2x)
            quality_multiplier = 0.5 + (data_quality * 1.5)

            # Size multiplier (logarithmic scaling)
            size_multiplier = 1.0 + (data_size_mb ** 0.3) * 0.1

            # Demand multiplier
            demand_multiplier = demand_factor

            # Calculate final price
            estimated_price = base_price * quality_multiplier * size_multiplier * demand_multiplier

            # Apply volatility bounds
            min_price = base_price * (1 - oracle_price.volatility)
            max_price = base_price * (1 + oracle_price.volatility)
            estimated_price = max(min_price, min(estimated_price, max_price))

            return {
                "category": category.value,
                "base_price": round(base_price, 2),
                "estimated_price": round(estimated_price, 2),
                "quality_multiplier": round(quality_multiplier, 2),
                "size_multiplier": round(size_multiplier, 2),
                "demand_multiplier": round(demand_multiplier, 2),
                "confidence": round(oracle_price.confidence, 2),
                "data_points": oracle_price.data_points,
                "last_updated": oracle_price.last_updated.isoformat(),
                "price_range": {
                    "min": round(min_price, 2),
                    "max": round(max_price, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error getting price estimate: {e}")
            return {"error": str(e)}

    async def record_transaction(self, listing_id: str, category: DataCategory,
                               price: float, volume: int = 1):
        """
        Record a marketplace transaction for price learning.

        Args:
            listing_id: Listing ID
            category: Data category
            price: Transaction price
            volume: Transaction volume
        """
        try:
            data_point = PriceDataPoint(
                dataset_hash=listing_id,
                category=category,
                price=price,
                volume=volume,
                timestamp=datetime.now(),
                source=OracleSource.MARKET_TRANSACTIONS,
                confidence=0.8  # High confidence for actual transactions
            )

            # Add to history
            if listing_id not in self.price_history:
                self.price_history[listing_id] = []
            self.price_history[listing_id].append(data_point)

            # Update category price
            await self._update_category_price(category)

            logger.info(f"📊 Recorded transaction: {price} DracmaS for {category.value}")

        except Exception as e:
            logger.error(f"Error recording transaction: {e}")

    async def record_federated_contribution(self, node_id: str, category: DataCategory,
                                          contribution_value: float, quality_score: float):
        """
        Record federated learning contribution for price signals.

        Args:
            node_id: Contributing node ID
            category: Data category
            contribution_value: Value of contribution
            quality_score: Quality score
        """
        try:
            # Convert contribution to price signal
            price_signal = contribution_value * quality_score * 0.1  # Scale down

            data_point = PriceDataPoint(
                dataset_hash=f"fed_{node_id}_{int(time.time())}",
                category=category,
                price=price_signal,
                volume=1,
                timestamp=datetime.now(),
                source=OracleSource.FEDERATED_CONTRIBUTIONS,
                confidence=quality_score * 0.6  # Lower confidence for indirect signals
            )

            # Add to category history
            category_key = f"category_{category.value}"
            if category_key not in self.price_history:
                self.price_history[category_key] = []
            self.price_history[category_key].append(data_point)

            # Update category price
            await self._update_category_price(category)

        except Exception as e:
            logger.error(f"Error recording federated contribution: {e}")

    async def _update_category_price(self, category: DataCategory):
        """Update aggregated price for a category."""
        try:
            # Get recent data points
            cutoff_time = datetime.now() - timedelta(days=self.history_window_days)
            category_key = f"category_{category.value}"

            all_points = []
            # Get category-specific points
            if category_key in self.price_history:
                all_points.extend(self.price_history[category_key])

            # Get points from actual listings in this category
            for listing_points in self.price_history.values():
                for point in listing_points:
                    if point.category == category and point.timestamp > cutoff_time:
                        all_points.append(point)

            if len(all_points) < self.min_data_points:
                return  # Not enough data

            # Calculate weighted average price
            total_weight = 0
            weighted_sum = 0

            for point in all_points:
                weight = point.confidence * point.volume
                weighted_sum += point.price * weight
                total_weight += weight

            if total_weight == 0:
                return

            market_price = weighted_sum / total_weight

            # Calculate volatility (coefficient of variation)
            prices = [p.price for p in all_points]
            if len(prices) > 1:
                volatility = statistics.stdev(prices) / statistics.mean(prices)
                volatility = min(volatility, self.max_volatility)
            else:
                volatility = 0.0

            # Calculate confidence based on data points and recency
            confidence = min(len(all_points) / 20, 1.0)  # Max confidence at 20 points

            # Update oracle price
            oracle_price = self.category_prices[category]
            oracle_price.market_price = market_price
            oracle_price.suggested_price = market_price
            oracle_price.confidence = confidence
            oracle_price.last_updated = datetime.now()
            oracle_price.data_points = len(all_points)
            oracle_price.volatility = volatility

            logger.info(f"📈 Updated {category.value} price: {market_price:.2f} DracmaS (confidence: {confidence:.2f})")

        except Exception as e:
            logger.error(f"Error updating category price: {e}")

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overview of all market prices."""
        try:
            overview = {}
            for category, oracle_price in self.category_prices.items():
                overview[category.value] = {
                    "base_price": round(oracle_price.base_price, 2),
                    "market_price": round(oracle_price.market_price, 2),
                    "suggested_price": round(oracle_price.suggested_price, 2),
                    "confidence": round(oracle_price.confidence, 2),
                    "data_points": oracle_price.data_points,
                    "volatility": round(oracle_price.volatility, 2),
                    "last_updated": oracle_price.last_updated.isoformat()
                }

            return {
                "categories": overview,
                "total_data_points": sum(len(points) for points in self.price_history.values()),
                "last_update": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {"error": str(e)}

    async def predict_price_trend(self, category: DataCategory, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Predict price trend for a category.

        Args:
            category: Data category
            days_ahead: Days to predict ahead

        Returns:
            Price trend prediction
        """
        try:
            category_key = f"category_{category.value}"
            if category_key not in self.price_history:
                return {"trend": "insufficient_data"}

            points = self.price_history[category_key]
            if len(points) < 10:
                return {"trend": "insufficient_data"}

            # Sort by timestamp
            points.sort(key=lambda x: x.timestamp)

            # Simple linear regression for trend
            x_values = [(p.timestamp - points[0].timestamp).total_seconds() / 86400 for p in points]
            y_values = [p.price for p in points]

            if len(x_values) < 2:
                return {"trend": "stable"}

            # Calculate slope
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_xx = sum(x * x for x in x_values)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

            # Predict future price
            last_x = x_values[-1]
            current_price = y_values[-1]
            future_price = current_price + slope * days_ahead

            trend = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"

            return {
                "trend": trend,
                "slope": round(slope, 4),
                "current_price": round(current_price, 2),
                "predicted_price": round(future_price, 2),
                "confidence": min(len(points) / 30, 1.0)
            }

        except Exception as e:
            logger.error(f"Error predicting price trend: {e}")
            return {"trend": "error", "error": str(e)}

    def export_price_data(self, filename: str):
        """Export price data for analysis."""
        try:
            data = {
                "price_history": {},
                "category_prices": {},
                "exported_at": datetime.now().isoformat()
            }

            # Export price history
            for key, points in self.price_history.items():
                data["price_history"][key] = [
                    {
                        "dataset_hash": p.dataset_hash,
                        "category": p.category.value,
                        "price": p.price,
                        "volume": p.volume,
                        "timestamp": p.timestamp.isoformat(),
                        "source": p.source.value,
                        "confidence": p.confidence
                    }
                    for p in points
                ]

            # Export category prices
            for category, oracle_price in self.category_prices.items():
                data["category_prices"][category.value] = {
                    "base_price": oracle_price.base_price,
                    "market_price": oracle_price.market_price,
                    "suggested_price": oracle_price.suggested_price,
                    "confidence": oracle_price.confidence,
                    "last_updated": oracle_price.last_updated.isoformat(),
                    "data_points": oracle_price.data_points,
                    "volatility": oracle_price.volatility
                }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"📊 Exported price data to {filename}")

        except Exception as e:
            logger.error(f"Error exporting price data: {e}")

    def import_price_data(self, filename: str):
        """Import price data from file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            # Import price history
            for key, points_data in data.get("price_history", {}).items():
                self.price_history[key] = []
                for point_data in points_data:
                    point_data["category"] = DataCategory(point_data["category"])
                    point_data["source"] = OracleSource(point_data["source"])
                    point_data["timestamp"] = datetime.fromisoformat(point_data["timestamp"])
                    self.price_history[key].append(PriceDataPoint(**point_data))

            # Import category prices
            for cat_name, price_data in data.get("category_prices", {}).items():
                category = DataCategory(cat_name)
                price_data["category"] = category
                price_data["last_updated"] = datetime.fromisoformat(price_data["last_updated"])
                self.category_prices[category] = OraclePrice(**price_data)

            logger.info(f"📊 Imported price data from {filename}")

        except Exception as e:
            logger.error(f"Error importing price data: {e}")


# Global price oracle instance
price_oracle = PriceOracle()


async def get_dataset_price_estimate(category: str, quality: float = 0.5,
                                   size_mb: float = 1.0) -> Dict[str, Any]:
    """
    Convenience function to get price estimate.

    Args:
        category: Data category string
        quality: Quality score (0-1)
        size_mb: Size in MB

    Returns:
        Price estimate
    """
    try:
        data_category = DataCategory(category)
        return await price_oracle.get_price_estimate(data_category, quality, size_mb)
    except ValueError:
        return {"error": f"Invalid category: {category}"}


def get_market_overview() -> Dict[str, Any]:
    """Get market overview (synchronous wrapper)."""
    try:
        # Run async function in new event loop if needed
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(price_oracle.get_market_overview())
        loop.close()
        return result
    except Exception as e:
        return {"error": str(e)}