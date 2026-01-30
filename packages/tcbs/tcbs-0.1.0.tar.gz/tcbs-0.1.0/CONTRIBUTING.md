# Contributing to TCBS Python SDK

Thank you for your interest in contributing to the TCBS Python SDK!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/tcbs/tcbs-python-sdk.git
cd tcbs-python-sdk
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Testing

⚠️ **IMPORTANT**: Never commit real API keys or test with real trading accounts!

- Use mock data for unit tests
- Comment out actual trading operations
- Test read-only operations first

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public methods
- Keep functions focused and concise

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Security

- Never commit API keys, tokens, or credentials
- Report security vulnerabilities privately to cskh@tcbs.com.vn
- Do not open public issues for security concerns

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
