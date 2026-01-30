# yfinance/test_yfinance.py

from collections.abc import AsyncGenerator

import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.api import (
    get_quote_summary,
    search_quotes,
)
from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.config import (
    FeedConfig,
)
from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.session import (
    YFSession,
)
from equity_aggregator.schemas.feeds import YFinanceFeedData

pytestmark = pytest.mark.live

_TEST_TICKER = "AAPL"
_TEST_QUERY = "Apple"


@pytest.fixture
async def yf_session() -> AsyncGenerator[YFSession, None]:
    """
    Provide a YFSession for tests.
    """
    config = FeedConfig()
    session = YFSession(config)
    yield session
    await session.aclose()


async def test_yfinance_search_returns_quotes(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance search API via YFSession
    ACT:     search for a known query
    ASSERT:  returns non-empty list of quotes
    """
    quotes = await search_quotes(yf_session, _TEST_QUERY)

    assert isinstance(quotes, list) and len(quotes) > 0


async def test_yfinance_search_quote_has_symbol(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance search API via YFSession
    ACT:     search and inspect first quote
    ASSERT:  quote contains 'symbol' key
    """
    quotes = await search_quotes(yf_session, _TEST_QUERY)
    first_quote = quotes[0]

    assert "symbol" in first_quote


async def test_yfinance_search_quote_has_quote_type(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance search API via YFSession
    ACT:     search and inspect first quote
    ASSERT:  quote contains 'quoteType' key with value 'EQUITY'
    """
    quotes = await search_quotes(yf_session, _TEST_QUERY)
    first_quote = quotes[0]

    assert first_quote.get("quoteType") == "EQUITY"


async def test_yfinance_search_quote_has_short_name(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance search API via YFSession
    ACT:     search and inspect first quote
    ASSERT:  quote contains 'shortname' key
    """
    quotes = await search_quotes(yf_session, _TEST_QUERY)
    first_quote = quotes[0]

    assert "shortname" in first_quote


async def test_yfinance_quote_summary_returns_data(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary for known ticker
    ASSERT:  returns non-empty dict
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert isinstance(data, dict) and len(data) > 0


async def test_yfinance_quote_summary_has_quote_type(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect
    ASSERT:  contains 'quoteType' field
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert "quoteType" in data


async def test_yfinance_quote_summary_quote_type_is_equity(
    yf_session: YFSession,
) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect quoteType
    ASSERT:  quoteType is 'EQUITY'
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert data.get("quoteType") == "EQUITY"


async def test_yfinance_quote_summary_has_long_name(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect
    ASSERT:  contains 'longName' or 'shortName' field
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert data.get("longName") or data.get("shortName")


async def test_yfinance_quote_summary_has_symbol(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect
    ASSERT:  contains 'symbol' or 'underlyingSymbol' field
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert data.get("symbol") or data.get("underlyingSymbol")


async def test_yfinance_quote_summary_has_currency(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect
    ASSERT:  contains 'currency' field
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert "currency" in data


async def test_yfinance_quote_summary_has_market_cap(yf_session: YFSession) -> None:
    """
    ARRANGE: live Yahoo Finance quote summary API via YFSession
    ACT:     fetch quote summary and inspect
    ASSERT:  contains 'marketCap' field
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    assert "marketCap" in data


async def test_yfinance_quote_summary_validates_against_schema(
    yf_session: YFSession,
) -> None:
    """
    ARRANGE: quote summary from live Yahoo Finance API
    ACT:     validate with YFinanceFeedData schema
    ASSERT:  no ValidationError raised
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)

    try:
        YFinanceFeedData.model_validate(data)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_yfinance_schema_produces_expected_fields() -> None:
    """
    ARRANGE: YFinanceFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has expected schema fields
    """
    expected_fields = {
        "name",
        "symbol",
        "currency",
        "last_price",
        "market_cap",
        "fifty_two_week_min",
        "fifty_two_week_max",
        "dividend_yield",
        "market_volume",
        "held_insiders",
        "held_institutions",
        "short_interest",
        "share_float",
        "shares_outstanding",
        "revenue_per_share",
        "profit_margin",
        "gross_margin",
        "operating_margin",
        "free_cash_flow",
        "operating_cash_flow",
        "return_on_equity",
        "return_on_assets",
        "performance_1_year",
        "total_debt",
        "revenue",
        "ebitda",
        "trailing_pe",
        "price_to_book",
        "trailing_eps",
        "analyst_rating",
        "industry",
        "sector",
    }

    assert set(YFinanceFeedData.model_fields.keys()) == expected_fields


async def test_yfinance_schema_extracts_symbol(yf_session: YFSession) -> None:
    """
    ARRANGE: quote summary from live Yahoo Finance API, validated
    ACT:     compare to schema's symbol field
    ASSERT:  symbol field matches expected ticker
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)
    feed_data = YFinanceFeedData.model_validate(data)

    assert feed_data.symbol == _TEST_TICKER


async def test_yfinance_schema_extracts_name(yf_session: YFSession) -> None:
    """
    ARRANGE: quote summary from live Yahoo Finance API, validated
    ACT:     inspect name field
    ASSERT:  name field is non-empty string
    """
    data = await get_quote_summary(yf_session, _TEST_TICKER)
    feed_data = YFinanceFeedData.model_validate(data)

    assert isinstance(feed_data.name, str) and len(feed_data.name) > 0
