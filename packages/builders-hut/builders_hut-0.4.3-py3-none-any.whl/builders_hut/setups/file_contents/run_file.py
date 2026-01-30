"""run.py"""

from textwrap import dedent

RUN_FILE_CONTENT = dedent(
    """
import uvicorn
from app.core.config import settings


def main():
    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()
"""
)
