import pytest
from sommify.wines.wine import Wine
from sommify.pyregion import regions
from sommify.pygrape import grapes as all_grapes


def test_wine_initialization():
    wine = Wine(
        title="Test Wine",
        country="Italy",
        region="Tuscany",
        grapes=["Sangiovese"],
        vintage="2020",
        price=20.0,
        currency="EUR",
    )

    assert wine.title == "Test Wine"
    assert wine.country == "Italy"
    assert wine.vintage == "2020"
    assert wine.price == 20.0
    assert wine.currency == "EUR"

    # Check region recognition
    # Tuscany should be recognized as a region object
    assert wine.region.name == "Tuscany"
    assert wine.region == regions.get(name="Tuscany")

    # Check grape recognition
    # Sangiovese should be recognized as a grape object
    assert len(wine.grapes) == 1
    assert wine.grapes[0].name == "Sangiovese"
    assert wine.grapes[0] == all_grapes.get(name="Sangiovese")


def test_wine_unknown_region_grape():
    wine = Wine(
        title="Unknown Wine",
        country="Nowhere",
        region="Unknown Region",
        grapes=["Unknown Grape"],
    )

    assert wine.region == "Unknown Region"
    assert len(wine.grapes) == 1
    assert wine.grapes[0] == "Unknown Grape"


if __name__ == "__main__":
    # Manually run tests if pytest is not available or for quick check
    try:
        test_wine_initialization()
        print("test_wine_initialization passed")
        test_wine_unknown_region_grape()
        print("test_wine_unknown_region_grape passed")
    except AssertionError as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
