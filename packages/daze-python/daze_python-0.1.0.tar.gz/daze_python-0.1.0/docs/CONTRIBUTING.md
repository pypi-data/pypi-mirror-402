# Contributing to daze-python

We appreciate your interest in contributing to daze-python! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - macOS/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
5. Install development dependencies: `pip install -e ".[dev]"`

## Development Workflow

1. Create a new branch for your feature: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest test/ -v`
4. Commit your changes: `git commit -m "Add your message"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Create a Pull Request

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Add docstrings to functions and classes
- Keep functions focused and simple

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a PR
- Aim for high test coverage

## Reporting Issues

- Use GitHub Issues to report bugs
- Provide a clear description and reproduction steps
- Include Python version and OS information

Thank you for contributing!
