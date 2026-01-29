from sommify.wines.wine import Wine
import json


def test_qdrant_loading():
    # Data provided by the user
    qdrant_record = {
        "id": "053f91ad-d6ce-4883-b0c6-c4fc486829b5",
        "payload": {
            "wineId": "PSOMM-87225411060429504092310328214142986088",
            "wineIdNoVintage": "PSOMM-230176838609123475630940787300286137476",
            "producer": "pierre brevin",
            "currency": "EUR",
            "sku": 15507,
            "ouid": None,
            "packaging": "bottle",
            "closure": "natural cork",
            "stockLevel": None,
            "companyId": 65,
            "grapesLen": 2,
            "year": 2025,
            "isPromotion": False,
            "volume": 0.75,
            "price": 12.14,
            "pricePerLitre": 16.19,
            "promotionPrice": 12.14,
            "alcohol": 10.5,
            "tags": [
                "hartwall wine",
                "stock_g",
                "traditional",
                "france",
                "loire valley",
                "unknown",
                "rose",
                "light",
                "nan",
                "medium acidic",
                "medium dry",
                "old world",
                "europe",
                "western europe",
                "west europe",
                "mediterranean",
            ],
            "grapes": ["cabernet franc", "cabernet sauvignon"],
            "types": ["rose"],
            "region": ["loire valley"],
            "country": "france",
            "alcoholString": "10.5",
            "volumeString": "0.75",
            "isVegan": False,
            "isOrganic": False,
            "qtyIncrements": "1",
            "bottlesPerCase": "6",
            "foodTags": [],
        },
    }

    print("--- Loading Wine from Qdrant Payload ---")
    wine = Wine.from_payload(qdrant_record["payload"])

    # Display the object
    print(f"Object: {wine}")
    print(f"Title: {wine.title}")
    print(f"Country: {wine.country}")
    print(
        f"Region: {wine.region} (Extracted from {qdrant_record['payload']['region']})"
    )
    print(f"Grapes: {wine.grapes}")
    print(f"Vintage: {wine.vintage}")
    print(f"Price: {wine.price} {wine.currency}")
    print(f"Alcohol: {wine.alcohol}%")
    print(f"Volume: {wine.volume}L")
    print(f"Tags Count: {len(wine.tags)}")
    print(f"Types: {wine.types}")
    print("--- Loading Successful ---")


if __name__ == "__main__":
    test_qdrant_loading()
