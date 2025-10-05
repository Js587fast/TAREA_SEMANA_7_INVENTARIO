from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Proveedor

proveedor_bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')

# ---- Decorador para exigir login ----
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---- Listar proveedores ----
@proveedor_bp.route("/")
@login_required
def index():
    proveedores = Proveedor.query.all()
    return render_template("proveedores.html", proveedores=proveedores)


# ---- Crear proveedor ----
@proveedor_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form.get('contacto')
        email = request.form.get('email')  # ✅ nuevo campo
        p = Proveedor(nombre=nombre, contacto=contacto, email=email)
        db.session.add(p)
        db.session.commit()
        flash('Proveedor creado correctamente ✅', 'success')
        return redirect(url_for('proveedor.index'))
    return render_template('nuevo_proveedor.html')


# ---- Editar proveedor ----
@proveedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_proveedor(id):
    p = Proveedor.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form['nombre']
        p.contacto = request.form.get('contacto')
        p.email = request.form.get('email')  # ✅ actualizar campo
        db.session.commit()
        flash('Proveedor actualizado correctamente ✅', 'success')
        return redirect(url_for('proveedor.index'))
    return render_template('editar_proveedor.html', proveedor=p)


# ---- Eliminar proveedor ----
@proveedor_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_proveedor(id):
    p = Proveedor.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Proveedor eliminado correctamente ✅', 'success')
    return redirect(url_for('proveedor.index'))
