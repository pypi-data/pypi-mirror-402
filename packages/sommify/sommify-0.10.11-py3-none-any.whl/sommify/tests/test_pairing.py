import numpy as np
from sommify.recipes import Recipe
from sommify.wines.wine import Wine
from sommify.pairing.signals import Signal, UtilityAggregator
from sommify.pairing.scorers import geo_country_scorer, region_scorer, discount_scorer


def test_pairing_logic_from_payload():
    # Setup data using from_payload
    payloads = [
        {
            "wineId": "WINE-1",
            "country": "france",
            "region": ["bordeaux"],
            "year": 2020,
            "price": 100.0,
            "discount": 0.2,
        },
        {
            "wineId": "WINE-2",
            "country": "italy",
            "region": ["tuscany"],
            "year": 2021,
            "price": 50.0,
            "discount": 0.1,
        },
    ]

    dishes = [
        Recipe(title="Beef Bourguignon", cuisine="france", region="burgundy"),
        Recipe(title="Pasta", cuisine="italy", region="tuscany"),
    ]

    wines = [Wine.from_payload(p) for p in payloads]
    # from_payload doesn't map discount yet, let's attach it just like in previous test
    for i, w in enumerate(wines):
        w.discount = payloads[i]["discount"]

    # Base similarity (fake embeddings)
    dish_emb = np.array([[1.0, 0.0], [0.0, 1.0]])
    wine_emb = np.array([[1.0, 0.0], [0.0, 1.0]])
    base_score = dish_emb @ wine_emb.T

    # Signals
    signals = [
        Signal("geo_country", "multiplicative", 0.05, geo_country_scorer),
        Signal("region", "multiplicative", 0.1, region_scorer),
        Signal("discount", "additive", 1.0, discount_scorer),
    ]

    aggregator = UtilityAggregator(signals)
    final_score, _ = aggregator.compute_final_score(
        base_score, dishes, wines, return_contributions=True
    )

    # Assertions (Bordeaux != Burgundy, but same country)
    # 1.0 * 1.05 (country) * 1.05 (region fallback) + 0.2 = 1.3025
    assert np.isclose(final_score[0, 0], 1.3025)
    # 1.0 * 1.05 (country) * 1.1 (region match) + 0.1 = 1.155 + 0.1 = 1.255
    assert np.isclose(final_score[1, 1], 1.255)


def test_lenient_pairing_with_dicts():
    # Raw dicts mimicking Qdrant records or custom objects
    dishes = [
        {"cuisine": "FR", "region": "Burgundy"},
        {"cuisine": "IT", "region": "Tuscany"},
    ]
    wines = [
        {"payload": {"country": "FR", "region": ["Bordeaux"], "discount": 0.2}},
        {"data": {"country": "IT", "region": "Tuscany", "discount": 0.1}},
    ]

    base_score = np.eye(2)
    signals = [
        Signal("geo_country", "multiplicative", 0.05, geo_country_scorer),
        Signal("region", "multiplicative", 0.1, region_scorer),
        Signal("discount", "additive", 1.0, discount_scorer),
    ]

    aggregator = UtilityAggregator(signals)
    final_score = aggregator.compute_final_score(base_score, dishes, wines)

    assert np.isclose(final_score[0, 0], 1.3025)
    assert np.isclose(final_score[1, 1], 1.255)


if __name__ == "__main__":
    test_pairing_logic_from_payload()
    test_lenient_pairing_with_dicts()
    print("All flexible pairing tests passed")
