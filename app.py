from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dala_foods_secret_key")

DB_NAME = "dala_foods.db"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT email, role FROM staff WHERE email=? AND password=?",
            (email, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["email"] = user["email"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid login details")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # Production chart
    cursor.execute(
        "SELECT product_name, SUM(quantity) as total FROM production GROUP BY product_name"
    )
    production = cursor.fetchall()
    prod_labels = [row["product_name"] for row in production]
    prod_values = [row["total"] for row in production]

    # Store inventory
    cursor.execute("SELECT item_name, quantity FROM store")
    store = cursor.fetchall()
    store_labels = [row["item_name"] for row in store]
    store_values = [row["quantity"] for row in store]

    # Low stock alert (≤ 10)
    low_stock = [
        f"{row['item_name']} ({row['quantity']})"
        for row in store if row["quantity"] <= 10
    ]

    conn.close()

    return render_template(
        "dashboard.html",
        email=session["email"],
        role=session["role"],
        prod_labels=prod_labels,
        prod_values=prod_values,
        store_labels=store_labels,
        store_values=store_values,
        low_stock=low_stock
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- STORE ----------------
@app.route("/store", methods=["GET", "POST"])
def store():
    if "role" not in session or session["role"] not in ["Admin", "Storekeeper"]:
        return "Access denied"

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        item_name = request.form["item_name"]
        quantity = float(request.form["quantity"])
        unit = request.form["unit"]

        cursor.execute(
            "INSERT INTO store (item_name, quantity, unit, date_added) VALUES (?, ?, ?, date('now'))",
            (item_name, quantity, unit)
        )
        conn.commit()

    cursor.execute("SELECT * FROM store ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()

    return render_template("store.html", items=items)

# ---------------- PRODUCTION ----------------
@app.route("/production", methods=["GET", "POST"])
def production():
    if "role" not in session or session["role"] not in ["Admin", "Staff"]:
        return "Access denied"

    conn = get_db()
    cursor = conn.cursor()
    message = ""

    if request.method == "POST":
        product_name = request.form["product_name"]
        quantity = float(request.form["quantity"])
        unit = request.form["unit"]
        produced_by = session["email"]

        # Check store availability
        cursor.execute(
            "SELECT id, quantity FROM store WHERE item_name=? AND unit=?",
            (product_name, unit)
        )
        item = cursor.fetchone()

        if not item:
            message = "Item not found in store"
        elif item["quantity"] < quantity:
            message = f"Insufficient stock. Available: {item['quantity']} {unit}"
        else:
            new_qty = item["quantity"] - quantity

            cursor.execute(
                "UPDATE store SET quantity=? WHERE id=?",
                (new_qty, item["id"])
            )
            cursor.execute(
                "INSERT INTO production (product_name, quantity, unit, produced_by, date_produced) "
                "VALUES (?, ?, ?, ?, date('now'))",
                (product_name, quantity, unit, produced_by)
            )
            conn.commit()
            message = "Production recorded successfully"

    cursor.execute("SELECT * FROM production ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()

    return render_template("production.html", records=records, message=message)

# ---------------- ADMIN: STAFF ----------------
@app.route("/admin/staff", methods=["GET", "POST"])
def manage_staff():
    if "role" not in session or session["role"] != "Admin":
        return "Access denied"

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form["action"]
        email = request.form["email"]

        if action == "Add":
            password = request.form["password"]
            role = request.form["role"]
            cursor.execute(
                "INSERT INTO staff (email, password, role) VALUES (?, ?, ?)",
                (email, password, role)
            )
        elif action == "Delete":
            cursor.execute("DELETE FROM staff WHERE email=?", (email,))

        conn.commit()

    cursor.execute("SELECT * FROM staff")
    staff_list = cursor.fetchall()
    conn.close()

    return render_template("admin_staff.html", staff_list=staff_list)

# ---------------- EXPORT PRODUCTION ----------------
@app.route("/admin/export_production")
def export_production():
    if "role" not in session or session["role"] != "Admin":
        return "Access denied"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM production")
    rows = cursor.fetchall()
    conn.close()

    def generate_csv():
        yield "ID,Product,Quantity,Unit,Produced By,Date\n"
        for r in rows:
            yield f"{r['id']},{r['product_name']},{r['quantity']},{r['unit']},{r['produced_by']},{r['date_produced']}\n"

    return Response(
        generate_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=production_report.csv"}
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run()
