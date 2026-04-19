from __future__ import annotations

import json
from pathlib import Path

import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import tushare as ts

ROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")
PRO = ts.pro_api("ccff9ae1a9762f99a414f46a08bc74a30fb6687abba90c67847b2177")

sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "STHeiti", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


def save_csv_png(df: pd.DataFrame, topic: str, anchor: str, plotter) -> None:
    csv_path = ROOT / topic / "charts" / "csv" / f"{anchor}.csv"
    png_path = ROOT / topic / "charts" / "png" / f"{anchor}.png"
    df.to_csv(csv_path, index=False)
    fig = plotter(df)
    fig.tight_layout()
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def chart_reinflation_oil_expectation() -> None:
    oil = ak.futures_foreign_hist(symbol="OIL")[["date", "close"]].rename(columns={"date": "trade_date", "close": "brent_close"})
    oil["trade_date"] = pd.to_datetime(oil["trade_date"])
    oil = oil[oil["trade_date"] >= pd.Timestamp("2024-01-01")]

    cpi = ak.macro_usa_cpi_monthly()[["日期", "今值"]].rename(columns={"日期": "trade_date", "今值": "cpi_mom"})
    cpi["trade_date"] = pd.to_datetime(cpi["trade_date"])
    cpi = cpi[cpi["trade_date"] >= pd.Timestamp("2024-01-01")]

    y10 = PRO.us_tycr(start_date="20240101")[["date", "y10"]].rename(columns={"date": "trade_date"})
    y10["trade_date"] = pd.to_datetime(y10["trade_date"])
    y10 = y10[y10["trade_date"] >= pd.Timestamp("2024-01-01")]

    monthly_oil = oil.set_index("trade_date").resample("MS").last().reset_index()
    merged = monthly_oil.merge(cpi, on="trade_date", how="left").merge(y10, on="trade_date", how="left")

    def plotter(df: pd.DataFrame):
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(df["trade_date"], df["brent_close"], color="#b45309", label="Brent/OIL close")
        ax1.set_ylabel("Oil close")
        ax2 = ax1.twinx()
        ax2.plot(df["trade_date"], df["y10"], color="#1d4ed8", label="US 10Y")
        ax2.plot(df["trade_date"], df["cpi_mom"], color="#dc2626", linestyle="--", label="US CPI mom")
        ax2.set_ylabel("Yield / CPI mom")
        ax1.set_title("Oil price, US CPI and 10Y yield")
        return fig

    save_csv_png(merged, "reinflation", "oil_price_inflation_expectation", plotter)


def chart_reinflation_fed_signal() -> None:
    cpi = ak.macro_usa_cpi_monthly()[["日期", "今值"]].rename(columns={"日期": "trade_date", "今值": "cpi_mom"})
    core = ak.macro_usa_core_cpi_monthly()[["日期", "今值"]].rename(columns={"日期": "trade_date", "今值": "core_cpi_mom"})
    spx = PRO.index_global(ts_code="SPX")[["trade_date", "close"]].rename(columns={"close": "spx_close"})
    y10 = PRO.us_tycr(start_date="20240101")[["date", "y10"]].rename(columns={"date": "trade_date"})
    for frame in (cpi, core):
        frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    for frame in (spx, y10):
        frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    cpi = cpi[cpi["trade_date"] >= pd.Timestamp("2024-01-01")]
    core = core[core["trade_date"] >= pd.Timestamp("2024-01-01")]
    spx = spx[spx["trade_date"] >= pd.Timestamp("2024-01-01")].sort_values("trade_date")
    y10 = y10[y10["trade_date"] >= pd.Timestamp("2024-01-01")]
    monthly_spx = spx.set_index("trade_date").resample("MS").last().reset_index()
    monthly_y10 = y10.set_index("trade_date").resample("MS").last().reset_index()
    merged = cpi.merge(core, on="trade_date", how="outer").merge(monthly_spx, on="trade_date", how="outer").merge(monthly_y10, on="trade_date", how="outer").sort_values("trade_date")

    def plotter(df: pd.DataFrame):
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        axes[0].plot(df["trade_date"], df["cpi_mom"], label="CPI mom", color="#dc2626")
        axes[0].plot(df["trade_date"], df["core_cpi_mom"], label="Core CPI mom", color="#7c3aed")
        axes[0].legend()
        axes[0].set_title("US CPI momentum")
        axes[1].plot(df["trade_date"], df["y10"], label="US 10Y", color="#1d4ed8")
        axes[1].plot(df["trade_date"], df["spx_close"], label="SPX", color="#059669")
        axes[1].legend()
        axes[1].set_title("US 10Y and SPX")
        return fig

    save_csv_png(merged, "reinflation", "fed_stagflation_signal", plotter)


def chart_reinflation_asset_map() -> None:
    spx = PRO.index_global(ts_code="SPX")[["trade_date", "pct_chg"]].rename(columns={"pct_chg": "spx_pct"})
    oil = ak.futures_foreign_hist(symbol="OIL")[["date", "close"]].rename(columns={"date": "trade_date", "close": "oil_close"})
    gold = ak.futures_foreign_hist(symbol="GC")[["date", "close"]].rename(columns={"date": "trade_date", "close": "gold_close"})
    y10 = PRO.us_tycr(start_date="20240101")[["date", "y10"]].rename(columns={"date": "trade_date"})

    for frame in (spx, oil, gold, y10):
        frame["trade_date"] = pd.to_datetime(frame["trade_date"])
        frame.sort_values("trade_date", inplace=True)

    oil = oil[oil["trade_date"] >= pd.Timestamp("2025-01-01")]
    gold = gold[gold["trade_date"] >= pd.Timestamp("2025-01-01")]
    y10 = y10[y10["trade_date"] >= pd.Timestamp("2025-01-01")]
    spx = spx[spx["trade_date"] >= pd.Timestamp("2025-01-01")]

    summary = pd.DataFrame(
        [
            {"asset": "SPX", "value": float(spx["spx_pct"].tail(20).mean())},
            {"asset": "Oil", "value": float(oil["oil_close"].pct_change().tail(20).mean() * 100)},
            {"asset": "Gold", "value": float(gold["gold_close"].pct_change().tail(20).mean() * 100)},
            {"asset": "US10Y", "value": float(y10["y10"].diff().tail(20).mean())},
        ]
    )

    def plotter(df: pd.DataFrame):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x="asset", y="value", palette="viridis", ax=ax)
        ax.set_title("Recent repricing snapshot")
        ax.set_ylabel("20-day average change")
        return fig

    save_csv_png(summary, "reinflation", "asset_repricing_map", plotter)


def chart_takaichi_aging_labor_gap() -> None:
    data = pd.DataFrame(
        [
            {"year": 2015, "total_population_mn": 127.1, "aged_share": 26.6, "foreign_workers_mn": 0.91},
            {"year": 2018, "total_population_mn": 126.5, "aged_share": 28.1, "foreign_workers_mn": 1.46},
            {"year": 2021, "total_population_mn": 125.5, "aged_share": 28.9, "foreign_workers_mn": 1.73},
            {"year": 2024, "total_population_mn": 123.8, "aged_share": 29.3, "foreign_workers_mn": 2.30},
        ]
    )

    def plotter(df: pd.DataFrame):
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(df["year"], df["total_population_mn"], marker="o", color="#1d4ed8", label="Population")
        ax1.set_ylabel("Population (mn)")
        ax2 = ax1.twinx()
        ax2.plot(df["year"], df["aged_share"], marker="s", color="#dc2626", label="65+ share")
        ax2.bar(df["year"], df["foreign_workers_mn"], alpha=0.25, color="#059669", label="Foreign workers")
        ax2.set_ylabel("Aged share / Foreign workers")
        ax1.set_title("Japan aging and labor gap")
        return fig

    save_csv_png(data, "takaichi", "aging_labor_gap", plotter)


def chart_takaichi_coalition() -> None:
    data = pd.DataFrame(
        [
            {"bloc": "LDP", "seats": 316},
            {"bloc": "Ishin", "seats": 35},
            {"bloc": "Komeito", "seats": 0},
            {"bloc": "Opposition others", "seats": 114},
        ]
    )

    def plotter(df: pd.DataFrame):
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.barplot(data=df, y="bloc", x="seats", palette="rocket", ax=ax)
        ax.set_title("Japan coalition right-shift snapshot")
        return fig

    save_csv_png(data, "takaichi", "coalition_right_shift", plotter)


def chart_takaichi_security() -> None:
    data = pd.DataFrame(
        [
            {"milestone": "Defense docs revised", "score": 1},
            {"milestone": "2% GDP target", "score": 2},
            {"milestone": "US alliance tightening", "score": 3},
            {"milestone": "Taiwan contingency rhetoric", "score": 4},
        ]
    )

    def plotter(df: pd.DataFrame):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["milestone"], df["score"], marker="o", color="#7c3aed")
        ax.set_title("Security posture escalation timeline")
        ax.set_ylabel("Escalation score")
        ax.tick_params(axis="x", rotation=20)
        return fig

    save_csv_png(data, "takaichi", "security_taiwan_impact", plotter)


def main() -> None:
    chart_reinflation_oil_expectation()
    chart_reinflation_fed_signal()
    chart_reinflation_asset_map()
    chart_takaichi_aging_labor_gap()
    chart_takaichi_coalition()
    chart_takaichi_security()
    manifest = {
        "generated": [
            "reinflation/oil_price_inflation_expectation",
            "reinflation/fed_stagflation_signal",
            "reinflation/asset_repricing_map",
            "takaichi/aging_labor_gap",
            "takaichi/coalition_right_shift",
            "takaichi/security_taiwan_impact",
        ]
    }
    (ROOT / "shared" / "config" / "chart_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(ROOT / "shared" / "config" / "chart_manifest.json")


if __name__ == "__main__":
    main()
