# sec/test_sec.py

import httpx
import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.discovery_feeds.sec.sec import (
    _HEADERS,
    _SEC_SEARCH_URL,
    EXCHANGE_TO_MIC,
    _parse_row,
)
from equity_aggregator.schemas.feeds import SecFeedData

pytestmark = pytest.mark.live

_HTTP_OK = 200
_CIK_STRING_LENGTH = 10


async def test_sec_endpoint_returns_ok() -> None:
    """
    ARRANGE: live SEC API endpoint
    ACT:     send GET request
    ASSERT:  returns HTTP 200
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    assert response.status_code == _HTTP_OK


async def test_sec_response_contains_data_key() -> None:
    """
    ARRANGE: live SEC API response
    ACT:     parse JSON payload
    ASSERT:  contains 'data' key
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()

    assert "data" in payload


async def test_sec_response_data_is_non_empty_list() -> None:
    """
    ARRANGE: live SEC API response
    ACT:     extract 'data' field
    ASSERT:  is a non-empty list
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    data = payload.get("data", [])

    assert isinstance(data, list) and len(data) > 0


async def test_sec_record_has_required_fields() -> None:
    """
    ARRANGE: first row from live SEC API response
    ACT:     parse row into record
    ASSERT:  record contains cik, name, symbol, exchange, mics keys
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    assert set(record.keys()) == {"cik", "name", "symbol", "exchange", "mics"}


async def test_sec_record_cik_is_integer() -> None:
    """
    ARRANGE: first row from live SEC API response
    ACT:     extract cik from parsed record
    ASSERT:  cik is an integer
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    assert isinstance(record["cik"], int)


async def test_sec_record_name_is_string() -> None:
    """
    ARRANGE: first row from live SEC API response
    ACT:     extract name from parsed record
    ASSERT:  name is a non-empty string
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    assert isinstance(record["name"], str) and len(record["name"]) > 0


async def test_sec_record_symbol_is_string() -> None:
    """
    ARRANGE: first row from live SEC API response
    ACT:     extract symbol from parsed record
    ASSERT:  symbol is a non-empty string
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    assert isinstance(record["symbol"], str) and len(record["symbol"]) > 0


async def test_sec_record_exchange_is_known() -> None:
    """
    ARRANGE: first row from live SEC API response
    ACT:     extract exchange from parsed record
    ASSERT:  exchange is one of the known exchanges
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    known_exchanges = set(EXCHANGE_TO_MIC.keys())

    assert record["exchange"] in known_exchanges


async def test_sec_record_validates_against_schema() -> None:
    """
    ARRANGE: first row from live SEC API response, parsed into record
    ACT:     validate with SecFeedData schema
    ASSERT:  no ValidationError raised
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)

    try:
        SecFeedData.model_validate(record)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_sec_schema_produces_expected_fields() -> None:
    """
    ARRANGE: SecFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has cik, name, symbol, mics fields
    """
    assert set(SecFeedData.model_fields.keys()) == {"cik", "name", "symbol", "mics"}


async def test_sec_schema_cik_is_zero_padded_string() -> None:
    """
    ARRANGE: first row from live SEC API response, parsed and validated
    ACT:     extract cik from validated SecFeedData
    ASSERT:  cik is a 10-digit zero-padded string
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.get(_SEC_SEARCH_URL)

    payload = response.json()
    first_row = payload["data"][0]
    record = _parse_row(first_row)
    feed_data = SecFeedData.model_validate(record)

    assert isinstance(feed_data.cik, str) and len(feed_data.cik) == _CIK_STRING_LENGTH
