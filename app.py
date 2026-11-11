from flask import abort
from sqlalchemy import func
from urllib.parse import quote_plus
import os
import json
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from scraper import extract_product
from comparator import build_comparison_groups

load_dotenv()
app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
database_url = os.getenv("DATABASE_URL", "sqlite:///pricescout.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
# requirements install psycopg v3, so select SQLAlchemy's psycopg v3 dialect.
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("VERCEL", "").lower() == "1"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return self.password_hash is not None and check_password_hash(self.password_hash, password)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(300), nullable=False, index=True)
    store_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(8), default="INR")
    product_url = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=True)
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def get_product_category(name):
    name = name.lower()

    categories = {
        "Mobiles": ["iphone", "samsung galaxy s", "oneplus", "pixel", "phone"],
        "Laptops": ["macbook", "pavilion", "ideapad", "vivobook", "inspiron"],
        "Audio": ["headphones", "airpods", "buds", "jbl", "earphones"],
        "Wearables": ["watch", "band", "colorfit"],
        "Cameras": ["canon", "gopro", "sony alpha"],
        "Home Appliances": ["ac", "refrigerator", "washing machine", "vacuum", "air fryer", "mixer", "instant pot"],
        "Accessories": ["mouse", "keyboard", "charger", "power bank"],
        "Storage": ["ssd", "usb", "passport"],
        "Televisions": ["tv", "television"],
        "Networking": ["router", "deco"],
        "Other": []
    }

    for category, keywords in categories.items():
        if any(keyword in name for keyword in keywords):
            return category

    return "Other"


CATEGORY_IMAGE_FILES = {
    "Mobiles": "mobiles.svg",
    "Laptops": "laptops.svg",
    "Audio": "audio.svg",
    "Wearables": "wearables.svg",
    "Cameras": "cameras.svg",
    "Home Appliances": "home-appliances.svg",
    "Accessories": "accessories.svg",
    "Storage": "storage.svg",
    "Televisions": "televisions.svg",
    "Networking": "networking.svg",
    "Other": "other.svg",
}

def get_category_image(category):
    return CATEGORY_IMAGE_FILES.get(category, "other.svg")


@app.route("/")
def index():
    from collections import OrderedDict

    query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "")
    selected_store = request.args.get("store", "")
    sort_by = request.args.get("sort", "relevance")

    offers_query = Offer.query

    if query:
        offers_query = offers_query.filter(
            Offer.product_name.ilike(f"%{query}%")
        )

    if selected_store:
        offers_query = offers_query.filter_by(
            store_name=selected_store
        )

    all_offers = offers_query.all()

    products = OrderedDict()

    for offer in all_offers:
        category = get_product_category(offer.product_name)

        if selected_category and category != selected_category:
            continue

        products.setdefault(offer.product_name, []).append(offer)

    comparisons = []

    for name, product_offers in products.items():
        cheapest = min(product_offers, key=lambda x: x.price)
        highest = max(product_offers, key=lambda x: x.price)

        comparisons.append({
            "name": name,
            "offers": product_offers,
            "cheapest": cheapest,
            "savings": round(highest.price - cheapest.price, 2),
            "category": get_product_category(name),
            "image": next(
                (o.image_url for o in product_offers if o.image_url),
                None
            ),
            "image_fallback": get_category_image(get_product_category(name))
        })

    if sort_by == "price_low":
        comparisons.sort(key=lambda p: p["cheapest"].price)
    elif sort_by == "price_high":
        comparisons.sort(key=lambda p: p["cheapest"].price, reverse=True)
    elif sort_by == "savings":
        comparisons.sort(key=lambda p: p["savings"], reverse=True)

    categories = sorted(set(
        get_product_category(p.product_name)
        for p in Offer.query.all()
    ))

    stores = sorted(set(
        p.store_name for p in Offer.query.all()
    ))

    store_searches = {
        "Amazon India": "https://www.amazon.in/s?k=" + quote_plus(query),
        "Flipkart": "https://www.flipkart.com/search?q=" + quote_plus(query)
    }

    return render_template(
        "index.html",
        comparisons=comparisons,
        query=query,
        categories=categories,
        stores=stores,
        selected_category=selected_category,
        selected_store=selected_store,
        sort_by=sort_by,
        store_searches=store_searches
    )


@app.route("/product/<int:offer_id>")
def product_detail(offer_id):
    offer = db.session.get(Offer, offer_id)

    if not offer:
        abort(404)

    related_offers = Offer.query.filter(
        func.lower(Offer.product_name) ==
        offer.product_name.lower()
    ).order_by(Offer.price.asc()).all()

    cheapest = min(related_offers, key=lambda x: x.price)

    return render_template(
        "product.html",
        offer=offer,
        offers=related_offers,
        cheapest=cheapest,
        category=get_product_category(offer.product_name)
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account is ready!", "success")
            return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/auth/google")
def google_login():
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        flash("Google login is not configured yet. Add the Google OAuth keys to your environment.", "error")
        return redirect(url_for("login"))
    return google.authorize_redirect(url_for("google_callback", _external=True))

@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        user_info = google.parse_id_token(token, nonce=None)
    email = user_info.get("email", "").lower()
    google_id = user_info.get("sub")
    if not email or not user_info.get("email_verified"):
        flash("Google did not provide a verified email address.", "error")
        return redirect(url_for("login"))
    user = User.query.filter_by(google_id=google_id).first() or User.query.filter_by(email=email).first()
    if not user:
        user = User(name=user_info.get("name", "Google user"), email=email, google_id=google_id)
        db.session.add(user)
    else:
        user.google_id = google_id
    db.session.commit()
    login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_offer():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            flash("Please enter a valid product URL.", "error")
            return redirect(url_for("add_offer"))
        try:
            data = extract_product(url)
            offer = Offer(
                product_name=data["name"],
                store_name=parsed.netloc.replace("www.", ""),
                price=data["price"],
                currency=data.get("currency", "INR"),
                product_url=url,
                image_url=data.get("image"),
                added_by=current_user.id,
            )
            db.session.add(offer)
            db.session.commit()
            flash(f"Added {offer.product_name} at {offer.currency} {offer.price:.2f}.", "success")
            return redirect(url_for("index", q=offer.product_name))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception:
            db.session.rollback()
            flash("Could not fetch this page. Try a publicly accessible product page with structured product data.", "error")
    return render_template("add_offer.html")

@app.route("/offer/<int:offer_id>/delete", methods=["POST"])
@login_required
def delete_offer(offer_id):
    offer = db.session.get(Offer, offer_id)
    if offer and offer.added_by == current_user.id:
        db.session.delete(offer)
        db.session.commit()
        flash("Your offer was deleted.", "success")
    return redirect(url_for("index"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
