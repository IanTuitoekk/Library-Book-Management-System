import click
from database import get_session, init_db
from models import Book, BorrowRecord, Member

@click.group()
def cli():
    """📚 Library Management System CLI"""
    pass

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
    books_list = Book.get_all(session)
    if not books_list:
        click.echo("⚠️ No books found.")
        session.close()
        return
    for book in books_list:
        available_count = book.available_copies
        status = f"✅ {available_count}/{book.total_copies} available" if available_count > 0 else "❌ All borrowed"
        click.echo(f"{book.id}: {book.title} by {book.author} - {status}")
    session.close()

@books.command("add")
def add_book():
    """Add a new book"""
    title = click.prompt("Enter book title")
    author = click.prompt("Enter author name")
    total_copies = click.prompt("Enter total copies", type=int, default=1)

    session = get_session()
    try:
        book = Book.create(session, title=title, author=author, total_copies=total_copies)
        click.echo(f"✅ Book added successfully! (ID: {book.id})")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    finally:
        session.close()

@books.command("delete")
def delete_book():
    """Delete a book"""
    session = get_session()
    book_id = click.prompt("Enter Book ID to delete", type=int)
    
    book = Book.find_by_id(session, book_id)
    if not book:
        click.echo("⚠️ Book not found.")
        session.close()
        return
    
    # Check if book has unreturned borrows
    active_borrows = session.query(BorrowRecord).filter(
        BorrowRecord.book_id == book.id,
        BorrowRecord.return_date.is_(None)
    ).count()
    
    if active_borrows > 0:
        click.echo(f"❌ Cannot delete book. It has {active_borrows} active borrow(s).")
        session.close()
        return
    
    confirm = click.confirm(f"Are you sure you want to delete '{book.title}'?")
    if confirm:
        book.delete(session)
        click.echo("✅ Book deleted successfully!")
    else:
        click.echo("⚠️ Deletion cancelled.")
    session.close()

@books.command("find")
def find_book():
    """Find a book by attribute"""
    click.echo("Search by:")
    click.echo("1. ID")
    click.echo("2. Title")
    click.echo("3. Author")
    choice = click.prompt("Enter choice", type=int)
    
    session = get_session()
    
    if choice == 1:
        book_id = click.prompt("Enter Book ID", type=int)
        book = Book.find_by_id(session, book_id)
        books_list = [book] if book else []
    elif choice == 2:
        title = click.prompt("Enter book title")
        books_list = Book.find_by_attribute(session, title=title)
    elif choice == 3:
        author = click.prompt("Enter author name")
        books_list = Book.find_by_attribute(session, author=author)
    else:
        click.echo("❌ Invalid choice.")
        session.close()
        return
    
    if not books_list:
        click.echo("⚠️ No books found.")
    else:
        for book in books_list:
            available_count = book.available_copies
            click.echo(f"{book.id}: {book.title} by {book.author} - {available_count}/{book.total_copies} available")
    session.close()

@books.command("related")
def view_related_books():
    """View borrow records related to a book"""
    session = get_session()
    book_id = click.prompt("Enter Book ID", type=int)
    
    book = Book.find_by_id(session, book_id)
    if not book:
        click.echo("⚠️ Book not found.")
        session.close()
        return
    
    click.echo(f"\n📖 Book: {book.title} by {book.author}")
    click.echo(f"Total copies: {book.total_copies}")
    click.echo(f"Available: {book.available_copies}\n")
    
    if not book.borrow_records:
        click.echo("⚠️ No borrow records for this book.")
    else:
        click.echo("Borrow History:")
        for record in book.borrow_records:
            status = f"Returned {record.return_date}" if record.return_date else "📚 Currently borrowed"
            click.echo(f"  - Record #{record.id}: {record.member.name} | Borrowed: {record.borrow_date} | {status}")
    session.close()

if __name__ == "__main__":
    cli()