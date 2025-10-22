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

# ========== HISTORY ==========
@cli.group()
def history():
    """View library activity history"""
    pass

@history.command("all")
def view_all_history():
    """View complete library history"""
    session = get_session()
    
    books = Book.get_all(session)
    members = Member.get_all(session)
    records = BorrowRecord.get_all(session)
    
    click.echo("\n" + "="*60)
    click.echo("📊 LIBRARY MANAGEMENT SYSTEM - COMPLETE HISTORY")
    click.echo("="*60)
    
    # Books Summary
    click.echo(f"\n📚 BOOKS SUMMARY:")
    click.echo(f"   Total Books: {len(books)}")
    if books:
        total_copies = sum(book.total_copies for book in books)
        available_copies = sum(book.available_copies for book in books)
        click.echo(f"   Total Copies: {total_copies}")
        click.echo(f"   Available Copies: {available_copies}")
        click.echo(f"   Borrowed Copies: {total_copies - available_copies}")
    
    # Members Summary
    click.echo(f"\n👥 MEMBERS SUMMARY:")
    click.echo(f"   Total Members: {len(members)}")
    if members:
        active_members = sum(1 for member in members if len(member.active_borrows) > 0)
        click.echo(f"   Active Borrowers: {active_members}")
    
    # Borrow Records Summary
    click.echo(f"\n📖 BORROW RECORDS SUMMARY:")
    click.echo(f"   Total Borrows: {len(records)}")
    if records:
        active_records = sum(1 for record in records if not record.return_date)
        returned_records = len(records) - active_records
        click.echo(f"   Active Borrows: {active_records}")
        click.echo(f"   Returned Books: {returned_records}")
    
    click.echo("\n" + "="*60)
    session.close()

@history.command("books")
def view_books_history():
    """View all books with their history"""
    session = get_session()
    books = Book.get_all(session)
    
    if not books:
        click.echo("⚠️ No books in the system.")
        session.close()
        return
    
    click.echo("\n" + "="*60)
    click.echo("📚 BOOKS HISTORY")
    click.echo("="*60 + "\n")
    
    for book in books:
        click.echo(f"📖 {book.title} by {book.author}")
        click.echo(f"   ID: {book.id} | Copies: {book.available_copies}/{book.total_copies} available")
        
        if book.borrow_records:
            click.echo(f"   Borrow History ({len(book.borrow_records)} total):")
            for record in book.borrow_records:
                status = f"✅ Returned {record.return_date}" if record.return_date else "📚 Active"
                click.echo(f"      - {record.member.name} | {record.borrow_date} | {status}")
        else:
            click.echo("   No borrow history")
        click.echo()
    
    session.close()

@history.command("members")
def view_members_history():
    """View all members with their history"""
    session = get_session()
    members = Member.get_all(session)
    
    if not members:
        click.echo("⚠️ No members in the system.")
        session.close()
        return
    
    click.echo("\n" + "="*60)
    click.echo("👥 MEMBERS HISTORY")
    click.echo("="*60 + "\n")
    
    for member in members:
        active_count = len(member.active_borrows)
        click.echo(f"👤 {member.name} ({member.email})")
        click.echo(f"   ID: {member.id} | Joined: {member.join_date}")
        click.echo(f"   Active Borrows: {active_count}")
        
        if member.borrow_records:
            click.echo(f"   Borrow History ({len(member.borrow_records)} total):")
            for record in member.borrow_records:
                status = f"✅ Returned" if record.return_date else "📚 Active"
                days = f"({record.days_borrowed} days)"
                click.echo(f"      - {record.book.title} | {record.borrow_date} | {status} {days}")
        else:
            click.echo("   No borrow history")
        click.echo()
    
    session.close()

@history.command("stats")
def view_statistics():
    """View library statistics"""
    session = get_session()
    
    books = Book.get_all(session)
    members = Member.get_all(session)
    records = BorrowRecord.get_all(session)
    
    click.echo("\n" + "="*60)
    click.echo("📊 LIBRARY STATISTICS")
    click.echo("="*60 + "\n")
    
    # Book Statistics
    if books:
        click.echo("📚 BOOK STATISTICS:")
        total_copies = sum(book.total_copies for book in books)
        available_copies = sum(book.available_copies for book in books)
        borrowed_copies = total_copies - available_copies
        
        click.echo(f"   Total Book Titles: {len(books)}")
        click.echo(f"   Total Copies: {total_copies}")
        click.echo(f"   Available: {available_copies} ({(available_copies/total_copies*100):.1f}%)")
        click.echo(f"   Borrowed: {borrowed_copies} ({(borrowed_copies/total_copies*100):.1f}%)")
        
        # Most borrowed books
        if records:
            book_borrow_count = {}
            for record in records:
                book_id = record.book_id
                book_borrow_count[book_id] = book_borrow_count.get(book_id, 0) + 1
            
            if book_borrow_count:
                most_borrowed_id = max(book_borrow_count, key=book_borrow_count.get)
                most_borrowed_book = Book.find_by_id(session, most_borrowed_id)
                click.echo(f"\n   Most Borrowed Book:")
                click.echo(f"      '{most_borrowed_book.title}' - {book_borrow_count[most_borrowed_id]} times")
    
    # Member Statistics
    if members:
        click.echo(f"\n👥 MEMBER STATISTICS:")
        click.echo(f"   Total Members: {len(members)}")
        active_members = [m for m in members if len(m.active_borrows) > 0]
        click.echo(f"   Active Borrowers: {len(active_members)}")
        
        # Most active member
        if records:
            member_borrow_count = {}
            for record in records:
                member_id = record.member_id
                member_borrow_count[member_id] = member_borrow_count.get(member_id, 0) + 1
            
            if member_borrow_count:
                most_active_id = max(member_borrow_count, key=member_borrow_count.get)
                most_active_member = Member.find_by_id(session, most_active_id)
                click.echo(f"\n   Most Active Member:")
                click.echo(f"      {most_active_member.name} - {member_borrow_count[most_active_id]} borrows")
    
    # Borrow Statistics
    if records:
        click.echo(f"\n📖 BORROW STATISTICS:")
        click.echo(f"   Total Borrows: {len(records)}")
        active = [r for r in records if not r.return_date]
        returned = [r for r in records if r.return_date]
        click.echo(f"   Currently Borrowed: {len(active)}")
        click.echo(f"   Returned: {len(returned)}")
        
        if returned:
            avg_days = sum(r.days_borrowed for r in returned) / len(returned)
            click.echo(f"   Average Borrow Duration: {avg_days:.1f} days")
    
    click.echo("\n" + "="*60)
    session.close()

if __name__ == "__main__":
    cli()