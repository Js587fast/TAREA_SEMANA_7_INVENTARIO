from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Proveedor

proveedor_bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')

@proveedor_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form.get('contacto')
        p = Proveedor(nombre=nombre, contacto=contacto)
        db.session.add(p)
        db.session.commit()
        flash('Proveedor creado correctamente ✅', 'success')
        return redirect(url_for('dashboard'))
    return render_template('nuevo_proveedor.html')

@proveedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):
    p = Proveedor.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form['nombre']
        p.contacto = request.form.get('contacto')
        db.session.commit()
        flash('Proveedor actualizado correctamente ✅', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editar_proveedor.html', proveedor=p)

@proveedor_bp.route('/eliminar/<int:id>', methods=['POST'])  # 🔹 ACEPTA POST
def eliminar_proveedor(id):
    p = Proveedor.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Proveedor eliminado correctamente ✅', 'success')
    return redirect(url_for('dashboard'))
