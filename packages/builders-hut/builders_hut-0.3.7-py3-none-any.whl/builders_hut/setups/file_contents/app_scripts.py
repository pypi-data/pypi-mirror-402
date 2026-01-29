"""app/scripts/*"""

from textwrap import dedent

APP_SCRIPTS_DEV_CONTENT = dedent("""
import uvicorn


def main():
    uvicorn.run("app.main:app", reload=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
""")
