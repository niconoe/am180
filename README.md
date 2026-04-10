# am180

A personal generative art tool. Python backend renders the art (flow fields,
and more to come), Vue 3 + TypeScript frontend lets you tweak parameters
live and export high-resolution PNGs.

Project is in early development.

## Prerequisites

- Python 3.14
- Node 20 or higher
- [uv](https://github.com/astral-sh/uv) for Python dependency management

## Setup

Clone the repo, then install both halves:

```bash
# Backend
uv sync

# Frontend
cd frontend
npm install
cd ..
```

## Running it

am180 runs as two processes during development. Open two terminals.

**Terminal 1 - backend** (from the project root):

```bash
uv run uvicorn am180.api:app --host 127.0.0.1 --port 7421 --reload
```

**Terminal 2 - frontend** (from the project root):

```bash
cd frontend
npm run dev
```

Then open <http://localhost:7422/> in a browser.

The frontend's Vite dev server proxies `/api/*` to the backend on 7421,
so the browser only ever talks to port 7422.

## Tests

```bash
uv run pytest backend/tests
```

## License

MIT - see [LICENSE](LICENSE).
