import click
from datetime import datetime
from database import SessionLocal
from models import Book, Member, BorrowRecord

# Create a DB session
session = SessionLocal()

@click.group()
def cli():
    """Library Management System - Borrow & Return"""
    pass

# ----- BORROW & RETURN COMMANDS -----
@cli.command("borrow")
@click.option("--book_id", type=int, prompt="Book ID to borrow")
@click.option("--member_id", type=int, prompt="Member ID borrowing the book")
def borrow_book(book_id, member_id):
    """Borrow a book for a member"""
    book = session.query(Book).get(book_id)
    member = session.query(Member).get(member_id)

    if not book:
        click.echo("Error: Book not found!")
        return
    if not member:
        click.echo("Error: Member not found!")
        return
    if not book.available:
        click.echo(f"Error: Book '{book.title}' is already borrowed.")
        return

    borrow_record = BorrowRecord(book_id=book_id, member_id=member_id)
    book.available = False
    session.add(borrow_record)
    session.commit()
    click.echo(f"Book '{book.title}' borrowed by member '{member.name}'.")

@cli.command("return")
@click.option("--book_id", type=int, prompt="Book ID to return")
def return_book(book_id):
    """Return a borrowed book"""
    borrow_record = session.query(BorrowRecord).filter_by(book_id=book_id, return_date=None).first()
    if not borrow_record:
        click.echo("No active borrow record found for this book.")
        return

    borrow_record.return_date = datetime.utcnow()
    borrow_record.book.available = True
    session.commit()
    click.echo(f"Book '{borrow_record.book.title}' returned successfully.")

# Entry point
if __name__ == "__main__":
    cli()
