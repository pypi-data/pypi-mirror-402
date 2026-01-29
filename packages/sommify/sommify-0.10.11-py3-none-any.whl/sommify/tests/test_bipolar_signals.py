import numpy as np
import pytest
from sommify.pairing.scorers import dessert_scorer
from sommify.pairing.signals import Signal, UtilityAggregator


class MockDish:
    def __init__(self, title, ingredients=None, phrases=None):
        self.title = title
        self.ingredients = ingredients or []
        self.phrases = phrases or []


class MockWine:
    def __init__(self, title, types=None):
        self.title = title
        self.types = types or []


def test_dessert_scorer_bipolar():
    # 1. Setup mock data
    # "chocolate" is a dessert ingredient in categories.py
    dessert_dish = MockDish("Chocolate Cake", ingredients=["chocolate", "sugar"])
    # "steak" is likely handled by protein list in categories.py
    savory_dish = MockDish("Beef Steak", ingredients=["beef", "garlic"])

    sweet_wine = MockWine("Sauternes", types=["Dessert"])
    dry_wine = MockWine("Cabernet Sauvignon", types=["Red"])

    dishes = [dessert_dish, savory_dish]
    wines = [sweet_wine, dry_wine]

    # 2. Run scorer
    matrix = dessert_scorer(dishes, wines, {})

    # Expected shape (2 dishes x 2 wines)
    assert matrix.shape == (2, 2)

    # Dessert Wine (index 0)
    # - Dessert Dish (index 0): +1.0
    # - Savory Dish (index 1): -1.0
    assert matrix[0, 0] == 1.0
    assert matrix[1, 0] == -1.0

    # Dry Wine (index 1)
    # - Both Dishes: 0.0
    assert matrix[0, 1] == 0.0
    assert matrix[1, 1] == 0.0


def test_utility_aggregator_bipolar():
    # Verify how UtilityAggregator handles the -1.0 values
    base_utility = np.array([[0.5, 0.5], [0.5, 0.5]])

    dessert_signal = Signal(
        name="dessert_push_pull", mode="additive", weight=0.2, scorer=dessert_scorer
    )

    agg = UtilityAggregator([dessert_signal])

    dessert_dish = MockDish("Chocolate Cake", ingredients=["chocolate", "sugar"])
    savory_dish = MockDish("Beef Steak", ingredients=["beef", "garlic"])
    sweet_wine = MockWine("Sauternes", types=["Dessert"])
    dry_wine = MockWine("Cabernet Sauvignon", types=["Red"])

    dishes = [dessert_dish, savory_dish]
    wines = [sweet_wine, dry_wine]

    final_scores = agg.compute_final_score(base_utility, dishes, wines)

    # Sweet wine + Dessert dish: 0.5 + (0.2 * 1.0) = 0.7
    assert final_scores[0, 0] == pytest.approx(0.7)

    # Sweet wine + Savory dish: 0.5 + (0.2 * -1.0) = 0.3
    assert final_scores[1, 0] == pytest.approx(0.3)

    # Dry wine + Any dish: 0.5 + (0.2 * 0.0) = 0.5
    assert final_scores[0, 1] == pytest.approx(0.5)
    assert final_scores[1, 1] == pytest.approx(0.5)


if __name__ == "__main__":
    pytest.main([__file__])
