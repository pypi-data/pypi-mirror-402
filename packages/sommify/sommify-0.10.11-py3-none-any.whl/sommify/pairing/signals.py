from typing import Callable, Optional

import numpy as np


class Signal:
    """
    Base class for a scoring signal.
    """

    def __init__(
        self,
        name: str,
        mode: str,  # "additive" or "multiplicative"
        weight: float,
        scorer: Callable[[list, list, dict], np.ndarray],
    ) -> None:
        """
        Args:
            name: Unique signal name
            mode: "additive" or "multiplicative"
            weight: Strength of the signal
            scorer: Function that takes (dish_objs, wine_objs, context) and returns Nd x Nw matrix
        """
        self.name = name
        assert mode in ("additive", "multiplicative")
        self.mode = mode
        self.weight = weight
        self.scorer = scorer

    def compute(
        self, dish_objs: list, wine_objs: list, context: Optional[dict] = None
    ) -> np.ndarray:
        """
        Compute the contribution matrix (Nd x Nw) for this signal.
        """
        return self.scorer(dish_objs, wine_objs, context or {})


class UtilityAggregator:
    """
    Aggregates base scores and signals into final utility matrix.
    """

    def __init__(self, signals: list[Signal]) -> None:
        self.signals = signals

    def compute_final_score(
        self,
        base_score: np.ndarray,
        dish_objs: list,
        wine_objs: list,
        context: Optional[dict] = None,
        return_contributions: bool = False,
    ) -> np.ndarray:
        final_score = base_score.copy()
        contributions = {}

        for signal in self.signals:
            contrib_matrix = signal.compute(dish_objs, wine_objs, context)
            if signal.mode == "additive":
                final_score += signal.weight * contrib_matrix
            elif signal.mode == "multiplicative":
                final_score *= 1 + signal.weight * contrib_matrix

            if return_contributions:
                contributions[signal.name] = contrib_matrix * signal.weight

        if return_contributions:
            return final_score, contributions
        else:
            return final_score
