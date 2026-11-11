import re
import unicodedata
from collections import defaultdict


def normalize_product_name(name: str) -> str:
    """Conservative normalization: remove punctuation and collapse whitespace."""
    value = unicodedata.normalize("NFKC", name or "").casefold()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def build_comparison_groups(offers):
    """Group offers with the same normalized product name and sort cheapest first."""
    groups = defaultdict(list)
    for offer in offers:
        groups[normalize_product_name(offer.product_name)].append(offer)

    comparisons = []
    for key, group_offers in groups.items():
        sorted_offers = sorted(group_offers, key=lambda item: item.price)
        comparisons.append({
            "key": key,
            "product_name": sorted_offers[0].product_name,
            "offers": sorted_offers,
            "lowest_price": sorted_offers[0].price,
            "savings": (sorted_offers[-1].price - sorted_offers[0].price) if len(sorted_offers) > 1 else 0,
        })
    return sorted(comparisons, key=lambda group: group["lowest_price"])
