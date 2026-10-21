# AGENTS.md

## Project Overview

**avgrabber** is a Python utility tool for extracting AV (Audio/Video) information and metadata.


## Agent Structure

No agents configured. This project requires manual execution of Python scripts for AV info gathering.


## Python Coding style
- Use tab characters for indentation
- Line spacing: 2 lines before functions, 3 lines before class definitions.
- Write internal packages and third-party packages separately.
- function and variable names lowercase / constant, enum names all uppercase / class Camel-Case
- Do not omit parentheses in if and while statements
- Comments:
  * Write in Korean so it is easy to understand
  * In class and function docstrings, instead of a single line like """function description""", place "function description" on a separate new line
  * All function docstring comments must follow Google style and include type hints for parameters and return values
- Do not arbitrarily delete existing comments


## Development Guidelines

- All Python source are located in the `src/` directory
- Configuration files are stored in `conf/`
- Logs are generated to `logs/` directory
- Except for the main() function, write in an OOP style as much as possible.
- For key strings used in JSON, define them as constants in a "ClassNameKey" class using the "Final[str]" type
- For commonly used literal values, define them in a "ClassNameDef" class using the "Final[<Type>]" type
- Configuration-related classes must be written as DataClasses
- DataClasses for configuration must be assignable from JSON files and data
- If execution parameters are considered, configuration values defined in DataClass must take priority


## Testing

Run tests using:
```bash
python tests/test_xxx.py
```

## Known Issues

- None currently
- Ensure dependencies are installed: `pip install -r requirements.txt`
