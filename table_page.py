from flask import Flask, render_template, request

CITIES = [
    ("Тула", 1146, 456813),
    ("Новомосковск", 1765, 115938),
    ("Донской", 1773, 61740),
    ("Алексин", 1348, 58220),
    ("Щёкино", 1870, 52177),
    ("Узловая", 1873, 47558),
    ("Ефремов", 1637, 34965),
    ("Богородицк", 1663, 29133),
]
COLUMNS = {"name": ("Город", 0), "year": ("Основан", 1),
           "people": ("Население, чел.", 2)}

app = Flask(__name__)


def select_rows(rows, sort="name", desc=False, query=""):
    index = COLUMNS.get(sort, COLUMNS["name"])[1]
    found = [row for row in rows if query.lower() in row[0].lower()]
    return sorted(found, key=lambda row: row[index], reverse=desc)


def spaced(number):
    return f"{number:,}".replace(",", " ")


app.jinja_env.filters["spaced"] = spaced


@app.get("/")
def cities():
    sort = request.args.get("sort", "name")
    desc = request.args.get("desc") == "1"
    query = request.args.get("q", "").strip()
    rows = select_rows(CITIES, sort, desc, query)
    return render_template("cities.html", rows=rows, columns=COLUMNS,
                           sort=sort, desc=desc, query=query,
                           total=sum(row[2] for row in rows))


if __name__ == "__main__":
    app.run(port=5000, debug=True)
