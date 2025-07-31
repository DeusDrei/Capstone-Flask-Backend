from api import create_app
from dotenv import load_dotenv
from api.models import *
import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(port=5000)
