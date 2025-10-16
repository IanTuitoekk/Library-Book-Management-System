import click
from database import get_session, init_db
from models import Book, Member, BorrowRecord
from datetime import date

# ========== MAIN CLI ==========
@click.group()
def cli():
    """📚 Library Management System CLI"""
    pass


# ========== DATABASE ==========
@cli.command("init-db")
def initialize_database():
    """Initialize the database (create all tables)."""
    init_db()
    click.echo("✅ Database initialized successfully!")


# ========== BOOKS ==========
@cli.group()
def books():
    """Manage books"""
    pass


@books.command("list")
def list_books():
    """List all books"""
    session = get_session()
    books_list = session.query(Book).all()
    if not books_list:
        click.echo("⚠️ No books found.")
        return
    for book in books_list:
        available_count = book.total_copies - session.query(BorrowRecord).filter(
            BorrowRecord.book_id == book.id,
            BorrowRecord.return_date.is_(None)
        ).count()
        status = f"✅ {available_count}/{book.total_copies} available" if available_count > 0 else "❌ All borrowed"
        click.echo(f"{book.id}: {book.title} by {book.author} - {status}")


@books.command("add")
def add_book():
    """Add a new book"""
    title = click.prompt("Enter book title")
    author = click.prompt("Enter author name")
    total_copies = click.prompt("Enter total copies", type=int)

    session = get_session()
    book = Book(title=title, author=author, total_copies=total_copies)
    session.add(book)
    session.commit()
    click.echo("✅ Book added successfully!")
    session.close()


# ========== MEMBERS ==========
@cli.group()
def members():
    """Manage members"""
    pass


@members.command("list")
def list_members():
    """List all members"""
    session = get_session()
    members_list = session.query(Member).all()
    if not members_list:
        click.echo("⚠️ No members found.")
        return
    for member in members_list:
        click.echo(f"{member.id}: {member.name} ({member.email}) joined {member.join_date}")
    session.close()


@members.command("add")
def add_member():
    """Add a new member"""
    name = click.prompt("Enter member name")
    email = click.prompt("Enter email")

    session = get_session()
    member = Member(name=name, email=email)
    session.add(member)
    session.commit()
    click.echo("✅ Member added successfully!")
    session.close()


# ========== BORROW RECORDS ==========
@cli.group()
def records():
    """Manage borrow records"""
    pass


@records.command("list")
def list_records():
    """List all borrow records"""
    session = get_session()
    records_list = session.query(BorrowRecord).all()
    if not records_list:
        click.echo("⚠️ No borrow records found.")
        return
    for record in records_list:
        status = f"Returned {record.return_date}" if record.return_date else "Not returned yet"
        click.echo(
            f"Record #{record.id}: Book {record.book.title} by {record.book.author} | "
            f"Member: {record.member.name} | Borrowed: {record.borrow_date} | {status}"
        )
    session.close()


@records.command("borrow")
def borrow_book():
    """Borrow a book"""
    session = get_session()
    book_id = click.prompt("Enter Book ID", type=int)
    member_id = click.prompt("Enter Member ID", type=int)

    book = session.query(Book).get(book_id)
    member = session.query(Member).get(member_id)

    if not book:
        click.echo("❌ Book not found.")
        session.close()
        return
    if not member:
        click.echo("❌ Member not found.")
        session.close()
        return

    # Check if copies are available
    borrowed_count = session.query(BorrowRecord).filter(
        BorrowRecord.book_id == book.id,
        BorrowRecord.return_date.is_(None)
    ).count()
    
    if borrowed_count >= book.total_copies:
        click.echo(f"⚠️ All {book.total_copies} copies of this book are currently borrowed.")
        session.close()
        return

    record = BorrowRecord(book_id=book.id, member_id=member.id)
    session.add(record)
    session.commit()
    click.echo(f"✅ {member.name} successfully borrowed '{book.title}'.")
    session.close()


@records.command("return")
def return_book():
    """Return a borrowed book"""
    session = get_session()
    record_id = click.prompt("Enter Borrow Record ID", type=int)

    record = session.query(BorrowRecord).get(record_id)
    if not record:
        click.echo("❌ Borrow record not found.")
        session.close()
        return
    if record.return_date:
        click.echo("⚠️ This book has already been returned.")
        session.close()
        return

    record.return_date = date.today()
    session.commit()
    click.echo(f"✅ '{record.book.title}' returned successfully by {record.member.name}.")
    session.close()


if __name__ == "__main__":
    cli()