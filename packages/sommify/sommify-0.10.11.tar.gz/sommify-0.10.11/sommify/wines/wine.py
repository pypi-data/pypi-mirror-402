from typing import Optional

from .. import utils
from ..pygrape import grapes as all_grapes
from ..pyregion import regions


class Wine:
    def __init__(
        self,
        title: str,
        country: str,
        region: str | list[str],
        grapes: list[str],
        vintage: Optional[str] = None,
        tags: Optional[list[str]] = None,
        types: Optional[list[str]] = None,
        producer: Optional[str] = None,
        packaging: Optional[str] = None,
        closure: Optional[str] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        sugars: Optional[float] = None,
        acids: Optional[float] = None,
        alcohol: Optional[float] = None,
        volume: Optional[float] = None,
    ) -> None:
        self.title = title
        # use pycountry to normalize cuisine to iso2
        self.country = utils.normalize_country(country)

        # Handle region as string or list
        region_str = region[0] if isinstance(region, list) and region else region
        if not isinstance(region_str, str):
            region_str = ""

        # Region recognition
        # Try to find the region object, otherwise keep the string
        if region_str and region_str.strip():
            found_region = regions.search_fuzzy(region_str)
            self.region = found_region if found_region else None
        else:
            self.region = None

        # Grapes recognition
        self.grapes = []
        for grape_name in grapes:
            if not grape_name or not grape_name.strip():
                continue
            # Try to find the grape object
            found_grape, _ = all_grapes.search(grape_name, fuzzy=True)
            if found_grape:
                self.grapes.append(found_grape)
            else:
                self.grapes.append(grape_name)

        self.vintage = str(vintage) if vintage is not None else None
        self.tags = tags if tags is not None else []
        self.types = types if types is not None else []
        self.producer = producer
        self.packaging = packaging
        self.closure = closure
        self.price = price
        self.currency = currency
        self.sugars = sugars
        self.acids = acids
        self.alcohol = alcohol
        self.volume = volume

    @classmethod
    def from_payload(cls, payload: dict) -> "Wine":
        """
        Factory method to create a Wine object from a Qdrant-style payload.
        """
        # Mapping common Qdrant keys to Wine attributes
        return cls(
            title=payload.get("title", "Unknown"),
            # country=payload.get("country", ""),
            country=utils.normalize_country(payload.get("country", "")),
            region=payload.get("subregion") or payload.get("region"),
            grapes=payload.get("grapes", []),
            vintage=payload.get("year"),
            tags=payload.get("tags"),
            types=list(
                filter(
                    None,
                    [
                        payload.get("typeL1"),
                        payload.get("typeL2"),
                        payload.get("typeL3"),
                    ],
                )
            ),
            producer=payload.get("producer"),
            packaging=payload.get("packaging"),
            closure=payload.get("closure"),
            price=payload.get("price"),
            currency=payload.get("currency"),
            alcohol=payload.get("alcohol"),
            volume=payload.get("volume"),
        )

    def __repr__(self) -> str:
        return f"<Wine: {self.title} ({self.vintage})>"
