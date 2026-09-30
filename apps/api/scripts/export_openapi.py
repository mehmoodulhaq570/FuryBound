"""Write the OpenAPI schema to apps/api/openapi.json without starting a server.

The web app generates its TypeScript types from this file (`pnpm gen:api-types`).
"""

import json
from pathlib import Path

from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def main() -> None:
    schema = create_app().openapi()
    OUTPUT.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
