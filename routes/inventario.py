from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Inventario, Producto, Tienda
from utils.security import require_roles  # 🔐 control de roles

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')


# ---- Listado de inventario (visible para usuario y administrador) ----
@inventario_bp.route("/")
@require_roles('usuario', 'administrador')
def index():
    inventarios = obtener_datos_inventario()
    return render_template("inventarios.html", inventarios=inventarios)


# ---- Crear inventario (solo administrador) ----
@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
def nuevo_inventario():
    productos = Producto.query.all()
    tiendas = Tienda.query.all()

    if request.method == "POST":
        try:
            cantidad = int(request.form["cantidad"])
            id_producto = int(request.form["id_producto"])
            id_tienda = int(request.form["id_tienda"])

            # validar duplicados por (producto, tienda)
            existente = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
            if existente:
                existente.cantidad += cantidad
                db.session.commit()
                flash("Cantidad sumada al inventario existente.", "success")
                return redirect(url_for("inventario.index"))

            i = Inventario(cantidad=cantidad, id_producto=id_producto, id_tienda=id_tienda)
            db.session.add(i)
            db.session.commit()
            flash("Inventario creado correctamente.", "success")
            return redirect(url_for("inventario.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear inventario: {e}", "danger")

    return render_template("nuevo_inventario.html", productos=productos, tiendas=tiendas)


# ---- Editar inventario (solo administrador) ----
@inventario_bp.route("/editar/<int:id_inventario>", methods=["GET", "POST"])
@require_roles('administrador')
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
            return redirect(url_for("inventario.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar inventario: {e}", "danger")

    return render_template("editar_inventario.html", inventario=i, productos=productos, tiendas=tiendas)


# ---- Eliminar inventario (solo administrador, por POST) ----
@inventario_bp.route("/eliminar/<int:id_inventario>", methods=["POST"])
@require_roles('administrador')
def eliminar_inventario(id_inventario):
    i = Inventario.query.get_or_404(id_inventario)
    try:
        db.session.delete(i)
        db.session.commit()
        flash("Inventario eliminado correctamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar inventario: {e}", "danger")
    return redirect(url_for("inventario.index"))


# ---- Helper para el listado ----
def obtener_datos_inventario():
    return db.session.query(
        Inventario.id_inventario.label("ID"),
        Producto.nombre.label("Producto"),
        Tienda.nombre.label("Tienda"),
        Inventario.cantidad.label("Cantidad")
    ).join(
        Producto, Inventario.id_producto == Producto.id_producto
    ).join(
        Tienda, Inventario.id_tienda == Tienda.id_tienda
    ).all()
