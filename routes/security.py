from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para acceder.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("rol") != "administrador":
            flash("Acceso restringido: Solo Administrador.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper
