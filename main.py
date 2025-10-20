import click
from database import get_session, init_db
from models import Book, Member, BorrowRecord
from datetime import date
from sqlalchemy.exc import IntegrityError

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
    books_list = Book.get_all(session)
    if not books_list:
        click.echo(" No books found.")
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
        click.echo(f" Error: {e}")
    finally:
        session.close()


@books.command("delete")
def delete_book():
    """Delete a book"""
    session = get_session()
    book_id = click.prompt("Enter Book ID to delete", type=int)
    
    book = Book.find_by_id(session, book_id)
    if not book:
        click.echo(" Book not found.")
        session.close()
        return
    
    # Check if book has unreturned borrows
    active_borrows = session.query(BorrowRecord).filter(
        BorrowRecord.book_id == book.id,
        BorrowRecord.return_date.is_(None)
    ).count()
    
    if active_borrows > 0:
        click.echo(f" Cannot delete book. It has {active_borrows} active borrow(s).")
        session.close()
        return
    
    confirm = click.confirm(f"Are you sure you want to delete '{book.title}'?")
    if confirm:
        book.delete(session)
        click.echo("✅ Book deleted successfully!")
    else:
        click.echo(" Deletion cancelled.")
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
        click.echo(" Invalid choice.")
        session.close()
        return
    
    if not books_list:
        click.echo(" No books found.")
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
        click.echo(" Book not found.")
        session.close()
        return
    
    click.echo(f"\n📖 Book: {book.title} by {book.author}")
    click.echo(f"Total copies: {book.total_copies}")
    click.echo(f"Available: {book.available_copies}\n")
    
    if not book.borrow_records:
        click.echo(" No borrow records for this book.")
    else:
        click.echo("Borrow History:")
        for record in book.borrow_records:
            status = f"Returned {record.return_date}" if record.return_date else "📚 Currently borrowed"
            click.echo(f"  - Record #{record.id}: {record.member.name} | Borrowed: {record.borrow_date} | {status}")
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
    members_list = Member.get_all(session)
    if not members_list:
        click.echo("⚠️ No members found.")
        session.close()
        return
    for member in members_list:
        active_count = len(member.active_borrows)
        status = f"({active_count} active borrow(s))" if active_count > 0 else ""
        click.echo(f"{member.id}: {member.name} ({member.email}) joined {member.join_date} {status}")
    session.close()


@members.command("add")
def add_member():
    """Add a new member"""
    name = click.prompt("Enter member name")
    email = click.prompt("Enter email")

    session = get_session()
    try:
        member = Member.create(session, name=name, email=email)
        click.echo(f"✅ Member added successfully! (ID: {member.id})")
    except IntegrityError:
        session.rollback()
        click.echo(" Error: Email already exists.")
    except ValueError as e:
        click.echo(f" Error: {e}")
    finally:
        session.close()


@members.command("delete")
def delete_member():
    """Delete a member"""
    session = get_session()
    member_id = click.prompt("Enter Member ID to delete", type=int)
    
    member = Member.find_by_id(session, member_id)
    if not member:
        click.echo(" Member not found.")
        session.close()
        return
    
    # Check if member has unreturned books
    active_borrows = len(member.active_borrows)
    if active_borrows > 0:
        click.echo(f" Cannot delete member. They have {active_borrows} unreturned book(s).")
        session.close()
        return
    
    confirm = click.confirm(f"Are you sure you want to delete member '{member.name}'?")
    if confirm:
        member.delete(session)
        click.echo("✅ Member deleted successfully!")
    else:
        click.echo(" Deletion cancelled.")
    session.close()


@members.command("find")
def find_member():
    """Find a member by attribute"""
    click.echo("Search by:")
    click.echo("1. ID")
    click.echo("2. Name")
    click.echo("3. Email")
    choice = click.prompt("Enter choice", type=int)
    
    session = get_session()
    
    if choice == 1:
        member_id = click.prompt("Enter Member ID", type=int)
        member = Member.find_by_id(session, member_id)
        members_list = [member] if member else []
    elif choice == 2:
        name = click.prompt("Enter member name")
        members_list = Member.find_by_attribute(session, name=name)
    elif choice == 3:
        email = click.prompt("Enter email")
        members_list = Member.find_by_attribute(session, email=email)
    else:
        click.echo(" Invalid choice.")
        session.close()
        return
    
    if not members_list:
        click.echo(" No members found.")
    else:
        for member in members_list:
            click.echo(f"{member.id}: {member.name} ({member.email}) - Joined: {member.join_date}")
    session.close()


@members.command("related")
def view_related_members():
    """View borrow records related to a member"""
    session = get_session()
    member_id = click.prompt("Enter Member ID", type=int)
    
    member = Member.find_by_id(session, member_id)
    if not member:
        click.echo(" Member not found.")
        session.close()
        return
    
    click.echo(f"\n👤 Member: {member.name} ({member.email})")
    click.echo(f"Joined: {member.join_date}\n")
    
    if not member.borrow_records:
        click.echo(" No borrow records for this member.")
    else:
        click.echo("Borrow History:")
        for record in member.borrow_records:
            status = f"Returned {record.return_date}" if record.return_date else "📚 Currently borrowed"
            click.echo(f"  - Record #{record.id}: {record.book.title} | Borrowed: {record.borrow_date} | {status}")
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
    records_list = BorrowRecord.get_all(session)
    if not records_list:
        click.echo(" No borrow records found.")
        session.close()
        return
    for record in records_list:
        status = f"Returned {record.return_date}" if record.return_date else "📚 Not returned yet"
        click.echo(
            f"Record #{record.id}: Book '{record.book.title}' by {record.book.author} | "
            f"Member: {record.member.name} | Borrowed: {record.borrow_date} | {status}"
        )
    session.close()


@records.command("borrow")
def borrow_book():
    """Borrow a book (create a borrow record)"""
    session = get_session()
    book_id = click.prompt("Enter Book ID", type=int)
    member_id = click.prompt("Enter Member ID", type=int)

    book = Book.find_by_id(session, book_id)
    member = Member.find_by_id(session, member_id)

    if not book:
        click.echo(" Book not found.")
        session.close()
        return
    if not member:
        click.echo(" Member not found.")
        session.close()
        return

    # Check if copies are available
    if book.available_copies < 1:
        click.echo(f"⚠️ All {book.total_copies} copies of this book are currently borrowed.")
        session.close()
        return

    try:
        record = BorrowRecord.create(session, book_id=book.id, member_id=member.id)
        click.echo(f"✅ {member.name} successfully borrowed '{book.title}'. (Record ID: {record.id})")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        session.close()


@records.command("return")
def return_book():
    """Return a borrowed book"""
    session = get_session()
    record_id = click.prompt("Enter Borrow Record ID", type=int)

    record = BorrowRecord.find_by_id(session, record_id)
    if not record:
        click.echo(" Borrow record not found.")
        session.close()
        return
    if record.return_date:
        click.echo(" This book has already been returned.")
        session.close()
        return

    record.return_date = date.today()
    session.commit()
    click.echo(f"✅ '{record.book.title}' returned successfully by {record.member.name}.")
    session.close()


@records.command("delete")
def delete_record():
    """Delete a borrow record"""
    session = get_session()
    record_id = click.prompt("Enter Borrow Record ID to delete", type=int)
    
    record = BorrowRecord.find_by_id(session, record_id)
    if not record:
        click.echo(" Borrow record not found.")
        session.close()
        return
    
    confirm = click.confirm(f"Are you sure you want to delete record #{record.id}?")
    if confirm:
        record.delete(session)
        click.echo("✅ Borrow record deleted successfully!")
    else:
        click.echo(" Deletion cancelled.")
    session.close()


@records.command("find")
def find_record():
    """Find a borrow record by attribute"""
    click.echo("Search by:")
    click.echo("1. Record ID")
    click.echo("2. Book ID")
    click.echo("3. Member ID")
    choice = click.prompt("Enter choice", type=int)
    
    session = get_session()
    
    if choice == 1:
        record_id = click.prompt("Enter Record ID", type=int)
        record = BorrowRecord.find_by_id(session, record_id)
        records_list = [record] if record else []
    elif choice == 2:
        book_id = click.prompt("Enter Book ID", type=int)
        records_list = BorrowRecord.find_by_attribute(session, book_id=book_id)
    elif choice == 3:
        member_id = click.prompt("Enter Member ID", type=int)
        records_list = BorrowRecord.find_by_attribute(session, member_id=member_id)
    else:
        click.echo(" Invalid choice.")
        session.close()
        return
    
    if not records_list:
        click.echo("⚠️ No borrow records found.")
    else:
        for record in records_list:
            status = f"Returned {record.return_date}" if record.return_date else "Not returned"
            click.echo(f"Record #{record.id}: {record.book.title} | {record.member.name} | {status}")
    session.close()


if __name__ == "__main__":
    cli()