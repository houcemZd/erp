import os
import re
from datetime import datetime
from functools import wraps
from secrets import token_hex

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)


def get_secret_key() -> str:
    configured = os.getenv("SECRET_KEY")
    if configured:
        return configured

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    if debug_mode:
        return token_hex(32)

    raise RuntimeError("SECRET_KEY must be set in production.")


app.config["SECRET_KEY"] = get_secret_key()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///sibec.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ALLOWED_REF = re.compile(r"^[A-Za-z0-9_-]{1,50}$")


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active_user = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user


class Stock(db.Model):
    __tablename__ = "stock"

    ref = db.Column(db.String(50), primary_key=True)
    qty = db.Column(db.Integer, nullable=False, default=0)


class Movement(db.Model):
    __tablename__ = "movement"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ref = db.Column(db.String(50), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    actor = db.relationship("User", lazy=True)


class Production(db.Model):
    __tablename__ = "production"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ref = db.Column(db.String(50), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    actor = db.relationship("User", lazy=True)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    actor = db.relationship("User", lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role != "admin":
            flash("Accès refusé : rôle admin requis.", "error")
            return redirect(url_for("home"))
        return view_func(*args, **kwargs)

    return wrapped


def validate_ref(ref: str) -> str:
    cleaned = ref.strip().upper()
    if not ALLOWED_REF.fullmatch(cleaned):
        raise ValueError("Référence invalide (A-Z, 0-9, _, - ; max 50 caractères).")
    return cleaned


def validate_qty(raw: str) -> int:
    try:
        qty = int(raw)
    except (TypeError, ValueError):
        raise ValueError("Quantité invalide.")
    if qty <= 0:
        raise ValueError("La quantité doit être strictement positive.")
    return qty


def write_audit(action: str, details: str, actor_id: int | None = None) -> None:
    """Add an audit entry to current DB session; caller commits transaction."""
    db.session.add(AuditLog(action=action, details=details, actor_id=actor_id))


def bootstrap_admin() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "admin")

    existing = User.query.filter_by(username=admin_username).first()
    if existing:
        return

    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD must be set to bootstrap the initial admin user.")

    admin = User(username=admin_username, role="admin")
    admin.set_password(admin_password)
    db.session.add(admin)
    write_audit("bootstrap_admin", f"Initial admin created: {admin_username}")
    db.session.commit()


with app.app_context():
    db.create_all()
    bootstrap_admin()


@app.route("/healthz")
def healthz():
    try:
        db.session.execute(db.select(func.count(User.id))).scalar()
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200
    except Exception as exc:  # pragma: no cover
        app.logger.exception("healthz failure: %s", exc)
        return jsonify({"status": "error", "message": "database unavailable"}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Identifiants invalides.", "error")
            return render_template("login.html")

        if not user.is_active_user:
            flash("Compte désactivé.", "error")
            return render_template("login.html")

        login_user(user)
        write_audit("login", "Connexion utilisateur", user.id)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    write_audit("logout", "Déconnexion utilisateur", current_user.id)
    db.session.commit()
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template("dashboard.html")


@app.route("/stock")
@login_required
def stock():
    data = Stock.query.order_by(Stock.ref.asc()).all()
    return render_template("stock.html", data=data)


@app.route("/movement", methods=["GET", "POST"])
@login_required
@admin_required
def movement():
    if request.method == "POST":
        typ = request.form.get("type", "")

        if typ not in {"ENTREE", "SORTIE"}:
            flash("Type de mouvement invalide.", "error")
            return redirect(url_for("movement"))

        try:
            ref = validate_ref(request.form.get("ref", ""))
            qty = validate_qty(request.form.get("qty", ""))
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("movement"))

        stock_item = db.session.get(Stock, ref)
        if stock_item is None:
            stock_item = Stock(ref=ref, qty=0)
            db.session.add(stock_item)

        if typ == "SORTIE" and stock_item.qty < qty:
            flash("Stock insuffisant : sortie refusée.", "error")
            return redirect(url_for("movement"))

        stock_item.qty = stock_item.qty + qty if typ == "ENTREE" else stock_item.qty - qty

        db.session.add(Movement(ref=ref, qty=qty, type=typ, actor_id=current_user.id))
        write_audit("movement", f"{typ} {qty} sur {ref}", current_user.id)
        db.session.commit()

        flash("Mouvement enregistré.", "success")
        return redirect(url_for("movement"))

    return render_template("movement.html")


@app.route("/production", methods=["GET", "POST"])
@login_required
@admin_required
def production():
    if request.method == "POST":
        try:
            ref = validate_ref(request.form.get("ref", ""))
            qty = validate_qty(request.form.get("qty", ""))
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("production"))

        stock_item = db.session.get(Stock, ref)
        if stock_item is None:
            stock_item = Stock(ref=ref, qty=0)
            db.session.add(stock_item)

        stock_item.qty += qty
        db.session.add(Production(ref=ref, qty=qty, actor_id=current_user.id))
        write_audit("production", f"Production {qty} sur {ref}", current_user.id)
        db.session.commit()

        flash("Production enregistrée.", "success")
        return redirect(url_for("production"))

    return render_template("production.html")


@app.route("/history")
@login_required
def history():
    mov = Movement.query.order_by(Movement.date.desc()).limit(200).all()
    prod = Production.query.order_by(Production.date.desc()).limit(200).all()
    audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()

    return render_template("history.html", mov=mov, prod=prod, audits=audits)


@app.route("/kpi")
@login_required
def kpi():
    stock_count = db.session.execute(db.select(func.count(Stock.ref))).scalar_one()
    movement_count = db.session.execute(db.select(func.count(Movement.id))).scalar_one()
    production_count = db.session.execute(db.select(func.count(Production.id))).scalar_one()
    user_count = db.session.execute(db.select(func.count(User.id))).scalar_one()

    return render_template(
        "kpi.html",
        stock_count=stock_count,
        movement_count=movement_count,
        production_count=production_count,
        user_count=user_count,
    )


@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def admin_users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if not username or len(username) > 80:
            flash("Nom d'utilisateur invalide.", "error")
            return redirect(url_for("admin_users"))

        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "error")
            return redirect(url_for("admin_users"))

        if role not in {"admin", "user"}:
            flash("Rôle invalide.", "error")
            return redirect(url_for("admin_users"))

        if User.query.filter_by(username=username).first():
            flash("Utilisateur déjà existant.", "error")
            return redirect(url_for("admin_users"))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        write_audit("create_user", f"Nouvel utilisateur: {username} ({role})", current_user.id)
        db.session.commit()
        flash("Utilisateur créé.", "success")
        return redirect(url_for("admin_users"))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def admin_toggle_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Utilisateur introuvable.", "error")
        return redirect(url_for("admin_users"))

    if user.id == current_user.id:
        flash("Vous ne pouvez pas désactiver votre propre compte.", "error")
        return redirect(url_for("admin_users"))

    user.is_active_user = not user.is_active_user
    write_audit(
        "toggle_user",
        f"Utilisateur {user.username} actif={user.is_active_user}",
        current_user.id,
    )
    db.session.commit()

    flash("Statut utilisateur mis à jour.", "success")
    return redirect(url_for("admin_users"))


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=debug_mode)
