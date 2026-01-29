import os
import dotenv

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
PORT = int(os.getenv("PORT", "8800"))