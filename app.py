import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-before-production")
database_url = os.environ.get("DATABASE_URL", "sqlite:///campus_to_career.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student or company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    company_name = db.Column(db.String(160), nullable=False)
    location = db.Column(db.String(120), default="India")
    job_type = db.Column(db.String(40), default="Full-time")
    description = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="Submitted")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    job = db.relationship("Job", backref="applications")
    student = db.relationship("User", backref="applications")

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("This page is not available for your account type.", "danger")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapped
    return decorator

@app.context_processor
def inject_user():
    return {"current_user_name": session.get("name"), "current_role": session.get("role")}

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    query = Job.query.order_by(Job.created_at.desc())
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Job.title.ilike(like), Job.company_name.ilike(like), Job.location.ilike(like)))
    return render_template("index.html", jobs=query.all(), search=search)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        if not name or not email or len(password) < 8 or role not in ("student", "company"):
            flash("Enter all details. Password must be at least 8 characters.", "danger")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")
        user = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Email or password is incorrect.", "danger")
            return render_template("login.html")
        session.clear()
        session.update({"user_id": user.id, "name": user.name, "role": user.role})
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    if session["role"] == "student":
        applications = Application.query.filter_by(student_id=user_id).order_by(Application.created_at.desc()).all()
        return render_template("student_dashboard.html", applications=applications)
    jobs = Job.query.filter_by(posted_by=user_id).order_by(Job.created_at.desc()).all()
    return render_template("company_dashboard.html", jobs=jobs)

@app.route("/jobs/new", methods=["GET", "POST"])
@role_required("company")
def new_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company_name = request.form.get("company_name", "").strip()
        location = request.form.get("location", "").strip() or "India"
        job_type = request.form.get("job_type", "Full-time")
        description = request.form.get("description", "").strip()
        if not all([title, company_name, description]):
            flash("Please fill in the job title, company name, and description.", "danger")
            return render_template("new_job.html")
        job = Job(title=title, company_name=company_name, location=location, job_type=job_type,
                  description=description, posted_by=session["user_id"])
        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully.", "success")
        return redirect(url_for("dashboard"))
    return render_template("new_job.html")

@app.route("/jobs/<int:job_id>/apply", methods=["POST"])
@role_required("student")
def apply_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        flash("That job could not be found.", "danger")
        return redirect(url_for("index"))
    existing = Application.query.filter_by(job_id=job_id, student_id=session["user_id"]).first()
    if existing:
        flash("You have already applied for this job.", "warning")
    else:
        application = Application(job_id=job_id, student_id=session["user_id"],
                                 message=request.form.get("message", "").strip())
        db.session.add(application)
        db.session.commit()
        flash("Your application was submitted successfully.", "success")
    return redirect(url_for("index"))

@app.route("/applications/<int:application_id>/status", methods=["POST"])
@role_required("company")
def update_application(application_id):
    application = db.session.get(Application, application_id)
    if not application or application.job.posted_by != session["user_id"]:
        flash("Application not found for your company account.", "danger")
        return redirect(url_for("dashboard"))
    status = request.form.get("status")
    if status in ("Submitted", "Under review", "Shortlisted", "Rejected"):
        application.status = status
        db.session.commit()
        flash("Application status updated.", "success")
    return redirect(url_for("dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
