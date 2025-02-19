import os

from dotenv import load_dotenv

test_directory_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(f"{test_directory_path}/../secrets/mycelium.env")
