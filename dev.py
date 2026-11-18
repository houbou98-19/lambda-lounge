"""Run the app locally without Docker/SAM:  python dev.py"""
from dotenv import load_dotenv  # type: ignore

load_dotenv()

import uvicorn  # type: ignore  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
