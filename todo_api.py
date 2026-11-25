from flask import Flask, jsonify, request


class TodoList:
    def __init__(self):
        self.items = {}
        self.last_id = 0

    def add(self, title):
        self.last_id += 1
        self.items[self.last_id] = {"id": self.last_id, "title": title,
                                    "done": False}
        return self.items[self.last_id]

    def all(self, done=None):
        return [item for item in self.items.values()
                if done is None or item["done"] == done]


def check(data, partial=False):
    if not isinstance(data, dict):
        return "Ожидается JSON-объект"
    if not partial and "title" not in data:
        return "Не указано поле title"
    if "title" in data and not (isinstance(data["title"], str)
                                and data["title"].strip()):
        return "Поле title должно быть непустой строкой"
    if "done" in data and not isinstance(data["done"], bool):
        return "Поле done должно быть true или false"
    return None


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    todo = TodoList()

    def error(message, code):
        return jsonify(error=message), code

    @app.get("/tasks")
    def get_tasks():
        done = {"1": True, "0": False}.get(request.args.get("done"))
        return jsonify(todo.all(done))

    @app.post("/tasks")
    def add_task():
        data = request.get_json(silent=True)
        message = check(data)
        if message:
            return error(message, 400)
        item = todo.add(data["title"].strip())
        return jsonify(item), 201, {"Location": f"/tasks/{item['id']}"}

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        if task_id not in todo.items:
            return error("Задача не найдена", 404)
        return jsonify(todo.items[task_id])

    @app.patch("/tasks/<int:task_id>")
    def change_task(task_id):
        if task_id not in todo.items:
            return error("Задача не найдена", 404)
        data = request.get_json(silent=True)
        message = check(data, partial=True)
        if message:
            return error(message, 400)
        item = todo.items[task_id]
        item.update({key: data[key] for key in ("title", "done")
                     if key in data})
        return jsonify(item)

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        if todo.items.pop(task_id, None) is None:
            return error("Задача не найдена", 404)
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(port=5001, debug=True)
