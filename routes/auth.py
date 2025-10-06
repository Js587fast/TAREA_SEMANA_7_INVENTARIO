# inventario_pymes/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Usuario
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pantalla de login de usuarios"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(username=username).first()

        # ✅ Comprobación segura de contraseña
        if usuario and usuario.check_password(password):
            session.clear()  # Limpia cualquier sesión previa
            session['user_id'] = usuario.id
            session['rol'] = usuario.rol
            session.permanent = True  # Marca la sesión como permanente (necesario para que respete el tiempo configurado en app.py)
            flash("Login exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Cerrar sesión manualmente o por inactividad"""
    session.clear()  # Limpia toda la sesión
    flash("Tu sesión ha finalizado.", "warning")
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Pantalla de registro de nuevos usuarios"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validar si el usuario ya existe
        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe", "warning")
            return redirect(url_for('auth.register'))

        # Crear usuario con rol básico por defecto
        nuevo = Usuario(username=username, rol="usuario")
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()

        # Iniciar sesión automáticamente después del registro
        session.clear()
        session['user_id'] = nuevo.id
        session['rol'] = nuevo.rol
        session.permanent = True
        flash("Registro exitoso. ¡Bienvenido!", "success")
        return redirect(url_for('dashboard'))

    return render_template('register.html')
