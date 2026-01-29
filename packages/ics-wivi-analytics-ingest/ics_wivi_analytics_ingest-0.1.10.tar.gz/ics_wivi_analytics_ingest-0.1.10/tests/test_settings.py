import os

from dotenv import load_dotenv

# Load .env file variables
load_dotenv()

GRAPHQL_SERVER = os.getenv("GRAPHQL_SERVER", "[server]")
GRAPHQL_ENDPOINT = f"https://graph.{GRAPHQL_SERVER}.wlnv.srv:8080/graphql"
