from api import create_app
from dotenv import load_dotenv
from api.models import *
import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
