from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ================= CONFIG =================
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dala_foods.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, staff, store

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ================= CREATE TABLES =================
with app.app_context():
    db.create_all()

# ================= ROUTES =================
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        username=session.get("username"),
        role=session.get("role")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= TEMP ADMIN CREATION =================
# USE ONCE THEN DELETE
@app.route("/create_admin")
def create_admin():
    admin = User.query.filter_by(username="admin").first()
    if admin:
        return "Admin already exists ✅"

    admin = User(
        username="admin",
        email="admin@dalafoods.com",
        role="admin"
    )
    admin.set_password("Admin12345")  # CHANGE AFTER LOGIN

    db.session.add(admin)
    db.session.commit()
    return "Admin created successfully ✅"

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
