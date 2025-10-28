# inventario_pymes/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from urllib.parse import urlparse, urljoin
from sqlalchemy import or_
from models import Usuario
from extensions import db

# Todas las rutas bajo /auth
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# --------------------------------
# Observaciones: validar URL "next" segura
# --------------------------------
def _is_safe_url(target: str) -> bool:
    """Evita open-redirects. Permite solo URLs relativas o del mismo host."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')) and (ref_url.netloc == test_url.netloc)


# --------------------------------
# Login
# --------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pantalla de login de usuarios"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and usuario.check_password(password):
            session.clear()
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['rol'] = (usuario.rol or 'usuario').lower()
            session.permanent = True

            flash("Login exitoso.", "success")

            next_url = request.args.get('next') or request.form.get('next')
            if next_url and _is_safe_url(next_url):
                return redirect(next_url)

            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    # Plantillas se encuentran ubicadas directamente en /templates
    return render_template('login.html')


# --------------------------------
# Logout
# --------------------------------
@auth_bp.route('/logout')
def logout():
    """Cerrar sesión manualmente o por inactividad"""
    session.clear()
    flash("Tu sesión ha finalizado.", "warning")
    return redirect(url_for('auth.login'))


# --------------------------------
# Registro (rol fijo = 'usuario')
# --------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro de nuevos usuarios.
    - Asigna siempre rol 'usuario'
    - email es opcional (si se envía, se valida duplicado)
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Usuario y contraseña son obligatorios.", "warning")
            return redirect(url_for('auth.register'))

        
        filtros = [Usuario.username == username]
        if email:
            filtros.append(Usuario.email == email)

        existente = Usuario.query.filter(or_(*filtros)).first()
        if existente:
            if existente.username == username:
                flash("El nombre de usuario ya está en uso.", "warning")
            else:
                flash("El correo ya está registrado.", "warning")
            return redirect(url_for('auth.register'))

        # Crear usuario con rol fijo 'usuario'
        nuevo = Usuario(
            username=username,
            email=email if email else None,
            rol='usuario'
        )
        nuevo.set_password(password)

        try:
            db.session.add(nuevo)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Ocurrió un error al crear el usuario. Intenta nuevamente.", "danger")
            return redirect(url_for('auth.register'))

        # Auto-login tras registro
        session.clear()
        session['user_id'] = nuevo.id
        session['username'] = nuevo.username
        session['rol'] = 'usuario'
        session.permanent = True

        flash("Registro exitoso. ¡Bienvenido!", "success")

        next_url = request.args.get('next') or request.form.get('next')
        if next_url and _is_safe_url(next_url):
            return redirect(next_url)

        return redirect(url_for('dashboard'))

    # Plantillas ubicadas directamente en /templates
    return render_template('register.html')
