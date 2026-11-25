from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from storage import NotFound, NoteStorage


class NewNote(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    text: str = ""
    tags: list[str] = []


class NoteChanges(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    text: str | None = None
    tags: list[str] | None = None


class NoteView(BaseModel):
    id: int
    title: str
    text: str
    tags: list[str]
    created: datetime
    changed: datetime


def create_app(storage):
    app = FastAPI(title="Заметки")

    @app.exception_handler(NotFound)
    def not_found(request: Request, exc: NotFound):
        return JSONResponse({"detail": f"Заметки {exc} нет"}, 404)

    @app.get("/notes", response_model=list[NoteView])
    def find_notes(q: str = "", tag: str | None = None):
        return storage.find(q, tag)

    @app.post("/notes", response_model=NoteView,
              status_code=status.HTTP_201_CREATED)
    def add_note(note: NewNote):
        return storage.add(note.title, note.text, note.tags)

    @app.get("/notes/{note_id}", response_model=NoteView)
    def get_note(note_id: int):
        return storage.get(note_id)

    @app.patch("/notes/{note_id}", response_model=NoteView)
    def change_note(note_id: int, changes: NoteChanges):
        return storage.change(note_id, **changes.model_dump())

    @app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remove_note(note_id: int):
        storage.remove(note_id)

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(NoteStorage()), port=8001)
