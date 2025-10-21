import click
from database import init_db

@click.group()
def cli():
    """📚 Library Management System CLI"""
    pass

@cli.command("init-db")
def initialize_database():
    """Initialize the database (create all tables)."""
    init_db()
    click.echo("✅ Database initialized successfully!")

if __name__ == "__main__":
    cli()