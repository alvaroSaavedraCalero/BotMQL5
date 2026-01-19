"""
News Filter Module
Filters trading during high-impact economic news events
"""

import logging
import json
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class NewsImpact(Enum):
    """News impact levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class NewsEvent:
    """Economic news event"""
    event_time: datetime
    currency: str
    event_name: str
    impact: NewsImpact
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None

    @property
    def is_high_impact(self) -> bool:
        return self.impact == NewsImpact.HIGH


class NewsFilter:
    """
    Economic Calendar News Filter

    Fetches news from multiple sources and filters
    trading during high-impact events.
    """

    # News sources
    FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    # Currency mappings
    CURRENCY_MAP = {
        'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'],
        'EUR': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD'],
        'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD'],
        'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY'],
        'CHF': ['USDCHF', 'EURCHF', 'GBPCHF', 'CHFJPY'],
        'CAD': ['USDCAD', 'EURCAD', 'GBPCAD', 'CADJPY', 'AUDCAD'],
        'AUD': ['AUDUSD', 'EURAUD', 'GBPAUD', 'AUDJPY', 'AUDCAD', 'AUDNZD'],
        'NZD': ['NZDUSD', 'AUDNZD', 'NZDJPY', 'EURNZD', 'GBPNZD'],
    }

    def __init__(self, config):
        """
        Initialize News Filter

        Args:
            config: Configuration object
        """
        self.config = config
        self.buffer_minutes = config.session.news_buffer_minutes

        # Cache
        self.events: List[NewsEvent] = []
        self.last_fetch: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)

        # Data directory
        self.cache_file = config.paths.data_dir / "news_cache.json"

        # Load cached data
        self._load_cache()

    def _load_cache(self):
        """Load cached news data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)

                self.events = [
                    NewsEvent(
                        event_time=datetime.fromisoformat(e['event_time']),
                        currency=e['currency'],
                        event_name=e['event_name'],
                        impact=NewsImpact(e['impact']),
                        actual=e.get('actual'),
                        forecast=e.get('forecast'),
                        previous=e.get('previous')
                    )
                    for e in data.get('events', [])
                ]

                last_fetch_str = data.get('last_fetch')
                if last_fetch_str:
                    self.last_fetch = datetime.fromisoformat(last_fetch_str)

                logger.info(f"Loaded {len(self.events)} cached news events")

        except Exception as e:
            logger.warning(f"Error loading news cache: {e}")
            self.events = []

    def _save_cache(self):
        """Save news data to cache"""
        try:
            data = {
                'last_fetch': self.last_fetch.isoformat() if self.last_fetch else None,
                'events': [
                    {
                        'event_time': e.event_time.isoformat(),
                        'currency': e.currency,
                        'event_name': e.event_name,
                        'impact': e.impact.value,
                        'actual': e.actual,
                        'forecast': e.forecast,
                        'previous': e.previous
                    }
                    for e in self.events
                ]
            }

            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving news cache: {e}")

    async def fetch_news(self) -> bool:
        """
        Fetch news from economic calendar

        Returns:
            bool: True if successful
        """
        # Check cache validity
        if self.last_fetch and datetime.now() - self.last_fetch < self.cache_duration:
            logger.debug("Using cached news data")
            return True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.FOREX_FACTORY_URL, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._parse_forex_factory_data(data)
                        self.last_fetch = datetime.now()
                        self._save_cache()
                        logger.info(f"Fetched {len(self.events)} news events")
                        return True
                    else:
                        logger.warning(f"Failed to fetch news: HTTP {response.status}")

        except asyncio.TimeoutError:
            logger.warning("News fetch timeout")
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

        return False

    def fetch_news_sync(self) -> bool:
        """Synchronous version of fetch_news"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.fetch_news())

    def _parse_forex_factory_data(self, data: List[Dict]):
        """
        Parse Forex Factory calendar data

        Args:
            data: Raw JSON data from API
        """
        self.events = []

        for item in data:
            try:
                # Parse date and time
                date_str = item.get('date', '')
                time_str = item.get('time', '')

                if not date_str:
                    continue

                # Handle "All Day" events
                if time_str == 'All Day' or not time_str:
                    time_str = '00:00'

                # Parse datetime
                try:
                    event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue

                # Parse impact
                impact_str = item.get('impact', 'Low').lower()
                if impact_str == 'high':
                    impact = NewsImpact.HIGH
                elif impact_str == 'medium':
                    impact = NewsImpact.MEDIUM
                else:
                    impact = NewsImpact.LOW

                # Create event
                event = NewsEvent(
                    event_time=event_time,
                    currency=item.get('country', 'USD'),
                    event_name=item.get('title', 'Unknown'),
                    impact=impact,
                    actual=item.get('actual'),
                    forecast=item.get('forecast'),
                    previous=item.get('previous')
                )

                self.events.append(event)

            except Exception as e:
                logger.debug(f"Error parsing news item: {e}")
                continue

        # Sort by time
        self.events.sort(key=lambda x: x.event_time)

    def is_news_time(self, symbol: str = None) -> bool:
        """
        Check if currently within news buffer time

        Args:
            symbol: Optional symbol to check specific currency

        Returns:
            bool: True if within news buffer
        """
        now = datetime.now()
        buffer = timedelta(minutes=self.buffer_minutes)

        for event in self.events:
            # Only check high impact events
            if not event.is_high_impact:
                continue

            # Check time window
            start_time = event.event_time - buffer
            end_time = event.event_time + buffer

            if start_time <= now <= end_time:
                # If symbol specified, check if currency affects it
                if symbol:
                    affected_pairs = self.CURRENCY_MAP.get(event.currency, [])
                    if symbol not in affected_pairs:
                        continue

                logger.info(f"News filter active: {event.event_name} ({event.currency}) at {event.event_time}")
                return True

        return False

    def get_upcoming_news(self, hours: int = 24) -> List[NewsEvent]:
        """
        Get upcoming high-impact news events

        Args:
            hours: Look-ahead window in hours

        Returns:
            List of upcoming NewsEvent objects
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)

        upcoming = [
            event for event in self.events
            if event.is_high_impact and now <= event.event_time <= cutoff
        ]

        return upcoming

    def get_next_news_event(self) -> Optional[NewsEvent]:
        """
        Get the next high-impact news event

        Returns:
            Next NewsEvent or None
        """
        now = datetime.now()

        for event in self.events:
            if event.is_high_impact and event.event_time > now:
                return event

        return None

    def get_minutes_to_news(self) -> Optional[int]:
        """
        Get minutes until next high-impact news

        Returns:
            Minutes until next news or None if none upcoming
        """
        next_event = self.get_next_news_event()
        if next_event:
            delta = next_event.event_time - datetime.now()
            return int(delta.total_seconds() / 60)

        return None

    def get_news_status(self) -> Dict:
        """Get formatted news status for display"""
        upcoming = self.get_upcoming_news(24)
        next_event = self.get_next_news_event()
        minutes_to_news = self.get_minutes_to_news()

        return {
            'is_blocked': self.is_news_time(),
            'buffer_minutes': self.buffer_minutes,
            'upcoming_count': len(upcoming),
            'next_event': {
                'time': next_event.event_time.isoformat() if next_event else None,
                'currency': next_event.currency if next_event else None,
                'name': next_event.event_name if next_event else None,
                'impact': next_event.impact.value if next_event else None
            } if next_event else None,
            'minutes_to_news': minutes_to_news,
            'last_fetch': self.last_fetch.isoformat() if self.last_fetch else None,
            'total_events': len(self.events)
        }

    def send_news_block_to_mt5(self, mt5_connector) -> bool:
        """
        Send news block status to MT5

        Args:
            mt5_connector: MT5Connector instance

        Returns:
            bool: True if successful
        """
        is_blocked = self.is_news_time()
        return mt5_connector.send_command(f"NEWS_BLOCK:{1 if is_blocked else 0}")
