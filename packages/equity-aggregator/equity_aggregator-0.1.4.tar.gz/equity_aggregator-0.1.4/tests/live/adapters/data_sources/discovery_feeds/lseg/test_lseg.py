# lseg/test_lseg.py

import httpx
import pytest
from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.discovery_feeds.lseg._utils import (
    parse_response,
)
from equity_aggregator.adapters.data_sources.discovery_feeds.lseg.lseg import (
    _HEADERS,
    _LSEG_BASE_PARAMS,
    _LSEG_PATH,
    _LSEG_SEARCH_URL,
)
from equity_aggregator.schemas.feeds import LsegFeedData

pytestmark = pytest.mark.live

_HTTP_OK = 200
_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=None)


async def test_lseg_endpoint_returns_ok() -> None:
    """
    ARRANGE: live LSEG API endpoint
    ACT:     send GET request
    ASSERT:  returns HTTP 200
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    assert response.status_code == _HTTP_OK


async def test_lseg_response_contains_components_key() -> None:
    """
    ARRANGE: live LSEG API response
    ACT:     parse JSON payload
    ASSERT:  contains 'components' key
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()

    assert "components" in payload


async def test_lseg_response_contains_price_explorer_component() -> None:
    """
    ARRANGE: live LSEG API response
    ACT:     search for price-explorer component
    ASSERT:  component exists with type 'price-explorer'
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    components = payload.get("components", [])
    price_explorer = next(
        (c for c in components if c.get("type") == "price-explorer"),
        None,
    )

    assert price_explorer is not None


async def test_lseg_response_parses_to_records() -> None:
    """
    ARRANGE: live LSEG API response
    ACT:     parse response using parse_response
    ASSERT:  returns non-empty list of records
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)

    assert isinstance(records, list) and len(records) > 0


async def test_lseg_response_parses_to_pagination_info() -> None:
    """
    ARRANGE: live LSEG API response
    ACT:     parse response using parse_response
    ASSERT:  returns pagination info with totalPages
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    _, pagination_info = parse_response(payload)

    assert pagination_info is not None and "totalPages" in pagination_info


async def test_lseg_record_has_expected_fields() -> None:
    """
    ARRANGE: first record from live LSEG API response
    ACT:     inspect record keys
    ASSERT:  contains issuername, tidm, isin, currency, lastprice, marketcapitalization
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]

    expected_fields = {
        "issuername",
        "tidm",
        "isin",
        "currency",
        "lastprice",
        "marketcapitalization",
        "fiftyTwoWeeksMin",
        "fiftyTwoWeeksMax",
    }

    assert set(first_record.keys()) == expected_fields


async def test_lseg_record_issuername_is_string() -> None:
    """
    ARRANGE: first record from live LSEG API response
    ACT:     extract issuername field
    ASSERT:  issuername is a non-empty string
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]

    issuername = first_record["issuername"]

    assert isinstance(issuername, str) and len(issuername) > 0


async def test_lseg_record_tidm_is_string() -> None:
    """
    ARRANGE: first record from live LSEG API response
    ACT:     extract tidm (symbol) field
    ASSERT:  tidm is a non-empty string
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]

    assert isinstance(first_record["tidm"], str) and len(first_record["tidm"]) > 0


async def test_lseg_record_validates_against_schema() -> None:
    """
    ARRANGE: first record from live LSEG API response
    ACT:     validate with LsegFeedData schema
    ASSERT:  no ValidationError raised
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]

    try:
        LsegFeedData.model_validate(first_record)
        validated = True
    except ValidationError:
        validated = False

    assert validated


async def test_lseg_schema_produces_expected_fields() -> None:
    """
    ARRANGE: LsegFeedData schema class
    ACT:     inspect model fields
    ASSERT:  has expected schema fields
    """
    expected_fields = {
        "name",
        "symbol",
        "isin",
        "currency",
        "last_price",
        "market_cap",
        "fifty_two_week_min",
        "fifty_two_week_max",
    }

    assert set(LsegFeedData.model_fields.keys()) == expected_fields


async def test_lseg_schema_maps_issuername_to_name() -> None:
    """
    ARRANGE: first record from live LSEG API response, validated
    ACT:     compare issuername to schema's name field
    ASSERT:  name field matches original issuername
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]
    feed_data = LsegFeedData.model_validate(first_record)

    assert feed_data.name == first_record["issuername"]


async def test_lseg_schema_maps_tidm_to_symbol() -> None:
    """
    ARRANGE: first record from live LSEG API response, validated
    ACT:     compare tidm to schema's symbol field
    ASSERT:  symbol field matches original tidm
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        response = await client.get(
            _LSEG_SEARCH_URL,
            params={
                "path": _LSEG_PATH,
                "parameters": f"{_LSEG_BASE_PARAMS}&page=0",
            },
        )

    payload = response.json()
    records, _ = parse_response(payload)
    first_record = records[0]
    feed_data = LsegFeedData.model_validate(first_record)

    assert feed_data.symbol == first_record["tidm"]
