from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, DetalleVenta, Venta, Producto

detalle_bp = Blueprint('detalle', __name__, url_prefix='/detalle')

# ---- Decorador login ----
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# NUEVO DETALLE
# -------------------------------
@detalle_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_detalle():
    ventas = Venta.query.all()
    productos = Producto.query.all()

    if request.method == "POST":
        id_venta = int(request.form["id_venta"])
        id_producto = int(request.form["id_producto"])
        cantidad = int(request.form["cantidad"])

        # Calcular subtotal en el servidor (seguro)
        producto = Producto.query.get(id_producto)
        if not producto:
            flash("Producto no encontrado", "danger")
            return redirect(url_for("detalle.nuevo_detalle"))
        subtotal = producto.precio * cantidad

        # Crear detalle
        d = DetalleVenta(id_venta=id_venta, id_producto=id_producto, cantidad=cantidad, subtotal=subtotal)
        db.session.add(d)

        # Actualizar stock
        producto.stock -= cantidad

        # Recalcular total de la venta
        venta = Venta.query.get(id_venta)
        venta.total = sum(det.subtotal for det in venta.detalles)

        db.session.commit()
        flash("Detalle agregado y total actualizado", "success")
        return redirect(url_for("dashboard"))

    return render_template("nuevo_detalle.html", ventas=ventas, productos=productos)

# -------------------------------
# EDITAR DETALLE
# -------------------------------
@detalle_bp.route("/editar/<int:id_detalle>", methods=["GET", "POST"])
@login_required
def editar_detalle(id_detalle):
    d = DetalleVenta.query.get_or_404(id_detalle)
    ventas = Venta.query.all()
    productos = Producto.query.all()

    if request.method == "POST":
        id_venta = int(request.form["id_venta"])
        id_producto = int(request.form["id_producto"])
        cantidad = int(request.form["cantidad"])

        producto = Producto.query.get(id_producto)
        if not producto:
            flash("Producto no encontrado", "danger")
            return redirect(url_for("detalle.editar_detalle", id_detalle=id_detalle))

        # Si se cambia la cantidad, se actualiza stock correctamente
        diferencia = cantidad - d.cantidad
        producto.stock -= diferencia

        # Recalcular subtotal
        d.id_venta = id_venta
        d.id_producto = id_producto
        d.cantidad = cantidad
        d.subtotal = producto.precio * cantidad

        # Recalcular total de la venta
        venta = Venta.query.get(id_venta)
        venta.total = sum(det.subtotal for det in venta.detalles)

        db.session.commit()
        flash("Detalle actualizado y total recalculado", "success")
        return redirect(url_for("dashboard"))

    return render_template("editar_detalle.html", detalle=d, ventas=ventas, productos=productos)

# -------------------------------
# ELIMINAR DETALLE
# -------------------------------
@detalle_bp.route("/eliminar/<int:id_detalle>")
@login_required
def eliminar_detalle(id_detalle):
    d = DetalleVenta.query.get_or_404(id_detalle)
    id_venta = d.id_venta

    db.session.delete(d)
    db.session.commit()

    # Recalcular total de la venta luego de eliminar
    venta = Venta.query.get(id_venta)
    if venta:
        venta.total = sum(det.subtotal for det in venta.detalles)
        db.session.commit()

    flash("Detalle eliminado y total actualizado", "success")
    return redirect(url_for("dashboard"))
