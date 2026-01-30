# xetra/test_xetra.py

import httpx
import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.discovery_feeds.xetra.xetra import (
    _HEADERS,
    _XETRA_SEARCH_URL,
    _build_payload,
    _extract_records,
)
from equity_aggregator.schemas.feeds import XetraFeedData

pytestmark = pytest.mark.live

_HTTP_OK = 200


async def test_xetra_endpoint_returns_ok() -> None:
    """
    ARRANGE: live XETRA API endpoint
    ACT:     send POST request
    ASSERT:  returns HTTP 200
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    assert response.status_code == _HTTP_OK


async def test_xetra_response_contains_data_key() -> None:
    """
    ARRANGE: live XETRA API response
    ACT:     parse JSON payload
    ASSERT:  contains 'data' key
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()

    assert "data" in payload


async def test_xetra_response_contains_records_total() -> None:
    """
    ARRANGE: live XETRA API response
    ACT:     parse JSON payload
    ASSERT:  contains 'recordsTotal' for pagination
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()

    assert "recordsTotal" in payload


async def test_xetra_response_data_is_non_empty_list() -> None:
    """
    ARRANGE: live XETRA API response
    ACT:     extract 'data' field
    ASSERT:  is a non-empty list
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    data = payload.get("data", [])

    assert isinstance(data, list) and len(data) > 0


async def test_xetra_raw_record_has_name_field() -> None:
    """
    ARRANGE: first raw record from live XETRA API response
    ACT:     inspect record keys
    ASSERT:  contains 'name' key with 'originalValue'
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    first_row = payload["data"][0]

    assert "name" in first_row and "originalValue" in first_row["name"]


async def test_xetra_raw_record_has_wkn_field() -> None:
    """
    ARRANGE: first raw record from live XETRA API response
    ACT:     inspect record keys
    ASSERT:  contains 'wkn' key
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    first_row = payload["data"][0]

    assert "wkn" in first_row


async def test_xetra_raw_record_has_isin_field() -> None:
    """
    ARRANGE: first raw record from live XETRA API response
    ACT:     inspect record keys
    ASSERT:  contains 'isin' key
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    first_row = payload["data"][0]

    assert "isin" in first_row


async def test_xetra_extracted_record_has_expected_fields() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response
    ACT:     inspect extracted record keys
    ASSERT:  contains expected normalised fields
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]

    expected_fields = {
        "name",
        "wkn",
        "isin",
        "slug",
        "mics",
        "currency",
        "overview",
        "performance",
        "key_data",
        "sustainability",
    }

    assert set(first_record.keys()) == expected_fields


async def test_xetra_extracted_record_name_is_string() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response
    ACT:     extract name field
    ASSERT:  name is a non-empty string
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]

    assert isinstance(first_record["name"], str) and len(first_record["name"]) > 0


async def test_xetra_extracted_record_wkn_is_string() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response
    ACT:     extract wkn (symbol) field
    ASSERT:  wkn is a string
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]

    assert isinstance(first_record["wkn"], str)


async def test_xetra_extracted_record_validates_against_schema() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response
    ACT:     validate with XetraFeedData schema
    ASSERT:  no ValidationError raised
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]

    try:
        XetraFeedData.model_validate(first_record)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_xetra_schema_produces_expected_fields() -> None:
    """
    ARRANGE: XetraFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has expected schema fields
    """
    expected_fields = {
        "name",
        "symbol",
        "isin",
        "mics",
        "currency",
        "last_price",
        "market_cap",
        "fifty_two_week_min",
        "fifty_two_week_max",
        "performance_1_year",
        "dividend_yield",
        "price_to_book",
        "trailing_eps",
    }

    assert set(XetraFeedData.model_fields.keys()) == expected_fields


async def test_xetra_schema_maps_wkn_to_symbol() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response, validated
    ACT:     compare wkn to schema's symbol field
    ASSERT:  symbol field matches original wkn
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]
    feed_data = XetraFeedData.model_validate(first_record)

    assert feed_data.symbol == first_record["wkn"]


async def test_xetra_schema_sets_mics_to_xetr() -> None:
    """
    ARRANGE: first extracted record from live XETRA API response, validated
    ACT:     inspect mics field
    ASSERT:  mics contains 'XETR'
    """
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        response = await client.post(_XETRA_SEARCH_URL, json=_build_payload(offset=0))

    payload = response.json()
    records = _extract_records(payload)
    first_record = records[0]
    feed_data = XetraFeedData.model_validate(first_record)

    assert "XETR" in feed_data.mics
