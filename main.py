import click
from datetime import date
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

# ========== MEMBERS ==========
@cli.group()
def members():
    """Manage library members"""
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
        status = f"📚 {active_count} active borrow(s)" if active_count > 0 else "✅ No active borrows"
        click.echo(f"{member.id}: {member.name} ({member.email}) - {status}")
    session.close()

@members.command("add")
def add_member():
    """Add a new member"""
    name = click.prompt("Enter member name")
    email = click.prompt("Enter email address")
    
    session = get_session()
    try:
        member = Member.create(session, name=name, email=email)
        click.echo(f"✅ Member added successfully! (ID: {member.id})")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        session.close()

@members.command("delete")
def delete_member():
    """Delete a member"""
    session = get_session()
    member_id = click.prompt("Enter Member ID to delete", type=int)
    
    member = Member.find_by_id(session, member_id)
    if not member:
        click.echo("⚠️ Member not found.")
        session.close()
        return
    
    # Check if member has unreturned borrows
    active_borrows = len(member.active_borrows)
    
    if active_borrows > 0:
        click.echo(f"❌ Cannot delete member. They have {active_borrows} unreturned book(s).")
        session.close()
        return
    
    confirm = click.confirm(f"Are you sure you want to delete member '{member.name}'?")
    if confirm:
        member.delete(session)
        click.echo("✅ Member deleted successfully!")
    else:
        click.echo("⚠️ Deletion cancelled.")
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
        email = click.prompt("Enter email address")
        members_list = Member.find_by_attribute(session, email=email)
    else:
        click.echo("❌ Invalid choice.")
        session.close()
        return
    
    if not members_list:
        click.echo("⚠️ No members found.")
    else:
        for member in members_list:
            active_count = len(member.active_borrows)
            click.echo(f"{member.id}: {member.name} ({member.email}) - {active_count} active borrow(s)")
    session.close()

@members.command("related")
def view_related_members():
    """View borrow records related to a member"""
    session = get_session()
    member_id = click.prompt("Enter Member ID", type=int)
    
    member = Member.find_by_id(session, member_id)
    if not member:
        click.echo("⚠️ Member not found.")
        session.close()
        return
    
    click.echo(f"\n👤 Member: {member.name} ({member.email})")
    click.echo(f"Join Date: {member.join_date}")
    click.echo(f"Active Borrows: {len(member.active_borrows)}\n")
    
    if not member.borrow_records:
        click.echo("⚠️ No borrow records for this member.")
    else:
        click.echo("Borrow History:")
        for record in member.borrow_records:
            status = f"Returned {record.return_date}" if record.return_date else "📚 Currently borrowed"
            click.echo(f"  - Record #{record.id}: {record.book.title} | Borrowed: {record.borrow_date} | {status}")
    session.close()

# ========== BORROW & RETURN ==========
@cli.group()
def borrow():
    """Manage book borrowing"""
    pass

@borrow.command("book")
def borrow_book():
    """Borrow a book"""
    session = get_session()
    
    # Get member
    member_id = click.prompt("Enter Member ID", type=int)
    member = Member.find_by_id(session, member_id)
    if not member:
        click.echo("⚠️ Member not found.")
        session.close()
        return
    
    # Get book
    book_id = click.prompt("Enter Book ID", type=int)
    book = Book.find_by_id(session, book_id)
    if not book:
        click.echo("⚠️ Book not found.")
        session.close()
        return
    
    # Check availability
    if book.available_copies <= 0:
        click.echo(f"❌ No copies of '{book.title}' are available.")
        session.close()
        return
    
    # Create borrow record
    try:
        record = BorrowRecord.create(session, book_id=book.id, member_id=member.id)
        click.echo(f"✅ Book '{book.title}' borrowed successfully by {member.name}!")
        click.echo(f"   Record ID: {record.id} | Date: {record.borrow_date}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        session.close()

@borrow.command("return")
def return_book():
    """Return a borrowed book"""
    session = get_session()
    
    record_id = click.prompt("Enter Borrow Record ID", type=int)
    record = BorrowRecord.find_by_id(session, record_id)
    
    if not record:
        click.echo("⚠️ Borrow record not found.")
        session.close()
        return
    
    if record.return_date:
        click.echo(f"⚠️ This book was already returned on {record.return_date}.")
        session.close()
        return
    
    # Update return date
    try:
        record.return_date = date.today()
        session.commit()
        click.echo(f"✅ Book '{record.book.title}' returned successfully!")
        click.echo(f"   Borrowed for {record.days_borrowed} days")
    except Exception as e:
        session.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        session.close()

@borrow.command("list")
def list_borrows():
    """List all borrow records"""
    session = get_session()
    records = BorrowRecord.get_all(session)
    
    if not records:
        click.echo("⚠️ No borrow records found.")
        session.close()
        return
    
    click.echo("\n📚 All Borrow Records:")
    for record in records:
        status = "✅ Returned" if record.return_date else "📚 Active"
        days = f"{record.days_borrowed} days" if record.return_date else f"{record.days_borrowed} days (ongoing)"
        click.echo(f"  #{record.id}: {record.book.title} → {record.member.name} | {status} | {days}")
    session.close()

@borrow.command("active")
def list_active_borrows():
    """List all active (unreturned) borrows"""
    session = get_session()
    records = session.query(BorrowRecord).filter(BorrowRecord.return_date.is_(None)).all()
    
    if not records:
        click.echo("✅ No active borrows. All books returned!")
        session.close()
        return
    
    click.echo("\n📚 Active Borrows:")
    for record in records:
        click.echo(f"  #{record.id}: {record.book.title} → {record.member.name} | Borrowed: {record.borrow_date} | Days: {record.days_borrowed}")
    session.close()

if __name__ == "__main__":
    cli()