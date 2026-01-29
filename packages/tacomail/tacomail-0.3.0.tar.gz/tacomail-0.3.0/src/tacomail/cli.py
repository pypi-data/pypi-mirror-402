#!/usr/bin/env python3
"""Tacomail CLI - Command-line interface for Tacomail disposable email service."""

from typing import Optional, Any, Callable
from enum import Enum
import re
import json
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from tacomail import (
    TacomailClient,
    AsyncTacomailClient,
    Email,
)


class OutputFormat(str, Enum):
    """Output format options for CLI commands."""
    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"


app = typer.Typer(
    name="tacomail",
    help="Tacomail CLI - Disposable email service command-line interface",
    no_args_is_help=True,
)

console = Console()

# Global options
use_async = False
output_format: OutputFormat = OutputFormat.RICH


def output_data(data: dict[str, Any] | list[Any], rich_callback: Callable[[], None]) -> None:
    """Output data in the configured format.

    Args:
        data: The data to output (dict for single items, list for multiple items)
        rich_callback: A callback function to render rich output (only called for RICH format)
    """
    if output_format == OutputFormat.JSON:
        print(json.dumps(data, default=str))
    elif output_format == OutputFormat.PLAIN:
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # For list of dicts, output tab-separated values
                    print("\t".join(str(v) for v in item.values()))
                else:
                    print(item)
        else:
            for key, value in data.items():
                print(f"{key}={value}")
    else:
        rich_callback()


def get_client():
    """Get the appropriate client based on global async setting."""
    if use_async:
        return AsyncTacomailClient()
    return TacomailClient()


# Email commands
@app.command()
def create(
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Specific domain to use (otherwise random)"
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Specific username to use (otherwise random)"
    ),
) -> None:
    """Create a random email address.

    Generates a random email address using available domains.
    You can optionally specify a domain or username.
    """
    client = get_client()

    try:
        if username and domain:
            email_address = f"{username}@{domain}"
        elif domain:
            username = client.get_random_username()
            email_address = f"{username}@{domain}"
        else:
            email_address = client.get_random_address()

        def rich_output():
            console.print(Panel(
                f"[bold green]Generated Email:[/bold green]\n{email_address}",
                title="✨ Success",
                border_style="green"
            ))

        output_data({"email": email_address}, rich_output)
    except Exception as e:
        console.print(f"[red]Error creating email:[/red] {e}")
        raise typer.Exit(1)


@app.command("list-domains")
def list_domains() -> None:
    """List all available domains for email addresses.

    Shows all domains that can be used to create email addresses.
    """
    client = get_client()

    try:
        domains = client.get_domains()

        def rich_output():
            console.print(f"\n[bold]Available Domains:[/bold] ({len(domains)})")
            for domain in domains:
                console.print(f"  • {domain}")

        output_data(domains, rich_output)
    except Exception as e:
        console.print(f"[red]Error fetching domains:[/red] {e}")
        raise typer.Exit(1)


# Session commands
@app.command("create-with-session")
def create_with_session(
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Specific domain to use (otherwise random)"
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Specific username to use (otherwise random)"
    ),
) -> None:
    _create_with_session_impl(domain, username)


@app.command("new")
def new_email_with_session(
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Specific domain to use (otherwise random)"
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Specific username to use (otherwise random)"
    ),
) -> None:
    """Create a random email address and session in one command (alias for 'create-with-session').

    This is a short alias for the 'create-with-session' command.
    Use 'tacomail new' instead of 'tacomail create-with-session' for convenience.

    Example:
        tacomail new

    With options:
        tacomail new --domain tacomail.de
        tacomail new -u myuser -d tacomail.de
    """
    _create_with_session_impl(domain, username)


def _create_with_session_impl(
    domain: Optional[str],
    username: Optional[str],
) -> None:
    """Create a random email address and session in one command.

    This command combines the functionality of 'create' and 'create-session' into a single,
    convenient operation. It generates a random email address and automatically creates a session
    for it, eliminating the need to run two separate commands when you want to start receiving
    emails immediately.

    The command returns both the email address and session information, including the expiration
    time. This is the most efficient way to set up a temporary email inbox.

    Example:
        tacomail create-with-session

    With options:
        tacomail create-with-session --domain tacomail.de
        tacomail create-with-session --username myuser --domain tacomail.de

    This command works in both sync and async modes (use --async flag for async mode).
    """
    client = get_client()

    def display_results(email_address: str, session, expires_str: str) -> None:
        """Display the results using the configured output format."""
        data = {
            "email": email_address,
            "username": session.username,
            "domain": session.domain,
            "expires": expires_str,
        }

        def rich_output():
            console.print(Panel(
                f"[bold green]Email Address:[/bold green]\n{email_address}\n\n"
                f"[bold green]Session Created[/bold green]\n\n"
                f"[bold]Expires:[/bold] {expires_str}\n"
                f"[bold]Username:[/bold] {session.username}\n"
                f"[bold]Domain:[/bold] {session.domain}\n\n"
                f"[dim]You can now receive emails at this address![/dim]",
                title="✨ Email & Session Ready",
                border_style="green"
            ))

            console.print("\n[bold cyan]Next steps:[/bold cyan]")
            console.print("  • Monitor inbox: [green]tacomail list {}[/green]".format(email_address))
            console.print("  • Wait for email: [green]tacomail wait {}[/green]".format(email_address))

        output_data(data, rich_output)

    try:
        # Handle async mode
        if use_async:
            import asyncio

            async def async_operation():
                # Generate email address
                nonlocal username
                if username and domain:
                    email_address = f"{username}@{domain}"
                elif domain:
                    username = await client.get_random_username()
                    email_address = f"{username}@{domain}"
                else:
                    email_address = await client.get_random_address()

                # Parse email for session creation
                if "@" not in email_address:
                    console.print(f"[red]Invalid email address generated:[/red] {email_address}")
                    raise typer.Exit(1)

                user, dom = email_address.split("@", 1)

                # Create session
                session = await client.create_session(user, dom)

                # Format expiration time (timestamp is in milliseconds)
                expires_dt = datetime.fromtimestamp(session.expires / 1000)
                expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

                display_results(email_address, session, expires_str)

            asyncio.run(async_operation())
        else:
            # Generate email address
            if username and domain:
                email_address = f"{username}@{domain}"
            elif domain:
                username = client.get_random_username()
                email_address = f"{username}@{domain}"
            else:
                email_address = client.get_random_address()

            # Parse email for session creation
            if "@" not in email_address:
                console.print(f"[red]Invalid email address generated:[/red] {email_address}")
                raise typer.Exit(1)

            user, dom = email_address.split("@", 1)

            # Create session
            session = client.create_session(user, dom)

            # Format expiration time (timestamp is in milliseconds)
            expires_dt = datetime.fromtimestamp(session.expires / 1000)
            expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

            display_results(email_address, session, expires_str)

    except Exception as e:
        console.print(f"[red]Error creating email and session:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def create_session(
    email: str = typer.Argument(..., help="Email address (e.g., user@domain.com)"),
) -> None:
    """Create a session for an email address.

    Creating a session is required to receive emails.
    Only incoming emails with an associated session are saved.
    """
    client = get_client()

    try:
        # Parse email address
        if "@" not in email:
            console.print(f"[red]Invalid email address:[/red] {email}")
            raise typer.Exit(1)

        username, domain = email.split("@", 1)

        session = client.create_session(username, domain)

        expires_dt = datetime.fromtimestamp(session.expires / 1000)
        expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "email": email,
            "username": session.username,
            "domain": session.domain,
            "expires": expires_str,
        }

        def rich_output():
            console.print(Panel(
                f"[bold green]Session Created[/bold green]\n\n"
                f"Email: {email}\n"
                f"Expires: {expires_str}\n"
                f"Username: {session.username}\n"
                f"Domain: {session.domain}",
                title="🔐 Session",
                border_style="green"
            ))

        output_data(data, rich_output)
    except Exception as e:
        console.print(f"[red]Error creating session:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def delete_session(
    email: str = typer.Argument(..., help="Email address (e.g., user@domain.com)"),
) -> None:
    """Delete a session for an email address.

    This will cause incoming emails to be rejected.
    Already saved emails are not deleted.
    """
    client = get_client()

    try:
        if "@" not in email:
            console.print(f"[red]Invalid email address:[/red] {email}")
            raise typer.Exit(1)

        username, domain = email.split("@", 1)

        client.delete_session(username, domain)

        def rich_output():
            console.print(f"[green]✓ Session deleted for {email}[/green]")

        output_data({"deleted": email}, rich_output)
    except Exception as e:
        console.print(f"[red]Error deleting session:[/red] {e}")
        raise typer.Exit(1)


# Inbox commands
@app.command("list")
def list_inbox(
    email: str = typer.Argument(..., help="Email address to check"),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Maximum number of emails to show (max 10)"
    ),
) -> None:
    """List emails in the inbox.

    Shows recent emails for the specified address.
    Maximum of 10 emails can be retrieved.
    """
    client = get_client()

    try:
        emails = client.get_inbox(email, limit=limit)

        if not emails:
            if output_format != OutputFormat.RICH:
                # For non-rich formats, output empty list
                output_data([], lambda: None)
                return
            console.print(f"[yellow]No emails found for {email}[/yellow]")
            return

        # Prepare data for output
        emails_data = [
            {
                "id": email_obj.id,
                "from": email_obj.from_.address,
                "subject": email_obj.subject,
                "date": email_obj.date.strftime("%Y-%m-%d %H:%M"),
            }
            for email_obj in emails
        ]

        def rich_output():
            table = Table(title=f"Inbox for {email}")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("From", style="green")
            table.add_column("Subject", style="white")
            table.add_column("Date", style="blue")

            for email_obj in emails:
                from_addr = f"{email_obj.from_.name} <{email_obj.from_.address}>"
                subject = email_obj.subject[:50] + "..." if len(email_obj.subject) > 50 else email_obj.subject
                date_str = email_obj.date.strftime("%Y-%m-%d %H:%M")

                table.add_row(email_obj.id, from_addr, subject, date_str)

            console.print(table)
            console.print(f"\n[dim]Showing {len(emails)} email(s)[/dim]")

        output_data(emails_data, rich_output)
    except Exception as e:
        console.print(f"[red]Error listing inbox:[/red] {e}")
        raise typer.Exit(1)


@app.command("get")
def get_email(
    email: str = typer.Argument(..., help="Email address"),
    mail_id: str = typer.Argument(..., help="Email ID to retrieve"),
) -> None:
    """Get a specific email by ID.

    Displays full email details including body and attachments.
    """
    client = get_client()

    try:
        email_obj = client.get_email(email, mail_id)

        # Create formatted output
        from_addr = f"{email_obj.from_.name} <{email_obj.from_.address}>"
        to_addr = f"{email_obj.to.name} <{email_obj.to.address}>"
        date_str = email_obj.date.strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "id": email_obj.id,
            "from": email_obj.from_.address,
            "from_name": email_obj.from_.name,
            "to": email_obj.to.address,
            "to_name": email_obj.to.name,
            "subject": email_obj.subject,
            "date": date_str,
            "attachments": len(email_obj.attachments),
            "attachment_files": [att.fileName for att in email_obj.attachments],
            "body": email_obj.body.text or "",
        }

        def rich_output():
            content = f"""
[bold]From:[/bold] {from_addr}
[bold]To:[/bold] {to_addr}
[bold]Subject:[/bold] {email_obj.subject}
[bold]Date:[/bold] {date_str}
[bold]ID:[/bold] {email_obj.id}

[bold]Attachments:[/bold] {len(email_obj.attachments)} file(s)
"""

            if email_obj.attachments:
                for att in email_obj.attachments:
                    status = "✓" if att.present else "✗"
                    content += f"  {status} {att.fileName} (ID: {att.id})\n"

            content += "\n[bold]Body:[/bold]\n"
            if email_obj.body.text:
                content += f"\n{email_obj.body.text}\n"
            else:
                content += "[dim](No text body)[/dim]\n"

            console.print(Panel(content.strip(), title="📧 Email", border_style="blue"))

        output_data(data, rich_output)
    except Exception as e:
        console.print(f"[red]Error getting email:[/red] {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_email(
    email: str = typer.Argument(..., help="Email address"),
    mail_id: str = typer.Argument(..., help="Email ID to delete"),
) -> None:
    """Delete a specific email by ID.

    Permanently removes the email from the inbox.
    """
    client = get_client()

    try:
        client.delete_email(email, mail_id)

        def rich_output():
            console.print(f"[green]✓ Email {mail_id} deleted[/green]")

        output_data({"deleted": mail_id}, rich_output)
    except Exception as e:
        console.print(f"[red]Error deleting email:[/red] {e}")
        raise typer.Exit(1)


@app.command("clear")
def clear_inbox(
    email: str = typer.Argument(..., help="Email address"),
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Delete all emails from the inbox.

    Permanently removes all emails from the specified address.
    """
    client = get_client()

    try:
        if not confirm and output_format == OutputFormat.RICH:
            typer.confirm(f"Delete all emails from {email}?", abort=True)

        client.delete_inbox(email)

        def rich_output():
            console.print(f"[green]✓ Inbox cleared for {email}[/green]")

        output_data({"cleared": email}, rich_output)
    except Exception as e:
        console.print(f"[red]Error clearing inbox:[/red] {e}")
        raise typer.Exit(1)


# Wait commands
@app.command()
def wait(
    email: str = typer.Argument(..., help="Email address to monitor"),
    timeout: int = typer.Option(
        30, "--timeout", "-t", help="Maximum wait time in seconds"
    ),
    interval: int = typer.Option(
        2, "--interval", "-i", help="Check interval in seconds"
    ),
    filter_pattern: Optional[str] = typer.Option(
        None, "--filter", "-f", help="Filter by subject or sender (regex pattern)"
    ),
    print_body: bool = typer.Option(
        False, "--print-body", "-b", help="Also print email body"
    ),
) -> None:
    """Wait for a new email to arrive.

    Monitors the inbox and waits for a new email.
    Optionally filter by subject or sender using regex.
    """
    client = get_client()

    try:
        if output_format == OutputFormat.RICH:
            console.print(f"[dim]Waiting for email to {email}... (timeout: {timeout}s)[/dim]")

        if filter_pattern:
            # Create filter function
            regex = re.compile(filter_pattern, re.IGNORECASE)

            def filter_fn(email_obj: Email) -> bool:
                return bool(
                    regex.search(email_obj.subject) or
                    regex.search(email_obj.from_.address) or
                    regex.search(email_obj.from_.name)
                )

            email_obj = client.wait_for_email_filtered(
                email,
                filter_fn=filter_fn,
                timeout=timeout,
                interval=interval
            )
        else:
            email_obj = client.wait_for_email(
                email,
                timeout=timeout,
                interval=interval
            )

        if email_obj:
            date_str = email_obj.date.strftime("%Y-%m-%d %H:%M:%S")
            data = {
                "id": email_obj.id,
                "from": email_obj.from_.address,
                "from_name": email_obj.from_.name,
                "subject": email_obj.subject,
                "date": date_str,
            }
            if print_body:
                data["body"] = email_obj.body.text or ""

            def rich_output():
                console.print("\n[green]✓ Email received![/green]")
                console.print(f"  From: {email_obj.from_.name} <{email_obj.from_.address}>")
                console.print(f"  Subject: {email_obj.subject}")

                # Print email body if requested
                if print_body:
                    if email_obj.body.text:
                        console.print("\n[bold]Email Body:[/bold]")
                        console.print(f"{email_obj.body.text}")
                    else:
                        console.print("\n[dim]No text body available[/dim]")

            output_data(data, rich_output)
        else:
            def rich_output():
                console.print("\n[yellow]⏱ Timeout: No email received[/yellow]")

            output_data({"timeout": True}, rich_output)
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error waiting for email:[/red] {e}")
        raise typer.Exit(1)


@app.callback()
def main(
    async_mode: bool = typer.Option(
        False, "--async", help="Use async client for operations"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.RICH, "--output", "-o", help="Output format (rich, plain, json)"
    ),
) -> None:
    """Tacomail CLI - Disposable email service command-line interface."""
    global use_async, output_format
    use_async = async_mode
    output_format = output

    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
