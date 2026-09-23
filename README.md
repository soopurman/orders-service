# orders-service

A minimal FastAPI CRUD API. Run `docker compose up --build`, then visit `/` for its route index, `/docs` for Swagger UI, or `/items` for seeded data on port 8001. In a deployed preview it is mounted beneath `/b` (for example `/b/docs` and `/b/items`). Branches named `fg/<feature>` join the matching feature group in `catalog-service`; all other branches get an independent preview.

## Fast local check

This service runs the same on modern Fedora and macOS. Install Git and Docker Compose v2 first;
on macOS install/start Docker Desktop, and on Fedora install/enable Docker Engine plus the Compose
plugin. Python is not needed to start the container, but Python 3.10+ and `pip` are needed to run
the HTTP test suite locally.

```bash
docker compose up --build --detach
curl --fail http://localhost:8001/
curl --fail http://localhost:8001/items
pip install -r requirements-test.txt
API_BASE_URL=http://localhost:8001 pytest -q tests
docker compose down --volumes
```
