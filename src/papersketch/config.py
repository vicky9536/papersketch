# src/papersketch/config.py

import os
from dotenv import load_dotenv

# Load variables from .env at project root
load_dotenv()

PAPERSKETCH_ENDPOINT = "https://api.scholar.club/api/v1/papersketch_url/"
PAPERSKETCH_API_KEY = os.getenv("PAPERSKETCH_API_KEY")
REQUEST_TIMEOUT = 180
