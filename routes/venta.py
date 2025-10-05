from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Venta, Cliente, Producto, DetalleVenta, Inventario, Tienda
from datetime import date
from functools import wraps
from sqlalchemy.orm import joinedload

venta_bp = Blueprint('venta', __name__, url_prefix='/venta')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para continuar", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def parsear_detalles(form):
    detalles = {}
    for key, value in form.items():
        if key.startswith("detalles"):
            parts = key.replace("detalles[", "").replace("]", "").split("[")
            index = parts[0]
            field = parts[1]
            detalles.setdefault(index, {})[field] = value
    # Quitar líneas vacías o sin producto/cantidad
    depurados = {}
    for i, det in detalles.items():
        if str(det.get("id_producto", "")).strip() and str(det.get("cantidad", "")).strip():
            depurados[i] = det
    return depurados

@venta_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nueva_venta():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()

    if request.method == "POST":
        try:
            id_cliente = int(request.form.get("id_cliente", 0))
            id_tienda = int(request.form.get("id_tienda", 0))
            fecha = request.form.get("fecha") or date.today()

            if not id_cliente or not id_tienda:
                flash("⚠️ Debes seleccionar cliente y tienda.", "danger")
                return redirect(url_for("venta.nueva_venta"))

            venta = Venta(fecha=fecha, total=0, id_cliente=id_cliente, id_tienda=id_tienda)
            db.session.add(venta)
            db.session.flush()  # obtén id_venta

            total = 0
            detalles = parsear_detalles(request.form)
            if not detalles:
                flash("⚠️ Debes agregar al menos un producto.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.nueva_venta"))

            for det in detalles.values():
                try:
                    id_producto = int(det.get("id_producto", 0))
                    cantidad = int(det.get("cantidad", 0))
                    precio = float(det.get("precio_unitario", 0))
                except ValueError:
                    flash("⚠️ Datos inválidos en los detalles de la venta.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                if cantidad <= 0 or precio < 0:
                    flash("⚠️ Cantidad debe ser > 0 y precio ≥ 0.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
                if not inventario:
                    flash("❌ No hay inventario para este producto en la tienda seleccionada.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                if inventario.cantidad < cantidad:
                    flash(f"❌ Stock insuficiente para {inventario.producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                inventario.cantidad -= cantidad
                subtotal = cantidad * precio
                total += subtotal

                db.session.add(DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                ))

            venta.total = total
            db.session.commit()
            flash("✅ Venta registrada y stock de inventario actualizado correctamente", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Ocurrió un error al registrar la venta: {str(e)}", "danger")
            return redirect(url_for("venta.nueva_venta"))

    return render_template("nueva_venta.html", clientes=clientes, productos=productos, tiendas=tiendas)

@venta_bp.route("/editar/<int:id_venta>", methods=["GET", "POST"])
@login_required
def editar_venta(id_venta):
    venta = Venta.query.options(
        joinedload(Venta.detalles).joinedload(DetalleVenta.producto)
    ).get_or_404(id_venta)

    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()
    id_tienda = venta.id_tienda

    if request.method == "POST":
        try:
            # 1) Devolver stock de los detalles actuales
            for detalle in venta.detalles:
                inv = Inventario.query.filter_by(id_producto=detalle.id_producto, id_tienda=id_tienda).first()
                if inv:
                    inv.cantidad += detalle.cantidad

            # 2) Borrar detalles antiguos
            DetalleVenta.query.filter_by(id_venta=venta.id_venta).delete()

            # 3) Actualizar cabecera
            venta.id_cliente = int(request.form.get("id_cliente", venta.id_cliente))
            venta.fecha = request.form.get("fecha") or venta.fecha

            # 4) Parsear y revalidar
            total = 0
            detalles = parsear_detalles(request.form)
            if not detalles:
                flash("⚠️ Debes agregar al menos un producto.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.editar_venta", id_venta=id_venta))

            for det in detalles.values():
                try:
                    id_producto = int(det.get("id_producto", 0))
                    cantidad = int(det.get("cantidad", 0))
                    precio = float(det.get("precio_unitario", 0))
                except ValueError:
                    flash("⚠️ Datos inválidos en los detalles.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                if cantidad <= 0 or precio < 0:
                    flash("⚠️ Cantidad debe ser > 0 y precio ≥ 0.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
                if not inventario:
                    flash("❌ No hay inventario para este producto en la tienda de la venta.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                if inventario.cantidad < cantidad:
                    flash(f"❌ Stock insuficiente para {inventario.producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                inventario.cantidad -= cantidad
                subtotal = cantidad * precio
                total += subtotal

                db.session.add(DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                ))

            venta.total = total
            db.session.commit()
            flash("✅ Venta actualizada y stock de inventario recalculado", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al actualizar la venta: {str(e)}", "danger")
            return redirect(url_for("venta.editar_venta", id_venta=id_venta))

    return render_template("editar_venta.html", venta=venta, clientes=clientes, productos=productos, tiendas=tiendas)

@venta_bp.route("/eliminar/<int:id_venta>", methods=["POST"])
@login_required
def eliminar_venta(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    id_tienda = venta.id_tienda
    try:
        # Devolver stock y borrar detalles
        for detalle in venta.detalles:
            inv = Inventario.query.filter_by(id_producto=detalle.id_producto, id_tienda=id_tienda).first()
            if inv:
                inv.cantidad += detalle.cantidad
            db.session.delete(detalle)

        db.session.delete(venta)
        db.session.commit()
        flash("🗑️ Venta eliminada y stock de inventario restaurado", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ No se pudo eliminar la venta: {str(e)}", "danger")

    return redirect(url_for("dashboard"))
