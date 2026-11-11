import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

HEADERS = {
    "User-Agent": "PriceScoutStudentProject/1.0 (contact: project-owner@example.com)"
}

def _price(value):
    if isinstance(value, dict):
        value = value.get("price")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.]", "", value.replace(",", ""))
        return float(cleaned) if cleaned else None
    return None

def _walk_jsonld(node):
    if isinstance(node, list):
        for item in node:
            yield from _walk_jsonld(item)
    elif isinstance(node, dict):
        yield node
        graph = node.get("@graph")
        if graph:
            yield from _walk_jsonld(graph)

def extract_product(url):
    """Read Product/Offer JSON-LD from a page. Only use on pages you are allowed to access."""
    host = urlparse(url).hostname or ""
    if not host:
        raise ValueError("Invalid product URL.")
    response = requests.get(url, headers=HEADERS, timeout=12)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in _walk_jsonld(payload):
            kind = item.get("@type", [])
            if isinstance(kind, str):
                kind = [kind]
            if "Product" not in kind:
                continue
            name = item.get("name")
            offers = item.get("offers", {})
            offer = offers[0] if isinstance(offers, list) and offers else offers
            price = _price(offer)
            currency = offer.get("priceCurrency", "INR") if isinstance(offer, dict) else "INR"
            image = item.get("image")
            if isinstance(image, list):
                image = image[0] if image else None
            if isinstance(image, dict):
                image = image.get("url") or image.get("contentUrl")
            if isinstance(image, str) and image.strip():
                image = urljoin(response.url, image.strip())
                if urlparse(image).scheme not in ("http", "https"):
                    image = None
            else:
                image = None
            if name and price is not None:
                return {"name": str(name)[:300], "price": price, "currency": currency, "image": image}

    raise ValueError("No Product price data found. This store may not expose supported structured data.")
