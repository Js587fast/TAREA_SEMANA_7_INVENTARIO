from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validacion con base de datos
        session['user_id'] = username
        flash("Login exitoso.", "success")
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Guardar el usuario en la base de datos
        session['user_id'] = username
        flash("Registro exitoso.", "success")
        return redirect(url_for('dashboard'))
    return render_template('register.html')
