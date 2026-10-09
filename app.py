import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sahyog_secret_change_me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sahyog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# -------------------
# Database Models
# -------------------
class User(db.Model):
    """One table for all roles: parent, elder, admin."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # parent / elder / admin
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=False)
    # Healthcare info (mainly for elders; stored for emergencies)
    health_info = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    health_info = db.Column(db.Text)  # allergies, medication, conditions
    parent = db.relationship("User", backref="children")


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    elder_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(30))  # game / reading / exercise / other
    date = db.Column(db.String(10), nullable=False)   # YYYY-MM-DD
    time = db.Column(db.String(5), nullable=False)    # HH:MM
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, default=5)
    elder = db.relationship("User", backref="activities")


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey("child.id"), nullable=False)
    checked_in_at = db.Column(db.DateTime)
    checked_out_at = db.Column(db.DateTime)
    activity = db.relationship("Activity", backref="bookings")
    child = db.relationship("Child", backref="bookings")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


def notify(user_id, message):
    db.session.add(Notification(user_id=user_id, message=message))


# -------------------
# Helpers
# -------------------
def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and user.role != role:
                flash("You are not allowed to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# -------------------
# Public routes
# -------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role")
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if role not in ("parent", "elder"):
            flash("Invalid role.", "danger")
            return redirect(url_for("register"))
        if not name or not email or len(password) < 6:
            flash("Fill all fields (password min 6 characters).", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(
            name=name, email=email, role=role,
            password_hash=generate_password_hash(password),
            phone=request.form.get("phone"),
            address=request.form.get("address"),
            health_info=request.form.get("health_info"),
            emergency_contact=request.form.get("emergency_contact"),
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered! Your profile will be verified by an admin. You can log in now.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))


# -------------------
# Dashboard (role-based)
# -------------------
@app.route("/dashboard")
@login_required()
def dashboard():
    user = current_user()
    ctx = {"user": user, "role": user.role}
    ctx["notifications"] = (Notification.query.filter_by(user_id=user.id)
                            .order_by(Notification.created_at.desc()).limit(10).all())

    if user.role == "parent":
        ctx["children"] = user.children
        ctx["activities"] = (Activity.query.join(User, Activity.elder_id == User.id)
                             .filter(User.verified.is_(True))
                             .order_by(Activity.date, Activity.time).all())
        child_ids = [c.id for c in user.children]
        ctx["bookings"] = (Booking.query.filter(Booking.child_id.in_(child_ids)).all()
                           if child_ids else [])
    elif user.role == "elder":
        ctx["my_activities"] = (Activity.query.filter_by(elder_id=user.id)
                                .order_by(Activity.date, Activity.time).all())
    elif user.role == "admin":
        ctx["pending"] = User.query.filter(User.role != "admin", User.verified.is_(False)).all()
        ctx["users"] = User.query.filter(User.role != "admin").all()
        ctx["all_bookings"] = Booking.query.order_by(Booking.id.desc()).limit(30).all()
        ctx["stats"] = {
            "parents": User.query.filter_by(role="parent").count(),
            "elders": User.query.filter_by(role="elder").count(),
            "activities": Activity.query.count(),
            "bookings": Booking.query.count(),
        }
    # Each role has its own dashboard template
    return render_template(f"{user.role}_dashboard.html", **ctx)


# -------------------
# Parent actions
# -------------------
@app.route("/child/add", methods=["POST"])
@login_required("parent")
def add_child():
    user = current_user()
    name = request.form.get("name", "").strip()
    if not name:
        flash("Child name is required.", "danger")
        return redirect(url_for("dashboard"))
    age = request.form.get("age", type=int)
    db.session.add(Child(parent_id=user.id, name=name, age=age,
                         health_info=request.form.get("health_info")))
    db.session.commit()
    flash("Child added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/activity/<int:activity_id>/book", methods=["POST"])
@login_required("parent")
def book_activity(activity_id):
    user = current_user()
    activity = db.get_or_404(Activity, activity_id)
    child = db.session.get(Child, request.form.get("child_id", type=int))
    if not child or child.parent_id != user.id:
        flash("Choose one of your children.", "danger")
        return redirect(url_for("dashboard"))
    if len(activity.bookings) >= (activity.capacity or 0):
        flash("This activity is full.", "warning")
        return redirect(url_for("dashboard"))
    if Booking.query.filter_by(activity_id=activity.id, child_id=child.id).first():
        flash("Already booked.", "info")
        return redirect(url_for("dashboard"))
    db.session.add(Booking(activity_id=activity.id, child_id=child.id))
    notify(activity.elder_id, f"{child.name} was booked for '{activity.title}'.")
    db.session.commit()
    flash(f"{child.name} booked for {activity.title}.", "success")
    return redirect(url_for("dashboard"))


# -------------------
# Elder actions
# -------------------
@app.route("/activity/add", methods=["POST"])
@login_required("elder")
def add_activity():
    user = current_user()
    if not user.verified:
        flash("Your profile must be verified by an admin before scheduling.", "warning")
        return redirect(url_for("dashboard"))
    title = request.form.get("title", "").strip()
    date = request.form.get("date")
    time = request.form.get("time")
    if not (title and date and time):
        flash("Title, date and time are required.", "danger")
        return redirect(url_for("dashboard"))
    db.session.add(Activity(
        elder_id=user.id, title=title, date=date, time=time,
        category=request.form.get("category"),
        description=request.form.get("description"),
        capacity=request.form.get("capacity", type=int) or 5,
    ))
    db.session.commit()
    flash("Activity scheduled.", "success")
    return redirect(url_for("dashboard"))


@app.route("/booking/<int:booking_id>/<action>", methods=["POST"])
@login_required("elder")
def attendance(booking_id, action):
    user = current_user()
    booking = db.get_or_404(Booking, booking_id)
    if booking.activity.elder_id != user.id or action not in ("checkin", "checkout"):
        flash("Not allowed.", "danger")
        return redirect(url_for("dashboard"))

    child = booking.child
    if action == "checkin" and not booking.checked_in_at:
        booking.checked_in_at = datetime.now()
        notify(child.parent_id, f"{child.name} checked IN to '{booking.activity.title}' "
                                f"at {booking.checked_in_at:%H:%M}.")
    elif action == "checkout" and booking.checked_in_at and not booking.checked_out_at:
        booking.checked_out_at = datetime.now()
        notify(child.parent_id, f"{child.name} checked OUT of '{booking.activity.title}' "
                                f"at {booking.checked_out_at:%H:%M}.")
    else:
        flash("Invalid state for that action.", "warning")
        return redirect(url_for("dashboard"))
    db.session.commit()
    flash(f"{child.name}: {action} recorded, parent notified.", "success")
    return redirect(url_for("dashboard"))


# -------------------
# Admin actions
# -------------------
@app.route("/admin/verify/<int:user_id>", methods=["POST"])
@login_required("admin")
def verify_user(user_id):
    target = db.get_or_404(User, user_id)
    target.verified = True
    notify(target.id, "Your profile has been verified. Welcome to Sahyog Setu!")
    db.session.commit()
    flash(f"{target.name} verified.", "success")
    return redirect(url_for("dashboard"))


# -------------------
# Setup
# -------------------
def init_db():
    with app.app_context():
        db.create_all()
        # Pre-create one admin for demo (log in with email admin@sahyog.local)
        if not User.query.filter_by(email="admin@sahyog.local").first():
            db.session.add(User(
                name="Admin", email="admin@sahyog.local", role="admin", verified=True,
                password_hash=generate_password_hash("admin123"),
            ))
            db.session.commit()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
