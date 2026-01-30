#!/usr/bin/env python3
"""
RAG Baseline - Retrieval-augmented generation without agentic workflow
"""
import argparse
import json
import os
import time
from textwrap import dedent

import autogen
from finrobot.utils import get_current_date, register_keys_from_json
from finrobot.data_source import FinnHubUtils, YFinanceUtils


def fetch_data(ticker: str) -> str:
    """Fetch all data and concatenate into context string"""
    context_parts = []
    
    try:
        profile = FinnHubUtils.get_company_profile(ticker)
        context_parts.append(f"Company Profile:\n{profile}\n")
    except Exception as e:
        context_parts.append(f"Company profile unavailable: {e}\n")
    
    try:
        news = FinnHubUtils.get_company_news(ticker, start_date="2025-01-01", end_date=get_current_date())
        context_parts.append(f"Recent News:\n{news}\n")
    except Exception as e:
        context_parts.append(f"News unavailable: {e}\n")
    
    try:
        financials = FinnHubUtils.get_basic_financials(ticker)
        context_parts.append(f"Financial Metrics:\n{financials}\n")
    except Exception as e:
        context_parts.append(f"Financials unavailable: {e}\n")
    
    try:
        stock_data = YFinanceUtils.get_stock_data(ticker, start_date="2025-01-01", end_date=get_current_date())
        context_parts.append(f"Stock Price Data:\n{stock_data}\n")
    except Exception as e:
        context_parts.append(f"Stock data unavailable: {e}\n")
    
    return "\n".join(context_parts)


def run_rag(ticker: str, model: str, oai_config: str, keys_path: str, temperature: float) -> dict:
    """Run RAG baseline - fetch data, stuff into prompt, single LLM call"""
    
    if keys_path and os.path.isfile(keys_path):
        register_keys_from_json(keys_path)
    
    config_list = autogen.config_list_from_json(oai_config, filter_dict={"model": [model]})
    if not config_list:
        raise ValueError(f"Model {model} not found in {oai_config}")
    
    # Fetch context data
    print(f"  → Fetching data for {ticker}...")
    start_fetch = time.time()
    context = fetch_data(ticker)
    fetch_time = time.time() - start_fetch
    
    # Single LLM call with context
    prompt = dedent(f"""
        You are a financial analyst. Below is data about {ticker} as of {get_current_date()}.
        
        {context}
        
        Based on this data, provide:
        1. 2-4 key positive developments (be specific, cite the data above)
        2. 2-4 potential concerns or risks (be specific)
        3. A 1-week price movement prediction with percentage and clear reasoning
    """).strip()
    
    client = autogen.OpenAIWrapper(config_list=config_list)
    
    start_llm = time.time()
    response = client.create(
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    llm_time = time.time() - start_llm
    
    output = response.choices[0].message.content
    total_time = fetch_time + llm_time
    
    return {
        "system": "rag",
        "ticker": ticker,
        "model": model,
        "temperature": temperature,
        "analysis": output,  # Only the LLM analysis
        "latency_seconds": round(total_time, 2),
        "fetch_time": round(fetch_time, 2),
        "llm_time": round(llm_time, 2),
        "timestamp": get_current_date(),
    }


def main():
    parser = argparse.ArgumentParser(description="Run RAG Baseline")
    parser.add_argument("tickers", nargs="+", help="Stock tickers to analyze")
    parser.add_argument("--model", default="llama-3.3-70b", help="Model name")
    parser.add_argument("--oai-config", default="OAI_CONFIG_LIST", help="Config file")
    parser.add_argument("--keys", default="config_api_keys", help="API keys file")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    results = []
    for ticker in args.tickers:
        print(f"\n{'='*60}")
        print(f"Running RAG on {ticker} with {args.model}")
        print(f"{'='*60}")
        try:
            result = run_rag(ticker, args.model, args.oai_config, args.keys, args.temperature)
            results.append(result)
            print(f"✓ {ticker} completed in {result['latency_seconds']}s")
        except Exception as e:
            print(f"✗ {ticker} failed: {e}")
            results.append({"system": "rag", "ticker": ticker, "error": str(e)})
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {args.output}")


if __name__ == "__main__":
    main()


