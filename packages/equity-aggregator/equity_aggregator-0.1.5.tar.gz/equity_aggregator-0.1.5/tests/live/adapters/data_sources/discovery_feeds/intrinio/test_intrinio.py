# intrinio/test_intrinio.py

import os

import httpx
import pytest

from equity_aggregator.adapters.data_sources.discovery_feeds.intrinio._utils import (
    parse_companies_response,
    parse_securities_response,
)
from equity_aggregator.adapters.data_sources.discovery_feeds.intrinio.intrinio import (
    _INTRINIO_COMPANIES_URL,
)
from equity_aggregator.schemas.feeds import IntrinioFeedData

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.getenv("INTRINIO_API_KEY"),
        reason="INTRINIO_API_KEY environment variable not set",
    ),
]

_HTTP_OK = 200


def _get_api_key() -> str:
    return os.getenv("INTRINIO_API_KEY", "")


async def test_intrinio_endpoint_returns_ok() -> None:
    """
    ARRANGE: live Intrinio companies API endpoint
    ACT:     send GET request
    ASSERT:  returns HTTP 200
    """
    params = {"api_key": _get_api_key(), "page_size": "10"}

    async with httpx.AsyncClient() as client:
        response = await client.get(_INTRINIO_COMPANIES_URL, params=params)

    assert response.status_code == _HTTP_OK


async def test_intrinio_record_validates_against_schema() -> None:
    """
    ARRANGE: security record from live Intrinio API response
    ACT:     validate with IntrinioFeedData schema
    ASSERT:  no ValidationError raised
    """
    params = {"api_key": _get_api_key(), "page_size": "10"}

    async with httpx.AsyncClient() as client:
        response = await client.get(_INTRINIO_COMPANIES_URL, params=params)

    records, _ = parse_companies_response(response.json())
    first_company = records[0]
    ticker = first_company["company_ticker"]
    securities_url = f"{_INTRINIO_COMPANIES_URL}/{ticker}/securities"

    async with httpx.AsyncClient() as client:
        securities_response = await client.get(
            securities_url,
            params={"api_key": _get_api_key()},
        )

    security_records = parse_securities_response(securities_response.json())

    if not security_records:
        pytest.skip("No securities found for first company")

    assert IntrinioFeedData.model_validate(security_records[0])
