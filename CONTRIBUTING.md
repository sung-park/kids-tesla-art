# Contributing to Kids Tesla Art

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests (see below)
5. Submit a pull request

## Development Setup

See [README.md](README.md#local-development) for full setup instructions.

## Running Tests

**Backend:**
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

**Frontend:**
```bash
cd frontend
npm install
npm test
npx tsc --noEmit
```

## Code Style

- **Backend:** Follow PEP 8. No `Any` type hints.
- **Frontend:** TypeScript strict mode. No `any` types.
- All code and documentation must be in **English**.

## Adding a New Tesla Model

1. Add the official UV template PNG to `backend/app/templates/{model}.png`
   (source: [teslamotors/custom-wraps](https://github.com/teslamotors/custom-wraps))
2. Register the model in `backend/app/main.py` (`list_templates` endpoint)
3. Add the model to `SUPPORTED_MODELS` in `backend/app/routers/process.py`
4. Add the model option to `frontend/components/ModelSelector.tsx`
5. Generate a printable template: `python scripts/generate_templates.py --models {model}`

## Reporting Issues

Please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your OS, browser, and phone model (if relevant)
