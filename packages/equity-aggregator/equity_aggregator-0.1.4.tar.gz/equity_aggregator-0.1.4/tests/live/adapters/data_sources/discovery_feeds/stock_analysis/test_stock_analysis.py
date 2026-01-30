# stock_analysis/test_stock_analysis.py

import httpx
import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.discovery_feeds.stock_analysis import (
    stock_analysis,
)
from equity_aggregator.schemas.feeds import StockAnalysisFeedData

pytestmark = pytest.mark.live

_HTTP_OK = 200


async def test_stock_analysis_endpoint_returns_ok() -> None:
    """
    ARRANGE: live Stock Analysis screener API endpoint
    ACT:     send GET request
    ASSERT:  returns HTTP 200
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    assert response.status_code == _HTTP_OK


async def test_stock_analysis_response_contains_data_key() -> None:
    """
    ARRANGE: live Stock Analysis API response
    ACT:     parse JSON payload
    ASSERT:  contains 'data' key
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()

    assert "data" in payload


async def test_stock_analysis_response_contains_nested_data() -> None:
    """
    ARRANGE: live Stock Analysis API response
    ACT:     parse JSON payload
    ASSERT:  contains nested 'data.data' array
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})

    assert "data" in data_wrapper


async def test_stock_analysis_response_data_is_non_empty_list() -> None:
    """
    ARRANGE: live Stock Analysis API response
    ACT:     extract nested data array
    ASSERT:  is a non-empty list
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])

    assert isinstance(records, list) and len(records) > 0


async def test_stock_analysis_record_has_symbol_field() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response
    ACT:     inspect record keys
    ASSERT:  contains 's' key (symbol)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]

    assert "s" in first_record


async def test_stock_analysis_record_has_name_field() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response
    ACT:     inspect record keys
    ASSERT:  contains 'n' key (name)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]

    assert "n" in first_record


async def test_stock_analysis_record_symbol_is_string() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response
    ACT:     extract symbol field
    ASSERT:  symbol is a non-empty string
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]
    symbol = first_record.get("s")

    assert isinstance(symbol, str) and len(symbol) > 0


async def test_stock_analysis_record_name_is_string() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response
    ACT:     extract name field
    ASSERT:  name is a non-empty string
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]
    name = first_record.get("n")

    assert isinstance(name, str) and len(name) > 0


async def test_stock_analysis_record_validates_against_schema() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response
    ACT:     validate with StockAnalysisFeedData schema
    ASSERT:  no ValidationError raised
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]

    try:
        StockAnalysisFeedData.model_validate(first_record)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_stock_analysis_schema_produces_expected_fields() -> None:
    """
    ARRANGE: StockAnalysisFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has expected schema fields
    """
    expected_fields = {
        "name",
        "symbol",
        "cusip",
        "isin",
        "market_cap",
        "last_price",
        "market_volume",
        "trailing_pe",
        "sector",
        "industry",
        "revenue",
        "free_cash_flow",
        "return_on_equity",
        "return_on_assets",
        "ebitda",
    }

    assert set(StockAnalysisFeedData.model_fields.keys()) == expected_fields


async def test_stock_analysis_schema_maps_s_to_symbol() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response, validated
    ACT:     compare 's' to schema's symbol field
    ASSERT:  symbol field matches 's'
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]
    feed_data = StockAnalysisFeedData.model_validate(first_record)

    assert feed_data.symbol == first_record["s"]


async def test_stock_analysis_schema_maps_n_to_name() -> None:
    """
    ARRANGE: first record from live Stock Analysis API response, validated
    ACT:     compare 'n' to schema's name field
    ASSERT:  name field matches 'n'
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            stock_analysis._STOCK_ANALYSIS_SEARCH_URL,
            params=stock_analysis._PARAMS,
        )

    payload = response.json()
    data_wrapper = payload.get("data", {})
    records = data_wrapper.get("data", [])
    first_record = records[0]
    feed_data = StockAnalysisFeedData.model_validate(first_record)

    assert feed_data.name == first_record["n"]
