import numpy as np

from .utils import get_val


def _normalize_val(val: any) -> str:
    if isinstance(val, list) and val:
        val = val[0]
    if hasattr(val, "name"):
        val = val.name
    if isinstance(val, str):
        return val.lower().strip()
    return val


# Multiplicative country boost
def geo_country_scorer(
    dish_objs: list, wine_objs: list, context: dict[str, any]
) -> np.ndarray:
    """
    Boosts wines that come from the same country as the dish's cuisine.
    Returns a matrix where 1.0 indicates a country match.
    """
    Nd, Nw = len(dish_objs), len(wine_objs)
    matrix = np.zeros((Nd, Nw))
    for i, dish in enumerate(dish_objs):
        d_cuisine = get_val(dish, "cuisine")
        d_countries = (
            [_normalize_val(c) for c in d_cuisine]
            if isinstance(d_cuisine, (list, tuple))
            else [_normalize_val(d_cuisine)]
        )

        for j, wine in enumerate(wine_objs):
            w_country = _normalize_val(get_val(wine, "country"))

            if w_country in d_countries:
                matrix[i, j] = 1.0
    return matrix


# Multiplicative region boost
def region_scorer(
    dish_objs: list, wine_objs: list, context: dict[str, any]
) -> np.ndarray:
    """
    Boosts wines from the same region as the dish.
    Returns 1.0 for a region match, and 0.5 for a country match if regions don't match.
    """
    Nd, Nw = len(dish_objs), len(wine_objs)
    matrix = np.zeros((Nd, Nw))
    for i, dish in enumerate(dish_objs):
        for j, wine in enumerate(wine_objs):
            d_region = _normalize_val(get_val(dish, "region"))
            w_region = _normalize_val(get_val(wine, "region"))
            d_country = _normalize_val(get_val(dish, "cuisine"))
            w_country = _normalize_val(get_val(wine, "country"))

            if d_region and w_region and d_region == w_region:
                matrix[i, j] = 1.0
            elif d_country and w_country and d_country == w_country:
                matrix[i, j] = 0.5
    return matrix


# Additive discount boost
def discount_scorer(
    dish_objs: list, wine_objs: list, context: dict[str, any]
) -> np.ndarray:
    """
    Applies a wine's discount as a score boost across all dishes.
    """
    Nd, Nw = len(dish_objs), len(wine_objs)
    matrix = np.zeros((Nd, Nw))
    for j, wine in enumerate(wine_objs):
        discount = get_val(wine, "discount", 0.0)
        # Broadcast discount to all dishes
        matrix[:, j] = discount
    return matrix
    return matrix


# Additive dessert boost
def dessert_scorer(
    dish_objs: list, wine_objs: list, context: dict[str, any]
) -> np.ndarray:
    """
    A push-pull scorer for dessert wines.
    - Boosts dessert wines when paired with dessert dishes (+1.0).
    - Penalizes dessert wines when paired with non-dessert dishes (-1.0).
    - Neutral (0.0) for non-dessert wines.
    """
    Nd, Nw = len(dish_objs), len(wine_objs)
    matrix = np.zeros((Nd, Nw))

    # Pre-calculate dish "is_dessert" status
    dish_is_dessert = []
    for dish in dish_objs:
        ingredients = get_val(dish, "ingredients", [])
        # Extract names if ingredients are objects
        ing_names = [i.name if hasattr(i, "name") else i for i in ingredients]
        phrases = get_val(dish, "phrases", [])
        title = get_val(dish, "title", "")

        from ..data.categories import is_dessert

        dish_is_dessert.append(is_dessert(title, ing_names, phrases))

    for j, wine in enumerate(wine_objs):
        types = get_val(wine, "types", [])
        is_dessert_wine = "dessert" in [t.lower() for t in types]

        if is_dessert_wine:
            for i, is_dessert_dish in enumerate(dish_is_dessert):
                if is_dessert_dish:
                    matrix[i, j] = 1.0
                else:
                    matrix[i, j] = -1.0

    return matrix
