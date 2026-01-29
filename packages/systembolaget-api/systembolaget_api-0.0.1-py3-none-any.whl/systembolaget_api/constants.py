from typing import Literal

BASE_URL = "https://www.systembolaget.se"
API_BASE_URL = "https://api-extern.systembolaget.se"


MAPPER = {
    "query": "textQuery",
    "page": "page",
    "size": "size",
    "sort_by": "sortBy",
    "sort_direction": "sortDirection",
    "store_id": "storeId",
    "is_in_store_assortment_search": "isInStoreAssortmentSearch",
    "price_min": "price.min",
    "price_max": "price.max",
    "alcohol_percentage_min": "alcoholPercentage.min",
    "alcohol_percentage_max": "alcoholPercentage.max",
    "volume_min": "volume.min",
    "volume_max": "volume.max",
    "sugar_content_min": "sugarContentGramPer100ml.min",
    "sugar_content_max": "sugarContentGramPer100ml.max",
    "taste_clock_body_min": "tasteClockBody.min",
    "taste_clock_body_max": "tasteClockBody.max",
    "taste_clock_bitter_min": "tasteClockBitter.min",
    "taste_clock_bitter_max": "tasteClockBitter.max",
    "taste_clock_sweetness_min": "tasteClockSweetness.min",
    "taste_clock_sweetness_max": "tasteClockSweetness.max",
    "taste_clock_smokiness_min": "tasteClockSmokiness.min",
    "taste_clock_smokiness_max": "tasteClockSmokiness.max",
    "product_launch_min": "productLaunch.min",
    "product_launch_max": "productLaunch.max",
    "category_level1": "categoryLevel1",
    "category_level2": "categoryLevel2",
    "category_level3": "categoryLevel3",
    "packaging_level1": "packagingLevel1",
    "packaging_level2": "packagingLevel2",
    "vintage": "vintage",
    "grapes": "grapes",
    "taste_symbols": "tasteSymbols",
    "assortment_text": "assortmentText",
    "country": "country",
    "seal": "seal",
}

SortBy = Literal[
    "Score",
    "Price",
    "Name",
    "Volume",
    "ProductLaunchDate",
    "Vintage",
]
SortDirection = Literal[
    "Ascending",
    "Descending",
]
