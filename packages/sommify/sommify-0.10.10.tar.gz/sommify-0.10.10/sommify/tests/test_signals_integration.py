import json
import random

import numpy as np

from sommify.pairing.scorers import geo_country_scorer
from sommify.pairing.signals import Signal, UtilityAggregator
from sommify.pairing.utils import (
    generate_recommendation_matrix,
    generate_utility_matrix,
)
from sommify.recipes import Recipe
from sommify.wines import Wine


def _build_constraint_matrix(wines: list[Wine]) -> np.ndarray:
    """
    Build constraint matrix mapping wines to type categories.
    Returns: Array of shape (num_wines, 5) for [red, white, rose, sparkling, other]
    """
    CONSTRAINT_GROUPS = ["red", "white", "rose", "sparkling", "other"]
    num_wines = len(wines)
    constraint_matrix = np.zeros((num_wines, len(CONSTRAINT_GROUPS)), dtype=int)

    for i, wine in enumerate(wines):
        # Accessing .types directly on the Wine object
        types = [t.lower() for t in (wine.types or [])]

        if "sparkling" in types:
            constraint_matrix[i, 3] = 1
        elif "red" in types:
            constraint_matrix[i, 0] = 1
        elif "white" in types:
            constraint_matrix[i, 1] = 1
        elif "rose" in types:
            constraint_matrix[i, 2] = 1
        else:
            constraint_matrix[i, 4] = 1

    return constraint_matrix


def run_integration_test():
    print("--- Loading Data ---")

    # 1. Load Wines
    with open("sommify/tests/data/qdrant.json") as f:
        qdrant_data = json.load(f)

    # The file has a "result.points" structure
    points = qdrant_data.get("result", {}).get("points", qdrant_data)
    if not isinstance(points, list):
        points = []

    # We'll take a subset to keep it fast if needed, but let's try all
    wines = []
    wine_vectors = []
    for item in points:
        payload = item.get("payload", {})
        vector = item.get("vector")
        if vector:
            wines.append(Wine.from_payload(payload))
            wine_vectors.append(vector)

    wine_vectors = np.array(wine_vectors)
    print(f"Loaded {len(wines)} wines with vector shape {wine_vectors.shape}")

    # 2. Load Recipes
    with open("sommify/tests/data/recipes.json") as f:
        recipes_data = json.load(f)

    recipes = []
    recipe_vectors = []

    # Pick 10 random recipes
    random_recipes = random.sample(recipes_data, min(10, len(recipes_data)))

    for item in random_recipes:
        recipe = Recipe(
            phrases=item.get("phrases"),
            title=item.get("title"),
            cuisine=item.get("cuisine"),
            region=item.get("region"),
        )
        # Use the vector from JSON if available, otherwise it would calculate it (which might be slow)
        if "vector" in item:
            recipe.vector = np.array(item["vector"])

        recipes.append(recipe)
        recipe_vectors.append(recipe.vector)

    recipe_vectors = np.array(recipe_vectors)
    print(f"Loaded {len(recipes)} recipes with vector shape {recipe_vectors.shape}")

    print("\n--- Generating Base Utility Matrix ---")
    noise_scale = 0.01
    base_utility = generate_utility_matrix(
        dish_emb=recipe_vectors, wine_emb=wine_vectors, noise_scale=noise_scale
    )
    print(f"Base utility matrix shape: {base_utility.shape}")

    print("\n--- Applying Signals ---")
    # Add geo_country_scorer
    country_signal = Signal(
        name="country_match",
        mode="multiplicative",
        scorer=geo_country_scorer,
        weight=0.05,  # 5% boost if match
    )

    agg = UtilityAggregator([country_signal])

    context = {}  # Empty context for now
    final_utility = agg.compute_final_score(base_utility, recipes, wines, context)
    print(f"Final utility matrix shape: {final_utility.shape}")

    print("\n--- Building Constraints ---")
    constraint_matrix = _build_constraint_matrix(wines)
    print(f"Constraint matrix shape: {constraint_matrix.shape}")

    print("\n--- Generating Recommendations ---")
    recommendation_matrix = generate_recommendation_matrix(
        utility_matrix=final_utility,
        constraint_matrix=constraint_matrix,
        top_k_pct=0.1,  # Top 10%
        min_k=1,
    )
    print(f"Recommendation matrix shape: {recommendation_matrix.shape}")

    # Basic Check
    num_recs = np.sum(recommendation_matrix)
    print(f"Total recommendations generated: {num_recs}")

    if num_recs > 0:
        print("\nTest PASSED: Pipeline completed and generated recommendations.")

        # Look at recommendations for all dishes
        print("\n--- Recommendations ---")
        for i, recipe in enumerate(recipes):
            rec_idxs = np.where(recommendation_matrix[i] == 1)[0]
            print(
                f"\nRecommendations for recipe '{recipe.title}' (Cuisine: {recipe.cuisine}):"
            )
            if len(rec_idxs) == 0:
                print(" - No recommendations found.")
            for ridx in rec_idxs[:5]:  # Show first 5
                print(f" - {wines[ridx].title} ({wines[ridx].country})")
    else:
        print("\nTest FAILED: No recommendations generated.")


if __name__ == "__main__":
    run_integration_test()
