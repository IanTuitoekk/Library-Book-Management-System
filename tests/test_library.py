# tests/test_library.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Book, Member, BorrowRecord
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Use a temporary test database (if available)
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_create_book(db_session):
    new_book = Book(title="1984", author="George Orwell", isbn="9780451524935")
    db_session.add(new_book)
    db_session.commit()
    result = db_session.query(Book).filter_by(title="1984").first()
    assert result is not None
    assert result.author == "George Orwell"

def test_create_member(db_session):
    new_member = Member(name="Alice", email="alice@example.com")
    db_session.add(new_member)
    db_session.commit()
    result = db_session.query(Member).filter_by(name="Alice").first()
    assert result is not None
    assert result.email == "alice@example.com"

def test_borrow_record(db_session):
    book = Book(title="Brave New World", author="Aldous Huxley", isbn="9780060850524")
    member = Member(name="Bob", email="bob@example.com")
    db_session.add_all([book, member])
    db_session.commit()

    record = BorrowRecord(book_id=book.id, member_id=member.id)
    db_session.add(record)
    db_session.commit()

    result = db_session.query(BorrowRecord).filter_by(member_id=member.id).first()
    assert result is not None
    assert result.book_id == book.id
