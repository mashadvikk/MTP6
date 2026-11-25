import pytest
from fastapi.testclient import TestClient

import api_hello
import notes_api
import table_page
import todo_api
from storage import NotFound, NoteStorage


def test_rows_sorting_and_search():
    rows = table_page.select_rows(table_page.CITIES, "people", desc=True)
    assert [row[0] for row in rows[:2]] == ["Тула", "Новомосковск"]
    rows = table_page.select_rows(table_page.CITIES, query="ОВА")
    assert [row[0] for row in rows] == ["Узловая"]


def test_unknown_column_sorts_by_name():
    rows = table_page.select_rows(table_page.CITIES, "wrong")
    assert rows[0][0] == "Алексин"


def test_table_page():
    page = table_page.app.test_client().get("/?sort=year").text
    assert page.index("Тула</td>") < page.index("Алексин</td>")
    assert "456 813" in page and "▲" in page


def test_table_page_empty_search():
    page = table_page.app.test_client().get("/?q=Москва").text
    assert "Ничего не найдено" in page


def test_fastapi_hello():
    client = TestClient(api_hello.app)
    assert client.get("/").json() == {"hello": "FastAPI"}
    assert len(client.get("/time").json()["time"]) == 8


@pytest.fixture
def todo():
    return todo_api.create_app().test_client()


def test_todo_lifecycle(todo):
    created = todo.post("/tasks", json={"title": " Сдать ЛР6 "})
    assert created.status_code == 201
    assert created.headers["Location"] == "/tasks/1"
    assert created.json == {"id": 1, "title": "Сдать ЛР6", "done": False}
    todo.post("/tasks", json={"title": "Отдохнуть"})
    assert todo.patch("/tasks/1", json={"done": True}).json["done"] is True
    assert [t["id"] for t in todo.get("/tasks?done=0").json] == [2]
    assert todo.delete("/tasks/1").status_code == 204
    assert todo.get("/tasks/1").status_code == 404


def test_todo_ids_are_not_reused(todo):
    todo.post("/tasks", json={"title": "а"})
    todo.delete("/tasks/1")
    assert todo.post("/tasks", json={"title": "б"}).json["id"] == 2


@pytest.mark.parametrize("body", [{}, {"title": "  "}, {"title": 5}, []])
def test_todo_bad_request(todo, body):
    assert todo.post("/tasks", json=body).status_code == 400


def test_todo_bad_patch(todo):
    todo.post("/tasks", json={"title": "а"})
    assert todo.patch("/tasks/1", json={"done": "да"}).status_code == 400
    assert todo.get("/tasks/1").json["done"] is False


@pytest.fixture
def storage():
    storage = NoteStorage("sqlite://")
    yield storage
    storage.engine.dispose()


def test_storage_shares_tags(storage):
    storage.add("Первая", tags=["Учёба", "учёба ", ""])
    storage.add("Вторая", tags=["учёба", "дом"])
    assert storage.get(2)["tags"] == ["дом", "учёба"]
    assert len(storage.find(tag="Учёба")) == 2


def test_storage_search_and_changes(storage):
    note = storage.add("Покупки", "молоко")
    changed = storage.change(note["id"], text="100% сок", tags=["дом"])
    assert changed["title"] == "Покупки"
    assert changed["changed"] > note["changed"]
    assert len(storage.find("100%")) == 1
    assert storage.find("молоко") == []


def test_storage_not_found(storage):
    with pytest.raises(NotFound):
        storage.get(1)


@pytest.fixture
def notes(storage):
    return TestClient(notes_api.create_app(storage))


def test_notes_api_lifecycle(notes):
    created = notes.post("/notes", json={"title": "План", "tags": ["дом"]})
    assert created.status_code == 201
    url = f"/notes/{created.json()['id']}"
    assert notes.get(url).json() == created.json()
    assert notes.patch(url, json={"text": "уборка"}).json()["tags"] == ["дом"]
    assert len(notes.get("/notes", params={"q": "уборка"}).json()) == 1
    assert notes.delete(url).status_code == 204
    assert notes.get(url).status_code == 404


@pytest.mark.parametrize("body", [{}, {"title": ""}, {"title": "я" * 101},
                                  {"title": "а", "tags": "дом"}])
def test_notes_api_validation(notes, body):
    assert notes.post("/notes", json=body).status_code == 422


@pytest.mark.parametrize("method", ["get", "delete"])
def test_notes_api_not_found(notes, method):
    response = getattr(notes, method)("/notes/7")
    assert response.status_code == 404
    assert response.json() == {"detail": "Заметки 7 нет"}
