from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import and_
from models import db, Proveedor
from utils.security import require_roles  # 🔐 Control de roles

proveedor_bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')


# ---- Listar / buscar proveedores (solo administradores) ----
@proveedor_bp.route("/")
@require_roles('administrador')
def index():
    q = (request.args.get("q") or "").strip()
    query = Proveedor.query
    if q:
        # búsqueda simple por nombre / contacto / email / ubicación
        like = f"%{q}%"
        query = query.filter(
            (Proveedor.nombre.ilike(like)) |
            (Proveedor.contacto.ilike(like)) |
            (Proveedor.email.ilike(like)) |
            (Proveedor.ubicacion.ilike(like))
        )
    proveedores = query.order_by(Proveedor.nombre.asc()).all()
    return render_template("proveedores.html", proveedores=proveedores, q=q)


# ---- Crear proveedor (solo administradores) ----
@proveedor_bp.route('/nuevo', methods=['GET', 'POST'])
@require_roles('administrador')
def nuevo_proveedor():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        contacto = (request.form.get('contacto') or '').strip()
        email = (request.form.get('email') or '').strip()
        ubicacion = (request.form.get('ubicacion') or '').strip()

        if not nombre:
            flash('El nombre del proveedor es obligatorio.', 'warning')
            return redirect(url_for('proveedor.nuevo_proveedor'))

        # Evitar duplicado básico por (nombre, ubicacion)
        existe = Proveedor.query.filter(
            and_(Proveedor.nombre == nombre, Proveedor.ubicacion == (ubicacion or None))
        ).first()
        if existe:
            flash('Ya existe un proveedor con el mismo nombre y ubicación.', 'warning')
            return redirect(url_for('proveedor.nuevo_proveedor'))

        try:
            nuevo = Proveedor(
                nombre=nombre,
                contacto=contacto,
                email=email,
                ubicacion=ubicacion or None
            )
            db.session.add(nuevo)
            db.session.commit()
            flash('Proveedor creado correctamente ✅', 'success')
            return redirect(url_for('proveedor.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'No se pudo crear el proveedor: {e}', 'danger')
            return redirect(url_for('proveedor.nuevo_proveedor'))

    return render_template('nuevo_proveedor.html')


# ---- Editar proveedor (solo administradores) ----
@proveedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@require_roles('administrador')
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        contacto = (request.form.get('contacto') or '').strip()
        email = (request.form.get('email') or '').strip()
        ubicacion = (request.form.get('ubicacion') or '').strip()

        if not nombre:
            flash('El nombre del proveedor es obligatorio.', 'warning')
            return redirect(url_for('proveedor.editar_proveedor', id=id))

        # Evitar duplicado con otro registro
        existe = Proveedor.query.filter(
            and_(
                Proveedor.id_proveedor != proveedor.id_proveedor,
                Proveedor.nombre == nombre,
                Proveedor.ubicacion == (ubicacion or None)
            )
        ).first()
        if existe:
            flash('Ya existe otro proveedor con el mismo nombre y ubicación.', 'warning')
            return redirect(url_for('proveedor.editar_proveedor', id=id))

        try:
            proveedor.nombre = nombre
            proveedor.contacto = contacto
            proveedor.email = email
            proveedor.ubicacion = ubicacion or None
            db.session.commit()
            flash('Proveedor actualizado correctamente ✅', 'success')
            return redirect(url_for('proveedor.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'No se pudo actualizar el proveedor: {e}', 'danger')
            return redirect(url_for('proveedor.editar_proveedor', id=id))

    return render_template('editar_proveedor.html', proveedor=proveedor)


# ---- Eliminar proveedor (solo administradores, usando POST) ----
@proveedor_bp.route('/eliminar/<int:id>', methods=['POST'])
@require_roles('administrador')
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    try:
        db.session.delete(proveedor)
        db.session.commit()
        flash('Proveedor eliminado correctamente ✅', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'No se pudo eliminar el proveedor: {e}', 'danger')
    return redirect(url_for('proveedor.index'))
