import json
import random
from sommify.wines.wine import Wine


def test_batch_loading():
    json_path = "sommify/tests/data/qdrant.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    points = data.get("result", {}).get("points", [])
    print(f"Total wines in file: {len(points)}")

    loaded_wines = []
    for point in points:
        payload = point.get("payload", {})
        wine = Wine.from_payload(payload)
        loaded_wines.append((payload, wine))

    # Pick 5 random wines to inspect
    sample_size = min(5, len(loaded_wines))
    samples = random.sample(loaded_wines, sample_size)

    print("\n=== Verifying Random Samples ===\n")
    for i, (payload, wine) in enumerate(samples):
        print(f"--- Sample {i + 1} ---")
        print(f"Qdrant id: {payload.get('wineId')}")
        print(f"Wine Title: {wine.title}")
        print(f"Country: {wine.country}")
        print(f"Region: {wine.region} (from payload: {payload.get('region')})")
        print(f"Grapes: {wine.grapes}")
        print(f"Vintage: {wine.vintage} (from payload: {payload.get('year')})")
        print(f"Price: {wine.price} {wine.currency}")
        print("-" * 30)


if __name__ == "__main__":
    test_batch_loading()
