import click
from database import SessionLocal
from models import Member

# Create a DB session
session = SessionLocal()

@click.group()
def cli():
    """Library Management System - Member Management"""
    pass

# ----- MEMBER COMMANDS -----
@cli.group()
def member():
    """Manage library members"""
    pass

@member.command("add")
@click.option("--name", prompt="Member Name")
@click.option("--email", prompt="Member Email")
def add_member(name, email):
    """Add a new member"""
    # Check if email already exists
    if session.query(Member).filter_by(email=email).first():
        click.echo("Error: Email already exists!")
        return

    new_member = Member(name=name, email=email)
    session.add(new_member)
    session.commit()
    click.echo(f"Member '{name}' added successfully with email '{email}'.")

@member.command("list")
def list_members():
    """List all members"""
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
    """Update an existing member"""
    member = session.query(Member).get(member_id)
    if not member:
        click.echo("Member not found!")
        return
    if name:
        member.name = name
    if email:
        # check for duplicate email
        if session.query(Member).filter(Member.email==email, Member.id != member_id).first():
            click.echo("Error: Email already exists!")
            return
        member.email = email
    session.commit()
    click.echo(f"Member ID {member_id} updated successfully.")

@member.command("delete")
@click.option("--member_id", type=int, prompt="Member ID to delete")
def delete_member(member_id):
    """Delete a member"""
    member = session.query(Member).get(member_id)
    if not member:
        click.echo("Member not found!")
        return
    session.delete(member)
    session.commit()
    click.echo(f"Member ID {member_id} deleted successfully.")

# Entry point
if __name__ == "__main__":
    cli()
