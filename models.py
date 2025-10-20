# models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, validates
from datetime import date
import re

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    total_copies = Column(Integer, default=1)
    available = Column(Boolean, default=True)

    borrow_records = relationship("BorrowRecord", back_populates="book", cascade="all, delete-orphan")

    # ========== PROPERTY METHODS  ==========
    @validates('title', 'author')
    def validate_not_empty(self, key, value):
        """Ensure title and author are not empty strings."""
        if not value or not value.strip():
            raise ValueError(f"{key.capitalize()} cannot be empty")
        return value.strip()

    @validates('total_copies')
    def validate_total_copies(self, key, value):
        """Ensure total_copies is a positive integer."""
        if value < 1:
            raise ValueError("Total copies must be at least 1")
        return value

    @property
    def available_copies(self):
        """Calculate available copies dynamically."""
        from database import get_session
        session = get_session()
        borrowed_count = session.query(BorrowRecord).filter(
            BorrowRecord.book_id == self.id,
            BorrowRecord.return_date.is_(None)
        ).count()
        session.close()
        return self.total_copies - borrowed_count

    # ========== ORM METHODS ==========
    @classmethod
    def create(cls, session, title, author, total_copies=1):
        """Create a new book."""
        book = cls(title=title, author=author, total_copies=total_copies)
        session.add(book)
        session.commit()
        return book

    @classmethod
    def get_all(cls, session):
        """Get all books."""
        return session.query(cls).all()

    @classmethod
    def find_by_id(cls, session, book_id):
        """Find a book by ID."""
        return session.query(cls).get(book_id)

    @classmethod
    def find_by_attribute(cls, session, **kwargs):
        """Find books by attribute (e.g., title, author)."""
        return session.query(cls).filter_by(**kwargs).all()

    def delete(self, session):
        """Delete this book."""
        session.delete(self)
        session.commit()

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    join_date = Column(Date, default=date.today)

    borrow_records = relationship("BorrowRecord", back_populates="member", cascade="all, delete-orphan")

    # ========== PROPERTY METHODS ==========
    @validates('name')
    def validate_name(self, key, value):
        """Ensure name is not empty."""
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        return value.strip()

    @validates('email')
    def validate_email(self, key, value):
        """Ensure email has a valid format."""
        if not value or not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Invalid email format")
        return value.lower().strip()

    @property
    def active_borrows(self):
        """Get all books currently borrowed by this member."""
        return [record for record in self.borrow_records if record.return_date is None]

    # ========== ORM METHODS ==========
    @classmethod
    def create(cls, session, name, email):
        """Create a new member."""
        member = cls(name=name, email=email)
        session.add(member)
        session.commit()
        return member

    @classmethod
    def get_all(cls, session):
        """Get all members."""
        return session.query(cls).all()

    @classmethod
    def find_by_id(cls, session, member_id):
        """Find a member by ID."""
        return session.query(cls).get(member_id)

    @classmethod
    def find_by_attribute(cls, session, **kwargs):
        """Find members by attribute (e.g., name, email)."""
        return session.query(cls).filter_by(**kwargs).all()

    def delete(self, session):
        """Delete this member."""
        session.delete(self)
        session.commit()

    def __repr__(self):
        return f"<Member(id={self.id}, name='{self.name}', email='{self.email}')>"


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    borrow_date = Column(Date, default=date.today)
    return_date = Column(Date, nullable=True)

    book = relationship("Book", back_populates="borrow_records")
    member = relationship("Member", back_populates="borrow_records")

    # ========== PROPERTY METHODS (Constraints) ==========
    @validates('return_date')
    def validate_return_date(self, key, value):
        """Ensure return date is not before borrow date."""
        if value and self.borrow_date and value < self.borrow_date:
            raise ValueError("Return date cannot be before borrow date")
        return value

    @property
    def is_returned(self):
        """Check if the book has been returned."""
        return self.return_date is not None

    @property
    def days_borrowed(self):
        """Calculate days the book has been borrowed."""
        end_date = self.return_date if self.return_date else date.today()
        return (end_date - self.borrow_date).days

    # ========== ORM METHODS ==========
    @classmethod
    def create(cls, session, book_id, member_id):
        """Create a new borrow record."""
        record = cls(book_id=book_id, member_id=member_id)
        session.add(record)
        session.commit()
        return record

    @classmethod
    def get_all(cls, session):
        """Get all borrow records."""
        return session.query(cls).all()

    @classmethod
    def find_by_id(cls, session, record_id):
        """Find a borrow record by ID."""
        return session.query(cls).get(record_id)

    @classmethod
    def find_by_attribute(cls, session, **kwargs):
        """Find borrow records by attribute (e.g., book_id, member_id)."""
        return session.query(cls).filter_by(**kwargs).all()

    def delete(self, session):
        """Delete this borrow record."""
        session.delete(self)
        session.commit()

    def __repr__(self):
        return f"<BorrowRecord(id={self.id}, book_id={self.book_id}, member_id={self.member_id})>"