import os

from dotenv import load_dotenv

load_dotenv()

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SRC_DIR), "data")
TEST_DATA_PATH = os.path.join(DATA_DIR, os.getenv("TEST_DATA_FILENAME", "test_task_data.csv"))

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# DUCKDB_PATH = os.getenv("DUCKDB_PATH", os.path.join(DATA_DIR, "feature_store.db"))
DUCKDB_PATH = os.getenv("DUCKDB_PATH", ":memory:")
DUCKDB_BATCH = int(os.getenv("DUCKDB_BATCH", 1000))
