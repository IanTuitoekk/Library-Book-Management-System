import click
from database import SessionLocal
from models import Book

session = SessionLocal()

@click.group()
def cli():
    """Library Management System"""
    pass

# -------- BOOK COMMANDS --------
@cli.group()
def book():
    """Manage books"""
    pass

@book.command("add")
@click.option("--title", prompt=True)
@click.option("--author", prompt=True)
@click.option("--isbn", prompt=True)
def add_book(title, author, isbn):
    new_book = Book(title=title, author=author, isbn=isbn)
    session.add(new_book)
    session.commit()
    click.echo(f"Book '{title}' added.")

@book.command("list")
def list_books():
    books = session.query(Book).all()
    for b in books:
        status = "Available" if b.available else "Borrowed"
        click.echo(f"{b.id}: {b.title} by {b.author} [{status}]")

@book.command("update")
@click.option("--book_id", type=int, prompt=True)
@click.option("--title", prompt=False)
@click.option("--author", prompt=False)
@click.option("--isbn", prompt=False)
def update_book(book_id, title, author, isbn):
    book = session.query(Book).get(book_id)
    if not book:
        click.echo("Book not found")
        return
    if title:
        book.title = title
    if author:
        book.author = author
    if isbn:
        book.isbn = isbn
    session.commit()
    click.echo(f"Book ID {book_id} updated.")

@book.command("delete")
@click.option("--book_id", type=int, prompt=True)
def delete_book(book_id):
    book = session.query(Book).get(book_id)
    if not book:
        click.echo("Book not found")
        return
    session.delete(book)
    session.commit()
    click.echo(f"Book ID {book_id} deleted.")

if __name__ == "__main__":
    cli()
