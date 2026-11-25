import subprocess
import sys

TASKS = {
    "1": ("Средняя 4. Страница с таблицей данных", "table_page.py",
          "http://127.0.0.1:5000"),
    "2": ("Средняя 6. FastAPI Hello", "api_hello.py",
          "http://127.0.0.1:8000"),
    "3": ("Средняя 10. REST API список задач", "todo_api.py",
          "http://127.0.0.1:5001/tasks"),
    "4": ("Повышенная 5. REST API для заметок", "notes_api.py",
          "http://127.0.0.1:8001/docs"),
    "5": ("Повышенная 9. Подключение SQLAlchemy", "storage.py", None),
}


def main():
    while True:
        print("\nЛабораторная №6, вариант 4. Задания:")
        for key, (title, _, _) in TASKS.items():
            print(f"  {key}. {title}")
        print("  0. Выход")
        choice = input("Номер задания: ").strip()
        if choice == "0":
            print("Пока!")
            return
        task = TASKS.get(choice)
        if task is None:
            print("Нет такого пункта, попробуйте ещё раз.")
            continue
        title, script, address = task
        print(f"--- {title} ---")
        if address:
            print(f"Адрес: {address} (остановить сервер — Ctrl+C)")
        try:
            subprocess.run([sys.executable, script], check=False)
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
