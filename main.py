import click
from database import SessionLocal
from models import Book

# Create a DB session
session = SessionLocal()

@click.group()
def cli():
    """Library Management System - Book Management"""
    pass

# ----- BOOK COMMANDS -----
@cli.group()
def book():
    """Manage library books"""
    pass

@book.command("add")
@click.option("--title", prompt="Book Title")
@click.option("--author", prompt="Author")
@click.option("--isbn", prompt="ISBN")
def add_book(title, author, isbn):
    """Add a new book"""
    # Check if ISBN already exists
    if session.query(Book).filter_by(isbn=isbn).first():
        click.echo("Error: ISBN already exists!")
        return

    new_book = Book(title=title, author=author, isbn=isbn)
    session.add(new_book)
    session.commit()
    click.echo(f"Book '{title}' by {author} added successfully.")

@book.command("list")
def list_books():
    """List all books"""
    books = session.query(Book).all()
    if not books:
        click.echo("No books found.")
        return
    click.echo("ID | Title | Author | ISBN | Status")
    click.echo("-" * 60)
    for b in books:
        status = "Available" if b.available else "Borrowed"
        click.echo(f"{b.id} | {b.title} | {b.author} | {b.isbn} | {status}")

@book.command("update")
@click.option("--book_id", type=int, prompt="Book ID to update")
@click.option("--title", prompt="New title", required=False)
@click.option("--author", prompt="New author", required=False)
@click.option("--isbn", prompt="New ISBN", required=False)
def update_book(book_id, title, author, isbn):
    """Update an existing book"""
    book = session.query(Book).get(book_id)
    if not book:
        click.echo("Book not found!")
        return
    if title:
        book.title = title
    if author:
        book.author = author
    if isbn:
        # check for duplicate ISBN
        if session.query(Book).filter(Book.isbn==isbn, Book.id != book_id).first():
            click.echo("Error: ISBN already exists!")
            return
        book.isbn = isbn
    session.commit()
    click.echo(f"Book ID {book_id} updated successfully.")

@book.command("delete")
@click.option("--book_id", type=int, prompt="Book ID to delete")
def delete_book(book_id):
    """Delete a book"""
    book = session.query(Book).get(book_id)
    if not book:
        click.echo("Book not found!")
        return
    session.delete(book)
    session.commit()
    click.echo(f"Book ID {book_id} deleted successfully.")

# Entry point
if __name__ == "__main__":
    cli()
