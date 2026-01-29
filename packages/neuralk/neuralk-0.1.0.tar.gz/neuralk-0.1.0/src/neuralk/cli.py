"""Command-line interface for Neuralk SDK."""

import click

from neuralk.neuralk import get_access_token


@click.group()
def main():
    """Neuralk SDK command-line interface."""
    pass


@main.command()
def login():
    """Display instructions to create an account and get an API key."""
    get_access_token()
