
from app import app, db, Offer
from urllib.parse import quote

products = [
    ("Apple iPhone 16 128GB", 69900),
    ("Samsung Galaxy S25", 80999),
    ("OnePlus 13", 69999),
    ("Google Pixel 9", 74999),
    ("Nothing Phone 3a", 24999),
    ("Apple iPad 11th Gen", 34900),
    ("Samsung Galaxy Tab S10 FE", 36999),
    ("MacBook Air M4", 99900),
    ("HP Pavilion 15", 62990),
    ("Lenovo IdeaPad Slim 5", 68990),
    ("ASUS Vivobook 15", 52990),
    ("Dell Inspiron 14", 59990),
    ("Sony WH-1000XM5", 24990),
    ("Bose QuietComfort Headphones", 29900),
    ("Apple AirPods Pro 2", 22900),
    ("Samsung Galaxy Buds3 Pro", 17999),
    ("JBL Tune 770NC", 5999),
    ("boAt Airdopes 141", 1299),
    ("Apple Watch SE 2", 24900),
    ("Samsung Galaxy Watch7", 24999),
    ("Noise ColorFit Pro 5", 3999),
    ("Mi Smart Band 9", 3499),
    ("Canon EOS R50", 64999),
    ("GoPro HERO13 Black", 44990),
    ("Sony Alpha ZV-E10", 59990),
    ("LG 1.5 Ton Split AC", 44990),
    ("Voltas 1.5 Ton AC", 33990),
    ("Samsung 253L Refrigerator", 28990),
    ("LG 7kg Washing Machine", 32990),
    ("IFB 8kg Washing Machine", 36990),
    ("Dyson V8 Vacuum Cleaner", 24900),
    ("Philips Air Fryer 4.1L", 7999),
    ("Prestige Iris Mixer Grinder", 3499),
    ("Instant Pot Duo", 8999),
    ("TP-Link Archer AX55 Router", 6999),
    ("TP-Link Deco M4", 5999),
    ("Logitech MX Master 3S", 8995),
    ("Logitech K380 Keyboard", 2995),
    ("Samsung T7 1TB SSD", 8999),
    ("SanDisk Ultra 128GB USB", 899),
    ("WD My Passport 2TB", 5999),
    ("Anker 737 Power Bank", 9999),
    ("Ambrane 20000mAh Power Bank", 1799),
    ("Portronics 65W Charger", 1999),
    ("Kindle Paperwhite 16GB", 13999),
    ("Kindle 11th Gen", 10999),
    ("Xiaomi 4K Smart TV 43 inch", 24999),
    ("Samsung Crystal 4K TV 55 inch", 42990),
    ("LG 4K Smart TV 50 inch", 38990),
    ("Mi 360 Security Camera 2K", 2999),
]

with app.app_context():
    added = 0

    for name, base_price in products:
        for store, multiplier in [
            ("Amazon India", 0.985),
            ("Flipkart", 0.975),
        ]:
            url = (
                "https://www.amazon.in/s?k="
                if store == "Amazon India"
                else "https://www.flipkart.com/search?q="
            )

            product_url = url + quote(name)

            existing = Offer.query.filter_by(
                product_name=name,
                store_name=store
            ).first()

            if existing:
                continue

            offer = Offer(
                product_name=name,
                store_name=store,
                price=round(base_price * multiplier),
                currency="INR",
                product_url=product_url,
                image_url=None,
                added_by=None
            )

            db.session.add(offer)
            added += 1

    db.session.commit()

    print("--------------------------------")
    print("PRICESCOUT DATA IMPORT COMPLETE")
    print("Products:", len(products))
    print("New offers:", added)
    print("--------------------------------")
