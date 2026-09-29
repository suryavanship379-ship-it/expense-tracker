from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "expenses.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            source TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def format_date(date_string):
    try:
        parts = date_string.split("-")

        if len(parts) == 3:
            year = int(parts[0])

            # Fix dates like 0026-09-19
            if year < 2000:
                year += 2000

            date_string = f"{year:04d}-{parts[1]}-{parts[2]}"

            date_obj = datetime.strptime(
                date_string,
                "%Y-%m-%d"
            )

            return date_obj.strftime("%d %b %Y")

    except Exception:
        pass

    return date_string


@app.route("/")
def home():

    conn = get_db()

    # Get expenses
    expenses = conn.execute("""
        SELECT * FROM expenses
        ORDER BY date DESC, id DESC
    """).fetchall()

    # Get income
    incomes = conn.execute("""
        SELECT * FROM income
        ORDER BY date DESC, id DESC
    """).fetchall()

    # Total income
    total_income = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM income
    """).fetchone()[0]

    # Total expenses
    total_expenses = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """).fetchone()[0]

    # Current month expenses
    current_month = datetime.now().strftime("%Y-%m")

    monthly_expense = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(date, 1, 7) = ?
    """, (current_month,)).fetchone()[0]

    # Monthly history (last 6 months)
    monthly_history = []
    today = datetime.now()

    for i in range(5, -1, -1):
        month_number = today.month - i
        year = today.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        month_key = f"{year}-{month_number:02d}"

        month_name = datetime(
            year,
            month_number,
            1
        ).strftime("%b")

        amount = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE substr(date, 1, 7) = ?
        """, (month_key,)).fetchone()[0]

        monthly_history.append({
            "name": month_name,
            "year": year,
            "amount": float(amount)
        })

    # Aggregated Categories
    db_categories = conn.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
    """).fetchall()

    cat_map = {row["category"]: float(row["total"]) for row in db_categories}

    standard_categories = [
        "Food",
        "Shopping",
        "Travel",
        "Education",
        "Bills/Utilities",
        "Entertainment",
        "Health",
        "Other"
    ]

    categories_list = []
    for cat_name in standard_categories:
        val = 0.0
        if cat_name in cat_map:
            val += cat_map[cat_name]
        elif cat_name == "Bills/Utilities" and "Bills" in cat_map:
            val += cat_map["Bills"]
        categories_list.append({
            "category": cat_name,
            "total": val
        })

    # Include any custom categories stored in DB
    for cat_name, total_val in cat_map.items():
        if cat_name not in standard_categories and cat_name != "Bills":
            categories_list.append({
                "category": cat_name,
                "total": total_val
            })

    # Combine income and expenses into unified transactions list
    transactions = []

    for expense in expenses:
        transactions.append({
            "id": expense["id"],
            "date": expense["date"],
            "display_date": format_date(expense["date"]),
            "type": "Expense",
            "title": expense["title"],
            "category": expense["category"],
            "amount": -float(expense["amount"]),
            "raw_amount": float(expense["amount"])
        })

    for income in incomes:
        transactions.append({
            "id": income["id"],
            "date": income["date"],
            "display_date": format_date(income["date"]),
            "type": "Income",
            "title": income["title"],
            "category": income["source"],
            "amount": float(income["amount"]),
            "raw_amount": float(income["amount"])
        })

    # Sort transactions by date descending
    transactions.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    conn.close()

    # Calculate balance
    balance = float(total_income) - float(total_expenses)

    return render_template(
        "index.html",
        total_income=float(total_income),
        total_expenses=float(total_expenses),
        balance=float(balance),
        monthly_expense=float(monthly_expense),
        monthly_history=monthly_history,
        categories=categories_list,
        transactions=transactions,
        recent_transactions=transactions[:5]
    )


@app.route("/add-expense", methods=["POST"])
def add_expense():

    title = request.form["title"]
    amount = request.form["amount"]
    category = request.form["category"]
    date = request.form["date"]

    conn = get_db()

    conn.execute("""
        INSERT INTO expenses
        (title, amount, category, date)
        VALUES (?, ?, ?, ?)
    """, (
        title,
        amount,
        category,
        date
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/add-income", methods=["POST"])
def add_income():

    title = request.form["title"]
    amount = request.form["amount"]
    source = request.form["source"]
    date = request.form["date"]

    conn = get_db()

    conn.execute("""
        INSERT INTO income
        (title, amount, source, date)
        VALUES (?, ?, ?, ?)
    """, (
        title,
        amount,
        source,
        date
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/delete-expense/<int:id>")
def delete_expense(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM expenses WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/delete-income/<int:id>")
def delete_income(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM income WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )