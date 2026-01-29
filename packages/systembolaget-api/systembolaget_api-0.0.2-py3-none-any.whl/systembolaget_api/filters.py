from dataclasses import dataclass


@dataclass(frozen=True)
class FilterOptions:
    # Base parameters
    page: int = 1
    size: int = 30
    sort_by: str | None = None
    sort_direction: str | None = None

    # Store filtering
    store_id: str | None = None
    is_in_store_assortment_search: bool | None = None

    # Price filtering
    price_min: int | None = None
    price_max: int | None = None

    # Alcohol percentage filtering
    alcohol_percentage_min: int | None = None
    alcohol_percentage_max: int | None = None

    # Volume filtering
    volume_min: int | None = None
    volume_max: int | None = None

    # Sugar content filtering
    sugar_content_min: float | None = None
    sugar_content_max: float | None = None

    # Taste clock filtering (0-12 scale)
    taste_clock_body_min: int | None = None
    taste_clock_body_max: int | None = None
    taste_clock_bitter_min: int | None = None
    taste_clock_bitter_max: int | None = None
    taste_clock_sweetness_min: int | None = None
    taste_clock_sweetness_max: int | None = None
    taste_clock_smokiness_min: int | None = None
    taste_clock_smokiness_max: int | None = None

    # Product launch date filtering
    product_launch_min: str | None = None  # Format: "YYYY-MM-DD"
    product_launch_max: str | None = None

    # Category filtering
    category_level1: str | None = None
    category_level2: str | None = None
    category_level3: list[str] | None = None

    # Packaging filtering
    packaging_level1: str | None = None
    packaging_level2: str | None = None

    # Multi-value parameters
    vintage: list[int] | None = None
    grapes: list[str] | None = None
    taste_symbols: list[str] | None = None
    assortment_text: list[str] | None = None
    country: list[str] | None = None
    seal: str | None = None
