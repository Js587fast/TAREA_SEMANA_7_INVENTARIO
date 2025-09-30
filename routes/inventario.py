from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Inventario, Producto, Tienda

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_inventario():
    productos = Producto.query.all()
    tiendas = Tienda.query.all()
    if request.method == "POST":
        try:
            cantidad = int(request.form["cantidad"])
            id_producto = int(request.form["id_producto"])
            id_tienda = int(request.form["id_tienda"])
            i = Inventario(cantidad=cantidad, id_producto=id_producto, id_tienda=id_tienda)
            db.session.add(i)
            db.session.commit()
            flash("Inventario creado correctamente.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear inventario: {e}", "danger")
    return render_template("nuevo_inventario.html", productos=productos, tiendas=tiendas)

@inventario_bp.route("/editar/<int:id_inventario>", methods=["GET", "POST"])
@login_required
def editar_inventario(id_inventario):
    i = Inventario.query.get_or_404(id_inventario)
    productos = Producto.query.all()
    tiendas = Tienda.query.all()
    if request.method == "POST":
        try:
            i.cantidad = int(request.form["cantidad"])
            i.id_producto = int(request.form["id_producto"])
            i.id_tienda = int(request.form["id_tienda"])
            db.session.commit()
            flash("Inventario actualizado correctamente.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar inventario: {e}", "danger")
    return render_template("editar_inventario.html", inventario=i, productos=productos, tiendas=tiendas)

@inventario_bp.route("/eliminar/<int:id_inventario>")
@login_required
def eliminar_inventario(id_inventario):
    i = Inventario.query.get_or_404(id_inventario)
    try:
        db.session.delete(i)
        db.session.commit()
        flash("Inventario eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar inventario: {e}", "danger")
    return redirect(url_for("dashboard"))

def obtener_datos_inventario():
    return db.session.query(
        Inventario.id_inventario.label("ID"),
        Producto.nombre.label("Producto"),
        Tienda.nombre.label("Tienda"),
        Inventario.cantidad.label("Cantidad")
    ).join(Producto, Inventario.id_producto == Producto.id_producto
    ).join(Tienda, Inventario.id_tienda == Tienda.id_tienda
    ).all()
