import click
from codeppr.tools import is_interactive, check_installed, can_prompt
from codeppr.tools import install_pre_commit_hook, uninstall_pre_commit_hook, separate_staged_files
from codeppr.display import prompt_user, print_review, echo_staged_files, waiting_animation
from codeppr.git_helper import get_staged_files_with_status
from codeppr.reviewer import run_review
from codeppr.state import read_state, update_file_review, write_state, clear_state
from codeppr.auth.providers import PROVIDERS
from codeppr.auth.keys import set_api_key, get_api_key, delete_api_key
from codeppr.configure import read_config, write_config
import threading
import sys
import asyncio
from pathlib import Path
import tomllib
from importlib.metadata import PackageNotFoundError, version

def _get_version_from_pyproject() -> str:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "0.0.0")
    except Exception:
        return "0.0.0"

def _get_version() -> str:
    try:
        return version("codeppr")
    except PackageNotFoundError:
        return _get_version_from_pyproject()

_VERSION = _get_version()

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(_VERSION, "-v", "--version", message="codeppr version %(version)s")
def cli():
    """codeppr — AI-assisted code review before commit"""
    pass

@click.command()
def install():
    """Installs codeppr git pre-commit hook in the current repository to run AI review before commit"""
    try:
        install_pre_commit_hook()
        click.echo("✔ Git pre-commit hook installed")
    except RuntimeError as e:
        click.echo(f"❌ {e}")

@click.command()
def uninstall():
    """Uninstalls codeppr git pre-commit hook in the current repository"""
    try:
        uninstall_pre_commit_hook()
        click.echo("✔ Git pre-commit hook uninstalled")
    except RuntimeError as e:
        click.echo(f"❌ {e}")

async def _run_async():
    '''
    Run codeppr AI review before commit
    '''
    try:
        if not is_interactive():
            click.echo("Non-interactive environment detected. Skipping codeppr AI review.")
            sys.exit(0)
        
        if not check_installed():
            click.echo("codeppr is not installed. Please install it by running codeppr install.")
            sys.exit(1)
        
        if not can_prompt():
            click.echo("Cannot prompt user in this environment. Skipping codeppr AI review.")
            sys.exit(1)

        lines = get_staged_files_with_status()
        valid_files, non_valid_files = separate_staged_files(lines)
        # Flag to control whether to show staged files or AI review prompt
        show_staged_files = True
        config = read_config()

        while True:
            if show_staged_files:
                echo_staged_files(valid_files, non_valid_files)
                click.echo("\n---------------------------------------------------")
                click.secho(f"Using {config.get("model")} from {config.get("provider")} for the review.", fg="cyan")
                click.echo("---------------------------------------------------")

            ret =  prompt_user(after_ai_review=not show_staged_files)

            if type(ret) is tuple and ret[0] == 't':
                _, file_num = ret

                valid_len = len(valid_files)
                try:
                    file_index = int(file_num)
                    if file_index < 0 or file_index >= valid_len + len(non_valid_files):
                        click.echo("Invalid file number. Please try again.")
                        continue
                except ValueError:
                    click.echo("Invalid file number. Please try again.")
                    continue

                # Toggle review state of the file
                if file_index < valid_len:
                    # Move from valid to non-valid
                    file_to_move = valid_files.pop(file_index)
                    non_valid_files.append(file_to_move)
                else:
                    # Move from non-valid to valid
                    file_to_move = non_valid_files.pop(file_index - valid_len)
                    valid_files.append(file_to_move)
                continue

            else:

                if ret == 's':
                    click.echo("Proceeding with commit...")
                    sys.exit(0)
                if ret == 'a':
                    click.echo("Commit aborted.")
                    sys.exit(1)
                if ret == 'y':
                    stop_event = threading.Event()
                    thread = threading.Thread(target=waiting_animation, args=(stop_event,))
                    thread.start()
                    try:
                        review_results = await run_review(valid_files)
                    finally:
                        stop_event.set()
                        thread.join()
                    print_review(review_results)
                    # Update state based on review results
                    state = read_state()
                    for result in review_results:
                        path = result.get('path')
                        diff = result.get('diff')
                        if path and diff is not None:
                            update_file_review(state, path, diff)

                    write_state(state)

                    show_staged_files = False
                    continue

    except KeyboardInterrupt:
        print("\n⛔ Commit aborted by user (Ctrl+C)")
        sys.exit(1)

@click.command()
def run():
    '''
    Run codeppr AI review before commit
    '''
    asyncio.run(_run_async())

@click.group()
def cache():
    """Manage codeppr cache"""
    pass

@cache.command("clear")
def clear_cache():
    """Clear codeppr state cache"""
    clear_state()
    click.echo("✔ codeppr state cache cleared")

@click.group()
def auth():
    """Manage ai providers authentication"""
    pass

@auth.command()
@click.argument("provider")
def login(provider: str):
    """Login to AI provider"""
    provider = provider.lower()

    if provider not in PROVIDERS:
        click.echo(f"❌ Unknown provider: {provider}")
        click.echo(f"Available providers: {', '.join(PROVIDERS)}")
        raise click.Abort()
    
    display = PROVIDERS[provider]["display"]

    click.echo(f"🔐 Enter your {display} API key (input will be hidden):")
    api_key = click.prompt(
        "API key",
        hide_input=True,
    )

    try:
        set_api_key(provider, api_key)
    except Exception as e:
        click.echo(f"❌ Failed to store API key: {e}")
        raise click.Abort()

    click.echo(f"✅ {display} API key stored securely.")

@auth.command()
@click.argument("provider")
def logout(provider: str):
    """Remove stored API key for a provider."""
    provider = provider.lower()

    if provider not in PROVIDERS:
        click.echo(f"❌ Unknown provider: {provider}")
        raise click.Abort()

    try:
        delete_api_key(provider)
        click.echo(f"🗑️ Removed API key for {provider}.")
    except Exception:
        click.echo(f"ℹ️ No stored API key found for {provider}.")

@auth.command("status")
def auth_status():
    """Show authentication status for all providers."""
    click.echo("Authentication status:\n")

    for provider, meta in PROVIDERS.items():
        key = get_api_key(provider)
        status = "✔ configured" if key else "✖ not configured"
        click.echo(f"- {meta['display']}: {status}")

@click.command(
    short_help="Set AI provider and model to use for code reviews.\ncodeppr use <provider> <model>"
)
@click.argument("provider")
@click.argument("model")
def use(provider: str, model: str):
    """Set AI provider and model to use for code reviews."""
    provider = provider.lower()

    if provider not in PROVIDERS:
        click.echo(f"❌ Unknown provider: {provider}")
        click.echo(f"Available providers: {', '.join(PROVIDERS)}")
        raise click.Abort()
    
    config = read_config()
    config['provider'] = provider
    config['model'] = model
    write_config(config)

    click.echo(f"✅ Set provider to {provider} and model to {model}.")

@click.command()
def status():
    """Show current AI provider and model configuration."""
    config = read_config()
    provider = config.get('provider', 'not set')
    model = config.get('model', 'not set')

    click.echo("Current AI configuration:")
    click.echo(f"- Provider: {provider}")
    click.echo(f"- Model: {model}\n")

cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(run)
cli.add_command(cache)
cli.add_command(auth)
cli.add_command(use)
cli.add_command(status)