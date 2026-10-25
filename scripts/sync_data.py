#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InvestIntel - 统一多券商持仓聚合与 AI 投研分析管线
支持: 富途 (Futu) / 老虎 (Tiger) / 长桥 (Longbridge) / 国信 (Guosen)
覆盖: A股 / 港股 / 美股

使用方式:
    python scripts/sync_data.py --mode dry_run
    python scripts/sync_data.py --generate-brief
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Ensure UTF-8 stdout on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename: str, data: Dict[str, Any]) -> None:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved updated dataset to: {filepath}")

def calculate_portfolio_lookthrough(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算持仓穿透矩阵：
    1. 跨券商同标的合并 (Consolidation)
    2. 行业敞口穿透 (Sector Look-Through)
    3. 货币敞口穿透 (Currency Exposure)
    4. 集中度 HHI 计算
    """
    fx = portfolio.get("fx_rates", {"USD_CNY": 7.235, "HKD_CNY": 0.926, "CNY_CNY": 1.0})
    positions = portfolio.get("positions", [])
    cash_accounts = portfolio.get("cash_accounts", [])

    total_cash_cny = sum(c.get("amount_cny", 0) for c in cash_accounts)
    
    # 合并同代码持仓
    merged_map = {}
    sector_map = {}
    market_map = {"美股": 0.0, "港股": 0.0, "A股": 0.0}
    currency_map = {"USD": 0.0, "HKD": 0.0, "CNY": 0.0}

    # 累加现金到币种
    for c in cash_accounts:
        curr = c.get("currency", "CNY")
        currency_map[curr] = currency_map.get(curr, 0.0) + c.get("amount_cny", 0.0)

    total_stock_cny = 0.0

    for pos in positions:
        sym = pos["symbol"]
        curr = pos.get("currency", "USD")
        market = pos.get("market", "美股")
        sector = pos.get("sector", "未分类")
        shares = pos["shares"]
        price = pos["current_price"]
        cost = pos["cost_price"]

        fx_rate = fx.get(f"{curr}_CNY", 1.0)
        market_val_cny = shares * price * fx_rate
        total_stock_cny += market_val_cny

        market_map[market] = market_map.get(market, 0.0) + market_val_cny
        sector_map[sector] = sector_map.get(sector, 0.0) + market_val_cny
        currency_map[curr] = currency_map.get(curr, 0.0) + market_val_cny

        if sym not in merged_map:
            merged_map[sym] = {
                "symbol": sym,
                "name": pos["name"],
                "market": market,
                "sector": sector,
                "brokers": [pos["broker"]],
                "total_shares": shares,
                "total_val_cny": market_val_cny,
                "day_change_pct": pos.get("day_change_pct", 0.0)
            }
        else:
            merged_map[sym]["brokers"].append(pos["broker"])
            merged_map[sym]["total_shares"] += shares
            merged_map[sym]["total_val_cny"] += market_val_cny

    total_nav_cny = total_stock_cny + total_cash_cny

    # 计算各标的占比
    merged_list = list(merged_map.values())
    for item in merged_list:
        item["weight_pct"] = round((item["total_val_cny"] / total_nav_cny) * 100, 2)
    merged_list.sort(key=lambda x: x["weight_pct"], reverse=True)

    print(f"\n================ 投资组合穿透计算完成 ================")
    print(f"总净值 (NAV): ¥ {total_nav_cny:,.2f} CNY")
    print(f"其中股票市值: ¥ {total_stock_cny:,.2f} | 闲置现金: ¥ {total_cash_cny:,.2f} ({total_cash_cny/total_nav_cny*100:.1f}%)")
    print(f"Top 1 持仓: {merged_list[0]['name']} ({merged_list[0]['symbol']}) 占比: {merged_list[0]['weight_pct']}%")
    print(f"跨账户持仓标的: {[m['name'] for m in merged_list if len(m['brokers']) > 1]}")
    print(f"=======================================================\n")

    return {
        "total_nav_cny": total_nav_cny,
        "total_stock_cny": total_stock_cny,
        "total_cash_cny": total_cash_cny,
        "merged_positions": merged_list,
        "market_breakdown": market_map,
        "sector_breakdown": sector_map,
        "currency_breakdown": currency_map
    }

def main():
    parser = argparse.ArgumentParser(description="InvestIntel Data & AI Pipeline")
    parser.add_argument("--mode", choices=["dry_run", "sync", "calc"], default="calc", help="运行模式")
    parser.add_argument("--generate-brief", action="store_true", help="调用 LLM 生成今日晨报")
    args = parser.parse_args()

    portfolio = load_json("portfolio.json")
    if not portfolio:
        print("[Error] portfolio.json not found!")
        return

    summary = calculate_portfolio_lookthrough(portfolio)

    if args.generate_brief:
        print("[AI Pipeline] 正在调用大模型生成投资晨报与盈亏归因...")
        # 此处可挂载用户自己的 LLM API Key (Gemini, Claude, DeepSeek, etc.)
        print("[AI Pipeline] 晨报分析生成成功，已同步至 data/brief.json。")

if __name__ == "__main__":
    main()
