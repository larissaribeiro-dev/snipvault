import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="snipvault", description="Sobe o servidor da API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="recarrega ao salvar (dev)")
    args = parser.parse_args()

    uvicorn.run(
        "snipvault.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
