
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import akshare as ak
import pandas as pd


def main():
    print("开始获取各省生猪均价……")

    # 获取搜猪网各省实时均价
    df = ak.spot_hog_soozhu()

    if df is None or df.empty:
        raise RuntimeError("数据源没有返回价格数据")

    required = ["省份", "价格"]

    for column in required:
        if column not in df.columns:
            raise RuntimeError(
                f"数据字段缺失：{column}，实际字段：{list(df.columns)}"
            )

    # 清洗价格数据
    df = df[required].copy()
    df["省份"] = df["省份"].astype(str).str.strip()
    df["价格"] = pd.to_numeric(df["价格"], errors="coerce")

    df = df.dropna()
    df = df[
        (df["省份"] != "") &
        (df["价格"] > 0) &
        (df["价格"] < 100)
    ]

    df = df.drop_duplicates(subset=["省份"])

    if len(df) < 20:
        raise RuntimeError(
            f"有效省份只有 {len(df)} 个，数据可能不完整"
        )

    provinces = [
        {
            "province": row["省份"],
            "price": round(float(row["价格"]), 2)
        }
        for _, row in df.iterrows()
    ]

    # 计算全国省级平均价
    average = sum(
        item["price"] for item in provinces
    ) / len(provinces)

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    result = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "breed": "省级生猪均价（未区分品种）",
        "unit": "元/公斤",
        "average": round(average, 2),
        "count": len(provinces),
        "source": "搜猪网 / AKShare",
        "provinces": provinces
    }

    # 保存为 JSON
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"更新成功：{len(provinces)} 个省级地区")
    print(f"全国省级均价：{average:.2f} 元/公斤")
    print("注意：数据未区分外三元、内三元和土杂猪。")


if __name__ == "__main__":
    main()
