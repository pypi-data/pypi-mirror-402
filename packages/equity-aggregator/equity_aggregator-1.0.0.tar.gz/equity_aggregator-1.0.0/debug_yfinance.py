#!/usr/bin/env python3
"""
Debug script to investigate Yahoo Finance API responses for specific tickers.

This script tests the YFinance endpoints:
1. search_url - Search for ticker/company name
2. quote_summary_url - Detailed quote data endpoint
3. Validation - Test Pydantic validation and show failures

Usage:
    uv run python debug_yfinance.py BKSC
    uv run python debug_yfinance.py AAPL
    uv run python debug_yfinance.py CMC
"""

import asyncio
import json
import sys

from pydantic import ValidationError

from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.api.quote_summary import (
    _get_quote_summary_fallback,
    get_quote_summary,
)
from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.config import (
    FeedConfig,
)
from equity_aggregator.adapters.data_sources.enrichment_feeds.yfinance.session import (
    YFSession,
)
from equity_aggregator.schemas.feeds.yfinance_feed_data import YFinanceFeedData
from equity_aggregator.schemas.raw import RawEquity


async def debug_ticker(
    ticker: str, query: str | None = None, isin: str | None = None, export: bool = False
) -> None:
    """
    Debug Yahoo Finance API endpoints for a specific ticker.

    Args:
        ticker: The ticker symbol to query (e.g., "BKSC", "AAPL")
        query: Optional search query (defaults to ticker if not provided)
        isin: Optional ISIN to test identifier-based lookup flow
        export: Whether to export raw API responses to JSON files
    """
    query = query or ticker

    config = FeedConfig()

    print("=" * 80)
    print(f"DEBUGGING TICKER: {ticker}")
    print(f"SEARCH QUERY: {query}")
    if isin:
        print(f"ISIN: {isin}")
    print("=" * 80)
    print()

    session = YFSession(config)

    try:
        # ===================================================================
        # TEST 1: Search URL
        # ===================================================================
        print("📍 TEST 1: SEARCH URL")
        print(f"   URL: {config.search_url}")
        print(f"   Query: {query}")
        print("-" * 80)

        try:
            search_response = await session.get(
                config.search_url,
                params={"q": query},
            )
            print(f"   ✓ Status Code: {search_response.status_code}")

            search_data = search_response.json()

            # Export search data if requested
            if export:
                import os

                export_path = "documentation/reference_data/yfinance_search_equity.json"
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                with open(export_path, "w") as f:
                    json.dump(search_data, f, indent=2)
                print(f"   ✓ Exported to {export_path}")
            quotes = search_data.get("quotes", [])
            print(f"   ✓ Found {len(quotes)} results")

            if quotes:
                print("\n   Results:")
                for i, quote in enumerate(quotes[:5], 1):  # Show first 5
                    symbol = quote.get("symbol", "N/A")
                    name = quote.get("longName") or quote.get("shortName", "N/A")
                    quote_type = quote.get("quoteType", "N/A")
                    exchange = quote.get("exchange", "N/A")
                    print(f"   {i}. {symbol} - {name}")
                    print(f"      Type: {quote_type}, Exchange: {exchange}")
            else:
                print("   ⚠ No results found")

        except Exception as e:
            print(f"   ✗ ERROR: {e}")

        print()

        # ===================================================================
        # TEST 2: Quote Summary URL (Primary)
        # ===================================================================
        print("📍 TEST 2: QUOTE SUMMARY URL (PRIMARY)")
        print(f"   URL: {config.quote_summary_primary_url}{ticker}")
        print(f"   Modules: {len(config.modules)} modules requested")
        print("-" * 80)

        try:
            summary_url = config.quote_summary_primary_url + ticker
            # Add 30-second timeout to prevent hanging
            summary_response = await asyncio.wait_for(
                session.get(
                    summary_url,
                    params={
                        "modules": ",".join(config.modules),
                        "corsDomain": "finance.yahoo.com",
                        "formatted": "false",
                        "symbol": ticker,
                        "lang": "en-US",
                        "region": "US",
                    },
                ),
                timeout=30.0,
            )

            print(f"   ✓ Status Code: {summary_response.status_code}")
            print(
                f"   ✓ Content-Type: {summary_response.headers.get('content-type', 'N/A')}"
            )
            print(f"   ✓ Content-Length: {len(summary_response.content)} bytes")

            if summary_response.status_code == 200:
                summary_data = summary_response.json()

                # Export quote summary data if requested
                if export:
                    import os

                    export_path = "documentation/reference_data/yfinance_quote_summary_equity.json"
                    os.makedirs(os.path.dirname(export_path), exist_ok=True)
                    with open(export_path, "w") as f:
                        json.dump(summary_data, f, indent=2)
                    print(f"   ✓ Exported to {export_path}")

                result = summary_data.get("quoteSummary", {}).get("result", [])
                error = summary_data.get("quoteSummary", {}).get("error")

                if error:
                    print(f"   ✗ API Error: {error}")
                elif result:
                    print(f"   ✓ Data received for {len(result)} ticker(s)")

                    # Show available modules
                    modules_present = list(result[0].keys())
                    print(
                        f"   ✓ Available modules ({len(modules_present)}): {', '.join(modules_present)}"
                    )

                    # Flatten all module data to get total field count
                    all_fields = {}
                    for module_name in modules_present:
                        module_data = result[0].get(module_name)
                        if isinstance(module_data, dict):
                            all_fields.update(module_data)

                    print(f"   ✓ Total flattened fields: {len(all_fields)}")
                    print(f"\n   All fields from quote_summary_url:")
                    for field_name in sorted(all_fields.keys()):
                        value = all_fields[field_name]
                        # Truncate long values
                        if isinstance(value, (dict, list)):
                            value_str = str(type(value).__name__)
                        else:
                            value_str = str(value)[:50]
                        print(f"      {field_name}: {value_str}")
                else:
                    print("   ⚠ Empty result array")
                    print(
                        f"   Raw response: {json.dumps(summary_data, indent=2)[:500]}..."
                    )
            else:
                print(f"   ✗ Non-200 status code")
                print(f"   Response preview: {summary_response.text[:500]}...")

        except Exception as e:
            print(f"   ✗ ERROR: {e}")

        print()

        # ===================================================================
        # TEST 3: Quote Summary Fallback URL
        # ===================================================================
        print("📍 TEST 3: QUOTE SUMMARY FALLBACK URL")
        print(f"   URL: {config.quote_summary_fallback_url}")
        print(f"   Ticker: {ticker}")
        print("-" * 80)

        try:
            fallback_data = await _get_quote_summary_fallback(session, ticker)

            if fallback_data:
                print(f"   ✓ Data received for ticker")
                print(f"   ✓ Total fields: {len(fallback_data)}")

                print(f"\n   All fields from quote_summary_fallback_url:")
                for field_name in sorted(fallback_data.keys()):
                    value = fallback_data[field_name]
                    # Truncate long values
                    if isinstance(value, (dict, list)):
                        value_str = str(type(value).__name__)
                    else:
                        value_str = str(value)[:50]
                    print(f"      {field_name}: {value_str}")

                # Compare with primary endpoint
                print(f"\n   📊 FIELD COMPARISON:")
                print(f"   Primary endpoint would have returned flattened module data")
                print(
                    f"   Fallback endpoint returns {len(fallback_data)} direct fields"
                )

        except Exception as e:
            print(f"   ✗ ERROR: {e}")

        print()

        # ===================================================================
        # TEST 3.5: ISIN-based Lookup (Pipeline Simulation)
        # ===================================================================
        if isin:
            print("📍 TEST 3.5: ISIN-BASED LOOKUP (PIPELINE SIMULATION)")
            print(
                "   Simulating actual pipeline flow: search by ISIN → get symbol → fetch data"
            )
            print("-" * 80)

            try:
                # Search for the ISIN
                isin_search_response = await session.get(
                    config.search_url,
                    params={"q": isin},
                )
                isin_search_data = isin_search_response.json()
                isin_quotes = isin_search_data.get("quotes", [])

                # Filter for EQUITY type only (like search_quotes does)
                isin_equities = [
                    q for q in isin_quotes if q.get("quoteType") == "EQUITY"
                ]

                print(f"   ✓ Searched for ISIN: {isin}")
                print(f"   ✓ Found {len(isin_equities)} EQUITY results")

                if isin_equities:
                    print("\n   ISIN Search Results:")
                    for i, quote in enumerate(isin_equities, 1):
                        symbol = quote.get("symbol", "N/A")
                        name = quote.get("longname") or quote.get("shortname", "N/A")
                        exchange = quote.get("exchange", "N/A")
                        print(f"   {i}. {symbol} ({exchange}) - {name}")

                    # Pick the first equity (simplified - pipeline does fuzzy matching)
                    chosen_symbol = isin_equities[0].get("symbol")
                    print(f"\n   → Pipeline would fetch data for: {chosen_symbol}")

                    # Now fetch quote summary for this symbol
                    print(f"\n   Fetching quote summary for {chosen_symbol}...")
                    isin_raw_data = await get_quote_summary(session, chosen_symbol)

                    if isin_raw_data:
                        print(f"   ✓ Data fetched: {len(isin_raw_data)} fields")

                        # Validate this data
                        print(f"\n   Validating data from ISIN-based lookup...")
                        try:
                            yf_data = YFinanceFeedData.model_validate(isin_raw_data)
                            coerced = yf_data.model_dump()
                            _ = RawEquity.model_validate(coerced)
                            print(f"   ✓ Validation PASSED for {chosen_symbol}")
                        except ValidationError as ve:
                            print(f"   ✗ Validation FAILED for {chosen_symbol}")
                            print(
                                f"\n   ⚠️  THIS IS THE ACTUAL VALIDATION FAILURE IN THE PIPELINE!"
                            )
                            print(f"\n   Failed fields ({len(ve.errors())}):")
                            for err in ve.errors():
                                field_name = err["loc"][0] if err["loc"] else "unknown"
                                error_msg = err["msg"]

                                # Try to get value from either stage
                                if field_name in coerced:
                                    raw_value = coerced.get(field_name)
                                else:
                                    raw_value = isin_raw_data.get(field_name)

                                print(f"\n      ❌ Field: {field_name}")
                                print(f"         Error: {error_msg}")
                                print(f"         Raw value: {raw_value!r}")
                                print(
                                    f"         Value type: {type(raw_value).__name__}"
                                )

                                # Show related fields
                                if field_name in ["revenue", "revenue_per_share"]:
                                    print(f"         Related fields:")
                                    for related in ["totalRevenue", "revenuePerShare"]:
                                        if related in isin_raw_data:
                                            print(
                                                f"           {related}: {isin_raw_data[related]!r}"
                                            )
                                elif field_name == "trailing_pe":
                                    print(f"         Related fields:")
                                    for related in ["trailingPE", "forwardPE"]:
                                        if related in isin_raw_data:
                                            print(
                                                f"           {related}: {isin_raw_data[related]!r}"
                                            )
                else:
                    print("   ⚠ No EQUITY results found for ISIN")

            except Exception as e:
                print(f"   ✗ ERROR: {e}")
                import traceback

                traceback.print_exc()

            print()

        # ===================================================================
        # TEST 4: Validation Testing
        # ===================================================================
        print("📍 TEST 4: VALIDATION TESTING (Direct Symbol Lookup)")
        print("   Testing Pydantic validation against YFinanceFeedData schema")
        print("-" * 80)

        try:
            # Fetch raw data using the quote_summary function
            raw_data = await get_quote_summary(session, ticker)

            if not raw_data:
                print("   ⚠ No data returned from get_quote_summary()")
            else:
                print(f"   ✓ Raw data fetched: {len(raw_data)} fields")

                # Step 1: Try validating with YFinanceFeedData
                print("\n   Step 1: Validating with YFinanceFeedData model...")
                try:
                    yf_data = YFinanceFeedData.model_validate(raw_data)
                    print("   ✓ YFinanceFeedData validation PASSED")

                    # Step 2: Try converting to RawEquity
                    print("\n   Step 2: Converting to RawEquity model...")
                    try:
                        coerced = yf_data.model_dump()
                        _ = RawEquity.model_validate(coerced)
                        print("   ✓ RawEquity validation PASSED")
                        print(f"   ✓ All validation successful for ticker {ticker}")

                    except ValidationError as ve:
                        print("   ✗ RawEquity validation FAILED")
                        print(f"\n   Failed fields ({len(ve.errors())}):")
                        for err in ve.errors():
                            field_name = err["loc"][0] if err["loc"] else "unknown"
                            error_type = err["type"]
                            error_msg = err["msg"]

                            # Get the actual raw value that failed
                            raw_value = coerced.get(field_name, "<not found>")

                            print(f"\n      ❌ Field: {field_name}")
                            print(f"         Error: {error_msg}")
                            print(f"         Type: {error_type}")
                            print(f"         Raw value: {raw_value!r}")
                            print(f"         Value type: {type(raw_value).__name__}")

                except ValidationError as ve:
                    print("   ✗ YFinanceFeedData validation FAILED")
                    print(f"\n   Failed fields ({len(ve.errors())}):")
                    for err in ve.errors():
                        field_name = err["loc"][0] if err["loc"] else "unknown"
                        error_type = err["type"]
                        error_msg = err["msg"]

                        # Get the actual raw value that failed
                        raw_value = raw_data.get(field_name, "<not found>")

                        print(f"\n      ❌ Field: {field_name}")
                        print(f"         Error: {error_msg}")
                        print(f"         Type: {error_type}")
                        print(f"         Raw value: {raw_value!r}")
                        print(f"         Value type: {type(raw_value).__name__}")

                        # Show context: what other related fields look like
                        if field_name in ["revenue", "revenue_per_share"]:
                            print(f"         Related fields:")
                            for related in [
                                "totalRevenue",
                                "revenuePerShare",
                                "revenue",
                                "revenue_per_share",
                            ]:
                                if related in raw_data:
                                    print(
                                        f"           {related}: {raw_data[related]!r}"
                                    )
                        elif field_name == "trailing_pe":
                            print(f"         Related fields:")
                            for related in ["trailingPE", "trailing_pe", "forwardPE"]:
                                if related in raw_data:
                                    print(
                                        f"           {related}: {raw_data[related]!r}"
                                    )

        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            import traceback

            traceback.print_exc()

        print()
        print("=" * 80)
        print("DEBUG COMPLETE")
        print("=" * 80)

    finally:
        await session.aclose()


async def main() -> None:
    """Main entry point for the debug script."""
    if len(sys.argv) < 2:
        print(
            "Usage: uv run python debug_yfinance.py TICKER [QUERY] [--isin ISIN] [--export]"
        )
        print("\nExamples:")
        print("  uv run python debug_yfinance.py BKSC")
        print("  uv run python debug_yfinance.py AIT --isin GG00BB0RDB98")
        print("  uv run python debug_yfinance.py CMC --isin GB00BL6NGV24")
        print("  uv run python debug_yfinance.py AAPL --export")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    query = None
    isin = None
    export = False

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--isin" and i + 1 < len(sys.argv):
            isin = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--export":
            export = True
            i += 1
        else:
            query = sys.argv[i]
            i += 1

    await debug_ticker(ticker, query, isin, export)


if __name__ == "__main__":
    asyncio.run(main())
