# Glama.ai / Smithery.ai Submission

**Title:**
Cite-Finance: Hallucination-Free Financial Data

**Short Description (140 chars):**
Get verified, citation-backed financial metrics (SEC 10-K/Q) for AI agents. Stop hallucinating revenue numbers.

**Long Description / README:**
Building a financial agent? Tired of LLMs hallucinating revenue numbers or making up P/E ratios?

**Cite-Finance** is the first MCP server designed for **Compliance-Grade Provenance**.
Instead of just giving you a number, we give you the **Citation**: a direct link to the exact row in the SEC filing where that number came from.

### Features
*   ✅ **Zero Hallucination:** Structured JSON from XBRL tags.
*   ✅ **Verified Citations:** Every metric includes a source URL (e.g., "10-K, Page 42").
*   ✅ **Consistency Scores:** Confidence metrics for every data point.
*   ✅ **Demo Mode:** Try it instantly with AAPL or TSLA (no key required).

### Tools
*   `get_financial_metrics`: Get Revenue, Net Income, EBITDA, etc.
*   `get_market_sentiment`: AI-analyzed news sentiment (Coming Soon).

### Installation
```bash
uvx cite-finance-mcp
```

### Configuration
Works out-of-the-box in Demo Mode.
For full market access, get a key at [cite-finance.io](https://cite-finance.io) and set:
`CITE_FINANCE_API_KEY`

**Tags:**
Finance, Data, SEC, Stocks, Investing, Research, Provenance

**Repository URL:**
https://github.com/[YOUR_USERNAME]/cite-finance-api
