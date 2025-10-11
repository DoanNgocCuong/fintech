#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api.py
-----
Expose API lấy FULL báo cáo chứng khoán (dựa trên vnstock_full_report.py).

Chạy:
    # Cài deps
    pip install -r requirements.txt

    # Dev (auto-reload)
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

    # Prod tối giản
    python api.py --host 0.0.0.0 --port 8000

Prod (Linux):
    nohup python api.py --host 0.0.0.0 --port 8000 > server.log 2>&1 &

Endpoints:
    GET  /health
    GET  /report/{symbol}?start=YYYY-MM-DD&end=YYYY-MM-DD&source=VCI
"""

import argparse
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from vnstock_full_report import get_full_report

app = FastAPI(title="VNStock Full Report API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "today": date.today().isoformat()}


@app.get("/report/{symbol}")
def report(symbol: str, start: Optional[str] = Query(None), end: Optional[str] = Query(None), source: str = Query("VCI")):
    try:
        bundle = get_full_report(symbol=symbol, start=start, end=end, source=source)
        # Trả JSON: các DataFrame đã được convert trong get_full_report? ->
        # Ở đây để nhẹ server, chỉ trả gọn: meta + kích thước từng bảng, và khuyên dùng CLI để xuất Excel.
        sizes = {
            "overview": len(bundle.overview),
            "profile": len(bundle.profile),
            "large_shareholders": len(bundle.large_shareholders),
            "subsidiaries": len(bundle.subsidiaries),
            "balance_sheet": len(bundle.balance_sheet),
            "income_statement": len(bundle.income_statement),
            "cashflow": len(bundle.cashflow),
            "ratios": len(bundle.ratios),
            "dcf_valuation": len(bundle.dcf_valuation),
            "price_history": len(bundle.price_history),
            "volatility": len(bundle.volatility),
            "insider_deals": len(bundle.insider_deals),
            "news": len(bundle.news),
        }
        return {
            "symbol": bundle.symbol,
            "generated_at": bundle.generated_at,
            "sizes": sizes,
            "note": "Dùng CLI để xuất Excel/JSON đầy đủ: python vnstock_full_report.py -s {sym}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--host", type=str, default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
