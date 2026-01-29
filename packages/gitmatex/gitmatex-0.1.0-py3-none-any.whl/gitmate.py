import click
import os

@click.group()
def cli():
    """GitMate CLI - Simple GitHub Helper"""
    pass

@cli.command()
def hello():
    """Say hello"""
    click.echo("👋 Hello from GitMate CLI!")

if __name__ == "__main__":
    cli()
