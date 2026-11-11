# Deploy PriceScout to Vercel + Neon

This project is prepared for Vercel's Flask/Python runtime. The Flask entry point remains `app.py` and the WSGI application is named `app`. Static assets are served from `public/static/` at `/static/`.

## Before deployment

1. Create a PostgreSQL project in Neon.
2. In Neon, open **Connect**, select your branch/database/role, and copy the **pooled** connection string (hostname includes `-pooler`). Keep `sslmode=require` in the URL.
3. Push this project to a private or public GitHub repository. Do not commit `.env`, database files, or secrets.
4. Import the repository into Vercel and deploy.

## Vercel environment variables

Set these in **Project → Settings → Environment Variables** for Production (and Preview if needed):

- `SECRET_KEY`: a long random secret, not the development fallback.
- `DATABASE_URL`: Neon pooled PostgreSQL URL.
- `GOOGLE_CLIENT_ID`: existing Google OAuth client ID.
- `GOOGLE_CLIENT_SECRET`: existing Google OAuth client secret.
- `VERCEL`: `1` (enables secure session cookies).

Redeploy after adding or changing environment variables.

## Google OAuth update

After Vercel gives you a domain, add these to your Google OAuth Web client:

- Authorized JavaScript origin: `https://YOUR-VERCEL-DOMAIN`
- Authorized redirect URI: `https://YOUR-VERCEL-DOMAIN/auth/google/callback`

Keep your local development URLs too. Replace the example domain with your actual Vercel domain.

## Important: your local SQLite data

Vercel's serverless filesystem is not a persistent database. Do not deploy with SQLite as the production database. Set `DATABASE_URL` to Neon PostgreSQL before the first production launch. The app creates missing tables on startup, but `create_all()` does not copy your local users/offers. Your local `pricescout.db` remains untouched; we will migrate its records to Neon as a separate step before you switch over.

## Product images

When a retailer page exposes Product JSON-LD, the scraper saves its image URL and the catalogue displays it. If a page has no usable image, PriceScout displays a locally hosted category illustration. Demo offers do not have real retailer images, so they use category illustrations instead.

## Security checklist

- Never commit `.env`, OAuth secrets, or database URLs.
- Change the development `SECRET_KEY` to a strong random value in Vercel.
- Review the privacy, terms, and contact pages before public launch.
- Demo prices are illustrative and must not be presented as live retailer prices.
