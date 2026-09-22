# orders-service

A minimal FastAPI CRUD API. Run `docker compose up --build`, then visit `/` for its route index, `/docs` for Swagger UI, or `/items` for seeded data on port 8001. In a deployed preview it is mounted beneath `/b` (for example `/b/docs` and `/b/items`). Branches named `fg/<feature>` join the matching feature group in `catalog-service`; all other branches get an independent preview.
