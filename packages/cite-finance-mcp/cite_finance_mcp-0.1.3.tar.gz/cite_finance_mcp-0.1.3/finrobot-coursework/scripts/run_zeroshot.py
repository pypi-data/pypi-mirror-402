#!/usr/bin/env python3
"""
Zero-Shot Baseline - Raw LLM with no tools or data access
"""
import argparse
import json
import time
from textwrap import dedent

import autogen
from finrobot.utils import get_current_date


def run_zeroshot(ticker: str, model: str, oai_config: str, temperature: float) -> dict:
    """Run zero-shot baseline - just LLM knowledge, no external data"""
    
    config_list = autogen.config_list_from_json(oai_config, filter_dict={"model": [model]})
    if not config_list:
        raise ValueError(f"Model {model} not found in {oai_config}")
    
    prompt = dedent(f"""
        You are a financial analyst. Analyze {ticker} stock as of {get_current_date()}.
        
        Provide:
        1. 2-4 key positive developments for the company
        2. 2-4 potential concerns or risks
        3. A 1-week price movement prediction with percentage and reasoning
        
        Use your knowledge of the company and market trends.
    """).strip()
    
    client = autogen.OpenAIWrapper(config_list=config_list)
    
    start_time = time.time()
    response = client.create(
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    elapsed = time.time() - start_time
    
    output = response.choices[0].message.content
    
    return {
        "system": "zeroshot",
        "ticker": ticker,
        "model": model,
        "temperature": temperature,
        "analysis": output,  # Consistent field name
        "latency_seconds": round(elapsed, 2),
        "timestamp": get_current_date(),
    }


def main():
    parser = argparse.ArgumentParser(description="Run Zero-Shot Baseline")
    parser.add_argument("tickers", nargs="+", help="Stock tickers to analyze")
    parser.add_argument("--model", default="llama-3.3-70b", help="Model name")
    parser.add_argument("--oai-config", default="OAI_CONFIG_LIST", help="Config file")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    results = []
    for ticker in args.tickers:
        print(f"\n{'='*60}")
        print(f"Running ZERO-SHOT on {ticker} with {args.model}")
        print(f"{'='*60}")
        try:
            result = run_zeroshot(ticker, args.model, args.oai_config, args.temperature)
            results.append(result)
            print(f"✓ {ticker} completed in {result['latency_seconds']}s")
        except Exception as e:
            print(f"✗ {ticker} failed: {e}")
            results.append({"system": "zeroshot", "ticker": ticker, "error": str(e)})
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {args.output}")


if __name__ == "__main__":
    main()


