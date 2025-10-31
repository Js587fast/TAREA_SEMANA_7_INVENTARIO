from functools import wraps
from flask import session, redirect, url_for, flash

def require_roles(*roles_permitidos):
    roles_permitidos = {r.lower() for r in roles_permitidos}

    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            rol = (session.get('rol') or '').lower()
            if rol not in roles_permitidos:
                flash("No tienes permisos para esta acción.", "warning")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return wrapper
