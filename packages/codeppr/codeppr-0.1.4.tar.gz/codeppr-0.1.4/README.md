# Codeppr

An AI assisted code review agent that saves you from bad commits by running its analysis during the pre-commit stage.

## Features

- **AI Code Analysis**: Intelligent code review suggestions.
- **Pre-commit Safety**: Catch potential issues before they are committed.

## How to install
For a standard install, run:

```bash
pip install codeppr
```
## Usage

Once installed, you need to initialize the tool in your repository:

1. **Install Hook**: Run this command to set up this tool as a git hook.
   ```bash
   codeppr install
   ```

2. **Add Api Key**: Add api key for a provider (openai, anthropic or gemini).
   ```bash
   codeppr auth login <provider>
   ```

3. **Automatic Review**: The tool will now automatically run and review your changes whenever you try to commit code.
   ```bash
   git commit -m "your message"
   ```

> [!NOTE] 
> The default provider is OpenAI. Switch to Anthropic or Gemini with:
> `codeppr use <provider> <model_name>`

You can also manually check available commands with:

```bash
codeppr --help
```

## Installing locally (development)

To install the dependencies and set up the project locally for development, run:

Create and activate virtual environment
```
python -m venv .venv
```

Install dependencies
```bash
pip install .
# OR
uv sync
```