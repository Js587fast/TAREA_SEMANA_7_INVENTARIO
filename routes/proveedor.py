from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Proveedor
from utils.security import require_roles  # 🔐 Control de roles

proveedor_bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')


# ---- Listar proveedores (solo administradores) ----
@proveedor_bp.route("/")
@require_roles('administrador')
def index():
    proveedores = Proveedor.query.all()
    return render_template("proveedores.html", proveedores=proveedores)


# ---- Crear proveedor (solo administradores) ----
@proveedor_bp.route('/nuevo', methods=['GET', 'POST'])
@require_roles('administrador')
def nuevo_proveedor():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        contacto = request.form.get('contacto', '').strip()
        email = request.form.get('email', '').strip()

        if not nombre:
            flash('El nombre del proveedor es obligatorio.', 'warning')
            return redirect(url_for('proveedor.nuevo_proveedor'))

        nuevo = Proveedor(nombre=nombre, contacto=contacto, email=email)
        db.session.add(nuevo)
        db.session.commit()
        flash('Proveedor creado correctamente ✅', 'success')
        return redirect(url_for('proveedor.index'))

    return render_template('nuevo_proveedor.html')


# ---- Editar proveedor (solo administradores) ----
@proveedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@require_roles('administrador')
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        proveedor.nombre = request.form.get('nombre', '').strip()
        proveedor.contacto = request.form.get('contacto', '').strip()
        proveedor.email = request.form.get('email', '').strip()
        db.session.commit()
        flash('Proveedor actualizado correctamente ✅', 'success')
        return redirect(url_for('proveedor.index'))

    return render_template('editar_proveedor.html', proveedor=proveedor)


# ---- Eliminar proveedor (solo administradores, usando POST) ----
@proveedor_bp.route('/eliminar/<int:id>', methods=['POST'])
@require_roles('administrador')
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    flash('Proveedor eliminado correctamente ✅', 'info')
    return redirect(url_for('proveedor.index'))
