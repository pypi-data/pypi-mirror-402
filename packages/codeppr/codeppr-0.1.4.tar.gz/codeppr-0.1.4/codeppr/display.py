import shlex
import threading
import click
from codeppr.tools import input_from_tty, separate_staged_files
from codeppr.git_helper import get_staged_files_with_status
import time

def prompt_user(after_ai_review: bool = False):
    if after_ai_review:
        full_prompt = (
            "\r\nSelect action to perform?\n"
            "  [s] Commit anyway\n"
            "  [a/q] Abort\n"
            "Note: If made changes to the code, please abort and stage the changes again before committing.\n"
            "Choice: "
        )
    else:
        full_prompt = (
            "\r\nSelect action to perform?\n"
            "  [y] Proceed with AI Review\n"
            "  [t <file number>] toggle review state of a file (ready <-> skip)\n"
            "  [s] Commit anyway\n"
            "  [a/q] Abort\n"
            "Choice: "
        )
    short_prompt = "Choice: "
    first_prompt = True

    while True:
        prompt_text = full_prompt if first_prompt else short_prompt
        # Preserve original casing for paths (needed for toggling) while still
        # allowing case-insensitive commands.
        raw_choice = input_from_tty(prompt_text).strip()
        first_prompt = False

        if not raw_choice:
            print("Invalid choice. Use valid commands.")
            continue

        try:
            parts = shlex.split(raw_choice)
        except ValueError:
            print("Invalid choice. Use valid commands.")
            continue

        if not parts:
            print("Invalid choice. Use valid commands.")
            continue

        cmd = parts[0].lower()
        if cmd in ("y", "yes") and not after_ai_review:
            return 'y'
        if cmd == "t" and not after_ai_review and len(parts) >= 2:
            return ('t', parts[1])
        if cmd in ("s", "skip"):
            return 's'
        if cmd in ("a", "abort", "q", "quit"):
            return 'a'

        print("Invalid choice. Use valid commands.")

def echo_staged_files(valid_files=None, non_valid_files=None):
    if valid_files is None or non_valid_files is None:
        lines = get_staged_files_with_status()
        valid_files, non_valid_files = separate_staged_files(lines)

    click.secho("[file_number] [status] [path]", fg="green", bold=True)

    click.secho("\n=====Files ready to be reviewed=====", fg="cyan", bold=True)
    for i,file in enumerate(valid_files):
        if file['change_type']:
            click.echo(f"{i}\t{file['status']}\t{file['path']} ({file['change_type']})")
        else:
            click.echo(f"{i}\t{file['status']}\t{file['path']}")

    click.echo("")

    valid_len = len(valid_files)
    click.secho("=====Files skipped from review=====", fg="yellow", bold=True)
    for i,file in enumerate(non_valid_files):
        if file['change_type']:
            click.echo(f"{valid_len + i}\t{file['status']}\t{file['path']} ({file['change_type']})")
        else:
            click.echo(f"{valid_len + i}\t{file['status']}\t{file['path']}")

def print_review(review_results: list[dict]):
    # Group issues by severity across all files
    issues_by_severity = {'critical': [], 'high': [], 'low': []}
    
    for result in review_results:
        path = result.get('path', 'Unknown file')
        review = result.get('issues', {})
        
        for severity in ['critical', 'high', 'low']:
            issues = review.get(severity, [])
            for issue in issues:
                issue_with_path = issue.copy()
                issue_with_path['path'] = path
                issues_by_severity[severity].append(issue_with_path)
    
    # Check if there are any issues at all
    total_issues = sum(len(issues) for issues in issues_by_severity.values())
    if total_issues == 0:
        click.secho("\nNo issues found by AI review.", fg="green")
        return
    
    # Print issues grouped by severity
    severity_config = {
        'critical': {'title': 'Critical Issues', 'color': 'red'},
        'high': {'title': 'High Priority Issues', 'color': 'yellow'},
        'low': {'title': 'Low Priority Issues', 'color': 'blue'}
    }
    
    for severity in ['critical', 'high', 'low']:
        issues = issues_by_severity[severity]
        if not issues:
            continue
        
        config = severity_config[severity]
        click.secho(f"\n{config['title']}", fg=config['color'], bold=True)
        click.secho("=" * len(config['title']), fg=config['color'])
        
        for issue in issues:
            path = issue.get('path', 'Unknown file')
            line = issue.get('line')
            if not (isinstance(line, int) or (isinstance(line, str) and line.isdigit())):
                line = 'N/A'
            description = issue.get('description', 'No description provided.')
            suggestion = issue.get('suggestion')
            
            # Print path and line in smaller format using dim style
            if line != 'N/A':
                click.secho(f"[{path}:{line}]", fg=config['color'], dim=True)
            else:
                click.secho(f"[{path}]", fg=config['color'], dim=True)
            click.secho(f"{description}", fg=config['color'])
            if suggestion:
                label = click.style("Suggestion:", fg='green', bold=True)
                body = click.style(f" {suggestion}", fg=config['color'])
                click.echo(label + body)
            click.echo()  # Empty line between issues

def waiting_animation(stop_event: threading.Event):
    frames = ["[=     ]", "[ =    ]", "[  =   ]", "[   =  ]", "[    = ]", "[     =]", "[      ]"]
    idx = 0
    try:
        while not stop_event.is_set():
            print(f"\rRunning AI review... {frames[idx % len(frames)]}", end="", flush=True)
            idx += 1
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\rAI review interrupted by user.")
    else:
        # Final message after the stop signal to clear the spinner
        print("\rRunning AI review... done", end="\n", flush=True)