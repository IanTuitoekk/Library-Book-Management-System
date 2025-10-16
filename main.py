import click
from datetime import datetime
from database import SessionLocal
from models import Book, Member, BorrowRecord

# Create a DB session
session = SessionLocal()

@click.group()
def cli():
    """Library Management System CLI"""
    pass

# =======================
#       BOOK COMMANDS
# =======================
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

# =======================
#       MEMBER COMMANDS
# =======================
@cli.group()
def member():
    """Manage library members"""
    pass

@member.command("add")
@click.option("--name", prompt="Member Name")
@click.option("--email", prompt="Member Email")
def add_member(name, email):
    if session.query(Member).filter_by(email=email).first():
        click.echo("Error: Email already exists!")
        return
    new_member = Member(name=name, email=email)
    session.add(new_member)
    session.commit()
    click.echo(f"Member '{name}' added successfully.")

@member.command("list")
def list_members():
    members = session.query(Member).all()
    if not members:
        click.echo("No members found.")
        return
    click.echo("ID | Name | Email | Join Date")
    click.echo("-" * 40)
    for m in members:
        join_date = m.join_date.strftime("%Y-%m-%d")
        click.echo(f"{m.id} | {m.name} | {m.email} | {join_date}")

@member.command("update")
@click.option("--member_id", type=int, prompt="Member ID to update")
@click.option("--name", prompt="New name", required=False)
@click.option("--email", prompt="New email", required=False)
def update_member(member_id, name, email):
    member = session.query(Member).get(member_id)
    if not member:
        click.echo("Member not found!")
        return
    if name:
        member.name = name
    if email:
        if session.query(Member).filter(Member.email==email, Member.id != member_id).first():
            click.echo("Error: Email already exists!")
            return
        member.email = email
    session.commit()
    click.echo(f"Member ID {member_id} updated successfully.")

@member.command("delete")
@click.option("--member_id", type=int, prompt="Member ID to delete")
def delete_member(member_id):
    member = session.query(Member).get(member_id)
    if not member:
        click.echo("Member not found!")
        return
    session.delete(member)
    session.commit()
    click.echo(f"Member ID {member_id} deleted successfully.")

# =======================
#       BORROW & RETURN
# =======================
@cli.command("borrow")
@click.option("--book_id", type=int, prompt="Book ID to borrow")
@click.option("--member_id", type=int, prompt="Member ID borrowing the book")
def borrow_book(book_id, member_id):
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
    record = BorrowRecord(book_id=book_id, member_id=member_id)
    book.available = False
    session.add(record)
    session.commit()
    click.echo(f"Book '{book.title}' borrowed by '{member.name}'.")

@cli.command("return")
@click.option("--book_id", type=int, prompt="Book ID to return")
def return_book(book_id):
    record = session.query(BorrowRecord).filter_by(book_id=book_id, return_date=None).first()
    if not record:
        click.echo("No active borrow record found for this book.")
        return
    record.return_date = datetime.utcnow()
    record.book.available = True
    session.commit()
    click.echo(f"Book '{record.book.title}' returned successfully.")

# =======================
#       HISTORY VIEW
# =======================
@cli.command("history")
def view_history():
    records = session.query(BorrowRecord).all()
    if not records:
        click.echo("No borrowing history found.")
        return
    click.echo("Book | Member | Borrowed At | Returned At")
    click.echo("-" * 60)
    for r in records:
        borrowed = r.borrow_date.strftime("%Y-%m-%d %H:%M")
        returned = r.return_date.strftime("%Y-%m-%d %H:%M") if r.return_date else "Not returned"
        click.echo(f"{r.book.title} | {r.member.name} | {borrowed} | {returned}")

# Entry point
if __name__ == "__main__":
    cli()