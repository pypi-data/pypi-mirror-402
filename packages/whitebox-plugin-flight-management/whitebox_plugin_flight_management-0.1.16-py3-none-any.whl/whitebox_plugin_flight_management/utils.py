import os
import requests
import json

from django.conf import settings
from whitebox import get_plugin_logger


logger = get_plugin_logger(__name__)


# OpenAIP GCS bucket URL
BUCKET_URL = "https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f"

# Save directory for airport data
SAVE_DIR = os.path.join(settings.MANAGED_ASSETS_ROOT, "airport_data")


def get_country_code_from_env() -> str | None:
    country_code = os.getenv("COUNTRY_CODE", "").strip()
    if not country_code:
        logger.warning(f"Country code not found in environment variables.")
        return None

    return country_code.lower()


def download_airport_data() -> None:
    country_code = get_country_code_from_env()
    if not country_code:
        return

    filename = f"{country_code}_apt.json"
    url = f"{BUCKET_URL}/{filename}"

    os.makedirs(SAVE_DIR, exist_ok=True)
    save_path = os.path.join(SAVE_DIR, filename)

    if os.path.exists(save_path):
        logger.info(f"Airport data file already exists: {save_path}")
        return

    try:
        response = requests.get(url)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded airport data for {country_code} to {save_path}")
    except requests.RequestException as e:
        logger.exception(f"Failed to download airport data from {url}")
        return


def load_airport_data() -> dict | None:
    country_code = get_country_code_from_env()
    if not country_code:
        return

    filename = f"{country_code}_apt.json"
    file_path = os.path.join(SAVE_DIR, filename)

    if not os.path.exists(file_path):
        logger.warning(f"Airport data file not found: {file_path}")
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        logger.info(f"Loaded airport data from {file_path}")
        return data
    except Exception as e:
        logger.exception(f"Failed to load airport data from {file_path}")
        return


def query_for_airports(query: str) -> list:
    airports = load_airport_data()
    results = []

    if not airports:
        return results

    for airport in airports:
        name = airport.get("name", "").lower()
        icao = airport.get("icaoCode", "").lower()

        if query in name or query in icao:
            results.append(airport)

    return results
