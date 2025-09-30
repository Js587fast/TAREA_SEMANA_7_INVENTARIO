from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Venta, Cliente, Producto, DetalleVenta, Inventario, Tienda
from datetime import date
from functools import wraps

venta_bp = Blueprint('venta', __name__, url_prefix='/venta')

# ---- Decorador para exigir login ----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---- Crear nueva venta ----
@venta_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nueva_venta():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()

    if request.method == "POST":
        id_cliente = request.form.get("id_cliente")
        fecha = request.form.get("fecha") or date.today()
        id_tienda = int(request.form.get("id_tienda"))

        venta = Venta(fecha=fecha, total=0, id_cliente=id_cliente, id_tienda=id_tienda)
        db.session.add(venta)
        db.session.flush()

        total = 0
        detalles = {}
        for key, value in request.form.items():
            if key.startswith("detalles"):
                parts = key.replace("detalles[", "").replace("]", "").split("[")
                index = parts[0]
                field = parts[1]
                detalles.setdefault(index, {})[field] = value

        for det in detalles.values():
            id_producto = int(det.get("id_producto"))
            cantidad = int(det.get("cantidad"))
            precio = float(det.get("precio_unitario"))

            inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
            if not inventario:
                flash(f"❌ No hay inventario para este producto en la tienda seleccionada.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.nueva_venta"))

            if inventario.cantidad < cantidad:
                flash(f"❌ Stock insuficiente para {inventario.producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                db.session.rollback()
                return redirect(url_for("venta.nueva_venta"))

            inventario.cantidad -= cantidad
            subtotal = cantidad * precio
            total += subtotal

            detalle = DetalleVenta(
                id_venta=venta.id_venta,
                id_producto=id_producto,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(detalle)

        venta.total = total
        db.session.commit()

        flash("✅ Venta registrada y stock de inventario actualizado correctamente", "success")
        return redirect(url_for("dashboard"))

    return render_template("nueva_venta.html", clientes=clientes, productos=productos, tiendas=tiendas)


# ---- Editar venta existente ----
@venta_bp.route("/editar/<int:id_venta>", methods=["GET", "POST"])
@login_required
def editar_venta(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()
    id_tienda = venta.id_tienda  # Se usa la tienda de la venta

    if request.method == "POST":
        # Devolver stock de detalles anteriores
        for detalle in venta.detalles:
            inv = Inventario.query.filter_by(id_producto=detalle.id_producto, id_tienda=id_tienda).first()
            if inv:
                inv.cantidad += detalle.cantidad

        # Borrar detalles antiguos
        DetalleVenta.query.filter_by(id_venta=venta.id_venta).delete()

        venta.id_cliente = request.form.get("id_cliente")
        venta.fecha = request.form.get("fecha") or date.today()

        total = 0
        detalles = {}
        for key, value in request.form.items():
            if key.startswith("detalles"):
                parts = key.replace("detalles[", "").replace("]", "").split("[")
                index = parts[0]
                field = parts[1]
                detalles.setdefault(index, {})[field] = value

        for det in detalles.values():
            id_producto = int(det.get("id_producto"))
            cantidad = int(det.get("cantidad"))
            precio = float(det.get("precio_unitario"))

            inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
            if not inventario:
                flash(f"❌ No hay inventario para este producto en la tienda de la venta.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.editar_venta", id_venta=id_venta))

            if inventario.cantidad < cantidad:
                flash(f"❌ Stock insuficiente para {inventario.producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                db.session.rollback()
                return redirect(url_for("venta.editar_venta", id_venta=id_venta))

            inventario.cantidad -= cantidad
            subtotal = cantidad * precio
            total += subtotal

            nuevo_detalle = DetalleVenta(
                id_venta=venta.id_venta,
                id_producto=id_producto,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(nuevo_detalle)

        venta.total = total
        db.session.commit()

        flash("Venta actualizada y stock de inventario recalculado ✅", "success")
        return redirect(url_for("dashboard"))

    return render_template("editar_venta.html", venta=venta, clientes=clientes, productos=productos, tiendas=tiendas)


# ---- Eliminar venta ----
@venta_bp.route("/eliminar/<int:id_venta>", methods=["POST"])
@login_required
def eliminar_venta(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    id_tienda = venta.id_tienda

    # Devolver stock
    for detalle in venta.detalles:
        inv = Inventario.query.filter_by(id_producto=detalle.id_producto, id_tienda=id_tienda).first()
        if inv:
            inv.cantidad += detalle.cantidad
        db.session.delete(detalle)

    db.session.delete(venta)
    db.session.commit()
    flash("Venta eliminada y stock de inventario restaurado 🗑️", "success")
    return redirect(url_for("dashboard"))