# tradingview/test_tradingview.py

import httpx
import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.discovery_feeds.tradingview import (
    tradingview,
)
from equity_aggregator.schemas.feeds import TradingViewFeedData

pytestmark = pytest.mark.live

_HTTP_OK = 200


def _build_request_body(start: int = 0, end: int = tradingview._PAGE_SIZE) -> dict:
    """
    Build request body with pagination range.
    """
    return {**tradingview._REQUEST_BODY_TEMPLATE, "range": [start, end]}


async def test_tradingview_endpoint_returns_ok() -> None:
    """
    ARRANGE: live TradingView scanner API endpoint
    ACT:     send POST request
    ASSERT:  returns HTTP 200
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    assert response.status_code == _HTTP_OK


async def test_tradingview_response_contains_data_key() -> None:
    """
    ARRANGE: live TradingView API response
    ACT:     parse JSON payload
    ASSERT:  contains 'data' key
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()

    assert "data" in payload


async def test_tradingview_response_contains_total_count() -> None:
    """
    ARRANGE: live TradingView API response
    ACT:     parse JSON payload
    ASSERT:  contains 'totalCount' for pagination
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()

    assert "totalCount" in payload


async def test_tradingview_response_data_is_non_empty_list() -> None:
    """
    ARRANGE: live TradingView API response
    ACT:     extract 'data' field
    ASSERT:  is a non-empty list
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    data = payload.get("data", [])

    assert isinstance(data, list) and len(data) > 0


async def test_tradingview_row_has_s_field() -> None:
    """
    ARRANGE: first row from live TradingView API response
    ACT:     inspect row keys
    ASSERT:  contains 's' key (exchange:symbol format)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]

    assert "s" in first_row


async def test_tradingview_row_has_d_field() -> None:
    """
    ARRANGE: first row from live TradingView API response
    ACT:     inspect row keys
    ASSERT:  contains 'd' key (data array)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]

    assert "d" in first_row


async def test_tradingview_data_array_has_expected_length() -> None:
    """
    ARRANGE: first row from live TradingView API response
    ACT:     inspect 'd' array length
    ASSERT:  has at least expected number of elements
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    data_array = first_row.get("d", [])

    assert len(data_array) >= tradingview._EXPECTED_ARRAY_LENGTH


async def test_tradingview_data_array_contains_symbol() -> None:
    """
    ARRANGE: first row from live TradingView API response
    ACT:     extract symbol from d[0]
    ASSERT:  symbol is a non-empty string
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    data_array = first_row.get("d", [])
    symbol = data_array[0]

    assert isinstance(symbol, str) and len(symbol) > 0


async def test_tradingview_data_array_contains_name() -> None:
    """
    ARRANGE: first row from live TradingView API response
    ACT:     extract name from d[1]
    ASSERT:  name is a non-empty string
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    data_array = first_row.get("d", [])
    name = data_array[1]

    assert isinstance(name, str) and len(name) > 0


async def test_tradingview_parse_response_returns_records() -> None:
    """
    ARRANGE: live TradingView API response
    ACT:     parse response using _parse_response
    ASSERT:  returns non-empty list of records
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    records, _ = tradingview._parse_response(payload)

    assert isinstance(records, list) and len(records) > 0


async def test_tradingview_parse_response_returns_total_count() -> None:
    """
    ARRANGE: live TradingView API response
    ACT:     parse response using _parse_response
    ASSERT:  returns positive total count
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    _, total_count = tradingview._parse_response(payload)

    assert total_count > 0


async def test_tradingview_parsed_record_has_expected_keys() -> None:
    """
    ARRANGE: first parsed record from live TradingView API response
    ACT:     inspect parsed record keys
    ASSERT:  contains 's' and 'd' keys
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    record = tradingview._parse_row(first_row)

    assert set(record.keys()) == {"s", "d"}


async def test_tradingview_record_validates_against_schema() -> None:
    """
    ARRANGE: first parsed record from live TradingView API response
    ACT:     validate with TradingViewFeedData schema
    ASSERT:  no ValidationError raised
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    record = tradingview._parse_row(first_row)

    try:
        TradingViewFeedData.model_validate(record)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_tradingview_schema_produces_expected_fields() -> None:
    """
    ARRANGE: TradingViewFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has expected schema fields
    """
    expected_fields = {
        "name",
        "symbol",
        "currency",
        "last_price",
        "market_cap",
        "market_volume",
        "dividend_yield",
        "shares_outstanding",
        "revenue",
        "ebitda",
        "trailing_pe",
        "price_to_book",
        "trailing_eps",
        "return_on_equity",
        "return_on_assets",
        "sector",
        "industry",
    }

    assert set(TradingViewFeedData.model_fields.keys()) == expected_fields


async def test_tradingview_schema_extracts_symbol_from_array() -> None:
    """
    ARRANGE: first parsed record from live TradingView API response, validated
    ACT:     compare d[0] to schema's symbol field
    ASSERT:  symbol field matches d[0]
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    record = tradingview._parse_row(first_row)
    feed_data = TradingViewFeedData.model_validate(record)

    assert feed_data.symbol == record["d"][0]


async def test_tradingview_schema_extracts_name_from_array() -> None:
    """
    ARRANGE: first parsed record from live TradingView API response, validated
    ACT:     compare d[1] to schema's name field
    ASSERT:  name field matches d[1]
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            tradingview._TRADINGVIEW_SCAN_URL,
            json=_build_request_body(),
        )

    payload = response.json()
    first_row = payload["data"][0]
    record = tradingview._parse_row(first_row)
    feed_data = TradingViewFeedData.model_validate(record)

    assert feed_data.name == record["d"][1]
