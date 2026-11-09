import json
from datetime import datetime
from zoneinfo import ZoneInfo

import akshare as ak
import pandas as pd


def main():
    print("开始获取外三元省级猪价……")

    # 获取外三元各省价格
    df = ak.futures_pig_rank(symbol="外三元")

    if df is None or df.empty:
        raise RuntimeError("数据源没有返回价格数据")

    required = ["省份", "价格-公斤"]
    for column in required:
        if column not in df.columns:
            raise RuntimeError(f"数据字段缺失：{column}")

    # 清洗数据
    df = df[required].copy()
    df["省份"] = df["省份"].astype(str).str.strip()
    df["价格-公斤"] = pd.to_numeric(
        df["价格-公斤"], errors="coerce"
    )

    df = df.dropna()
    df = df[
        (df["省份"] != "") &
        (df["价格-公斤"] > 0) &
        (df["价格-公斤"] < 100)
    ]

    df = df.drop_duplicates(subset=["省份"], keep="first")

    if len(df) < 20:
        raise RuntimeError(
            f"有效省份只有 {len(df)} 个，数据可能不完整，停止更新"
        )

    provinces = [
        {
            "province": row["省份"],
            "price": round(float(row["价格-公斤"]), 2)
        }
        for _, row in df.iterrows()
    ]

    average = sum(p["price"] for p in provinces) / len(provinces)

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    result = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "breed": "外三元",
        "unit": "元/公斤",
        "average": round(average, 2),
        "count": len(provinces),
        "source": "AKShare / 养猪数据中心",
        "provinces": provinces
    }

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"更新成功：{len(provinces)} 个省级地区")
    print(f"全国平均价格：{average:.2f} 元/公斤")


if __name__ == "__main__":
    main()
