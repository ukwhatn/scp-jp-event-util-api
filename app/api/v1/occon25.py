import dataclasses
import logging
from datetime import datetime
from typing import List

import wikidot
from fastapi import APIRouter
from pydantic import BaseModel, Field, HttpUrl


class ChartDataItem(BaseModel):
    """グラフの各バーに対応するデータ項目

    const chartData = [{
            label: "Safe",
            value: 300,
            color: "#90ee90",
            image1: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-165-q25y/sehukun1.png",
            image2: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-f6v1/sehukun2.png",
            fallbackText: "Safe1",
            fallbackText2: "Safe2"
        },
        {
            label: "Euclid",
            value: 20,
            color: "#ffff00",
            image1: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-g6cv/yukuriddokun1.png",
            image2: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-bvj7/yujuriddokun2.png",
            fallbackText: "Euclid1",
            fallbackText2: "Euclid2"
        },
        {
            label: "Keter",
            value: 30,
            color: "#ff0000",
            image1: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-m7bg/keterukun1.png",
            image2: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-rinw/keterukun2.png",
            fallbackText: "Keter1",
            fallbackText2: "Keter2"
        },
        {
            label: "その他",
            value: 25,
            color: "#ee82ee",
            image1: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-bdix/%E7%94%BB%E5%83%8F1.png",
            image2: "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-p1mw/%E7%94%BB%E5%83%8F2.png",
            fallbackText: "Other1",
            fallbackText2: "Other2"
        }
    ];
    """

    label: str = Field(str, description="バーのラベル (例: Safe, Euclid)")
    value: float = Field(float, description="バーの値")
    color: str = Field(str, description="バーの色 (CSSカラーコード, 例: #90ee90)")
    image1: HttpUrl = Field(HttpUrl, description="通常時の画像URL")
    image2: HttpUrl = Field(HttpUrl, description="最大値の時の画像URL")
    fallbackText: str = Field(
        str, description="画像読み込み失敗時の代替テキスト (通常時)"
    )
    fallbackText2: str = Field(
        str, description="画像読み込み失敗時の代替テキスト (最大値時)"
    )


class ChartDataResponse(BaseModel):
    """APIレスポンス全体のスキーマ"""

    data: List[ChartDataItem]


@dataclasses.dataclass
class ChartDataCache:
    created_at: datetime
    data: List[ChartDataItem]

    # キャッシュの有効期限 (10分)
    cache_duration: int = 60 * 10

    # キャッシュの有効期限を確認
    def is_cache_valid(self) -> bool:
        return (datetime.now() - self.created_at).total_seconds() < self.cache_duration


# キャッシュを保持する辞書
chart_data_cache: ChartDataCache | None = None

SAFE_TAGS = "+safe -explained -コンテスト"
EUCLID_TAGS = "+euclid -explained -コンテスト"
KETER_TAGS = "+keter -explained -コンテスト"
OTHER_TAGS = "thaumiel neutralized apollyon archon ticonderoga decommissioned pending esoteric-class explained"

router = APIRouter()


@router.get("/chart-data", response_model=ChartDataResponse)
def get_chart_data(
        debug: bool = False,
):
    global chart_data_cache

    if debug or (chart_data_cache is None or not chart_data_cache.is_cache_valid()):
        logging.info("Fetching new data from Wikidot")
        with wikidot.Client() as wd_client:
            site = wd_client.site.get("scp-jp")

            safe_articles = site.pages.search(
                tags=SAFE_TAGS + (" +occon" if not debug else ""),
                limit="30" if debug else None,
            )
            euclid_articles = site.pages.search(
                tags=EUCLID_TAGS + (" +occon" if not debug else ""),
                limit="30" if debug else None,
            )
            keter_articles = site.pages.search(
                tags=KETER_TAGS + (" +occon" if not debug else ""),
                limit="30" if debug else None,
            )
            other_articles = site.pages.search(
                tags=OTHER_TAGS + (" +occon" if not debug else ""),
                limit="30" if debug else None,
            )

            # 各記事のratingを合算
            safe_rating = sum(article.rating for article in safe_articles if article.rating >= 0)
            euclid_rating = sum(article.rating for article in euclid_articles if article.rating >= 0)
            keter_rating = sum(article.rating for article in keter_articles if article.rating >= 0)
            other_rating = sum(article.rating for article in other_articles if article.rating >= 0)

        # returnデータビルド
        items = [
            ChartDataItem(
                label="Safe",
                value=safe_rating,
                color="#90ee90",
                image1=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-165-q25y/sehukun3.png"
                ),
                image2=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-f6v1/sehukun2.png"
                ),
                fallbackText="Safe1",
                fallbackText2="Safe2",
            ),
            ChartDataItem(
                label="Euclid",
                value=euclid_rating,
                color="#ffff00",
                image1=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-g6cv/yukuriddokun1.png"
                ),
                image2=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-bvj7/yujuriddokun2.png"
                ),
                fallbackText="Euclid1",
                fallbackText2="Euclid2",
            ),
            ChartDataItem(
                label="Keter",
                value=keter_rating,
                color="#ff0000",
                image1=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-m7bg/keterukun1.png"
                ),
                image2=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-rinw/keterukun2.png"
                ),
                fallbackText="Keter1",
                fallbackText2="Keter2",
            ),
            ChartDataItem(
                label="その他",
                value=other_rating,
                color="#ee82ee",
                image1=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-bdix/%E7%94%BB%E5%83%8F1.png"
                ),
                image2=HttpUrl(
                    "https://scp-jp-storage.wdfiles.com/local--files/file%3A7737619-166-p1mw/%E7%94%BB%E5%83%8F2.png"
                ),
                fallbackText="Other1",
                fallbackText2="Other2",
            ),
        ]

        # キャッシュを更新
        chart_data_cache = ChartDataCache(created_at=datetime.now(), data=items)
    else:
        logging.info("Using cached data")

    return chart_data_cache
