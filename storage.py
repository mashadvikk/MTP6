from datetime import datetime

from sqlalchemy import Column, ForeignKey, Table, create_engine, or_, select
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            relationship)
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


note_tags = Table(
    "note_tags", Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    text: Mapped[str] = mapped_column(default="")
    created: Mapped[datetime] = mapped_column(default=datetime.now)
    changed: Mapped[datetime] = mapped_column(default=datetime.now,
                                              onupdate=datetime.now)
    tags: Mapped[list[Tag]] = relationship(secondary=note_tags,
                                           order_by=Tag.name)


class NotFound(Exception):
    pass


class NoteStorage:
    def __init__(self, url="sqlite:///notes.db"):
        options = {}
        if url == "sqlite://":
            options = {"poolclass": StaticPool,
                       "connect_args": {"check_same_thread": False}}
        self.engine = create_engine(url, **options)
        Base.metadata.create_all(self.engine)

    def session(self):
        return Session(self.engine, expire_on_commit=False)

    def find(self, query="", tag=None):
        request = select(Note).order_by(Note.id)
        if query:
            request = request.where(or_(
                Note.title.contains(query, autoescape=True),
                Note.text.contains(query, autoescape=True)))
        if tag:
            request = request.where(Note.tags.any(Tag.name == tag.lower()))
        with self.session() as session:
            return [view(note) for note in session.scalars(request)]

    def get(self, note_id):
        with self.session() as session:
            return view(load(session, note_id))

    def add(self, title, text="", tags=()):
        with self.session() as session:
            note = Note(title=title, text=text, tags=use_tags(session, tags))
            session.add(note)
            session.commit()
            return view(note)

    def change(self, note_id, title=None, text=None, tags=None):
        with self.session() as session:
            note = load(session, note_id)
            if title is not None:
                note.title = title
            if text is not None:
                note.text = text
            if tags is not None:
                note.tags = use_tags(session, tags)
            session.commit()
            session.refresh(note)
            return view(note)

    def remove(self, note_id):
        with self.session() as session:
            session.delete(load(session, note_id))
            session.commit()


def load(session, note_id):
    note = session.get(Note, note_id)
    if note is None:
        raise NotFound(note_id)
    return note


def use_tags(session, names):
    result = []
    for name in sorted({name.strip().lower() for name in names} - {""}):
        tag = session.scalar(select(Tag).where(Tag.name == name))
        result.append(tag or Tag(name=name))
    return result


def view(note):
    return {"id": note.id, "title": note.title, "text": note.text,
            "tags": [tag.name for tag in note.tags],
            "created": note.created, "changed": note.changed}


if __name__ == "__main__":
    storage = NoteStorage("sqlite://")
    storage.add("Лабораторная 6", "Flask, FastAPI, SQLAlchemy", ["учёба"])
    storage.add("Покупки", "молоко, хлеб", ["дом", "магазин"])
    storage.change(2, text="молоко, хлеб, сыр")
    print("Таблицы:", ", ".join(sorted(Base.metadata.tables)))
    for item in storage.find():
        print(item["id"], item["title"], "|", item["text"], "|", item["tags"])
    print("По тегу «дом»:",
          [item["title"] for item in storage.find(tag="дом")])
