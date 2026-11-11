# PriceScout

A small Flask price-comparison app with accounts, password hashing, optional Google sign-in, product offer storage, and a JSON-LD product-page parser.

## Run locally (Windows PowerShell)

1. Install Python 3.11 or newer.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`. Change `SECRET_KEY` to a long random value.
6. Start the app:

   ```powershell
   python app.py
   ```

7. Visit http://127.0.0.1:5000

## Google sign-in setup

1. Open Google Cloud Console and create/select a project.
2. Configure the OAuth consent screen.
3. Create an OAuth client ID with application type **Web application**.
4. Add this authorized redirect URI for local development:
   `http://127.0.0.1:5000/auth/google/callback`
5. Put the client ID and secret in `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
6. Restart the app. For deployment, add your production callback URI too:
   `https://YOUR-DOMAIN/auth/google/callback`

Keep OAuth secrets private. Never commit `.env` to Git.

## Deploy to Render

1. Push this project to a GitHub repository.
2. In Render, choose **New > Blueprint** and connect the repository.
3. Render reads `render.yaml`, creates the web service and PostgreSQL database.
4. After deployment, open the service URL and test registration/login.
5. Add your production Google OAuth callback URL in Google Cloud Console and set the two Google environment variables in Render.

## How price collection works

The scraper looks for Schema.org `Product` and `Offer` JSON-LD in a product page. This is more reliable than guessing prices from arbitrary HTML, but many stores do not expose this data or block automated access. Use official APIs, affiliate feeds, or permitted pages for real deployments. Respect each site's terms, robots rules, rate limits, and applicable law.

## Database tables

- `user`: name, unique email, password hash (never plaintext), optional Google subject ID.
- `offer`: product name, store, price, currency, URL, image URL, and the user who submitted it.

## Before a public launch

Add CSRF protection, rate limiting, email verification/password reset, secure cookie settings, input/output validation, scraper SSRF protections and domain allowlisting, background jobs/caching, and proper migrations (Alembic/Flask-Migrate). This is a student MVP, not a security-audited commerce platform.
