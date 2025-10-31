# routes/venta.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Venta, Cliente, Producto, DetalleVenta, Inventario, Tienda
from datetime import date
from sqlalchemy.orm import joinedload
from utils.security import require_roles  # 🔐 Decorador para roles

venta_bp = Blueprint('venta', __name__, url_prefix='/venta')

# -------------------------------
# FUNCIÓN AUXILIAR
# -------------------------------
def parsear_detalles(form):
    """Convierte los campos del formulario en una estructura dict de detalles."""
    detalles = {}
    for key, value in form.items():
        if key.startswith("detalles"):
            # detalles[0][id_producto] -> index=0, field=id_producto
            parts = key.replace("detalles[", "").replace("]", "").split("[")
            index = parts[0]
            field = parts[1]
            detalles.setdefault(index, {})[field] = value

    # Quitar líneas vacías (sin producto o sin cantidad)
    depurados = {}
    for i, det in detalles.items():
        if str(det.get("id_producto", "")).strip() and str(det.get("cantidad", "")).strip():
            depurados[i] = det
    return depurados

# -------------------------------
# NUEVA VENTA
# -------------------------------
@venta_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
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
            db.session.flush()  # obtener id_venta

            total = 0
            detalles = parsear_detalles(request.form)
            if not detalles:
                flash("⚠️ Debes agregar al menos un producto.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.nueva_venta"))

            for det in detalles.values():
                # Parseo seguro
                id_producto = int(det.get("id_producto", 0))
                cantidad = int(det.get("cantidad", 0))

                if cantidad <= 0:
                    flash("⚠️ La cantidad debe ser > 0.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                # Precio SIEMPRE desde la base de datos 
                producto = Producto.query.get_or_404(id_producto)
                precio = float(producto.precio)  # <-- fuente de verdad
                subtotal = cantidad * precio

                # Validar/actualizar inventario por tienda
                inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
                if not inventario:
                    flash(f"❌ No hay inventario para '{producto.nombre}' en la tienda seleccionada.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                if inventario.cantidad < cantidad:
                    flash(f"❌ Stock insuficiente para {producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.nueva_venta"))

                inventario.cantidad -= cantidad
                total += subtotal

                db.session.add(DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                ))

            venta.total = total
            db.session.commit()
            flash("✅ Venta registrada correctamente.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al registrar venta: {str(e)}", "danger")
            return redirect(url_for("venta.nueva_venta"))

    return render_template("nueva_venta.html", clientes=clientes, productos=productos, tiendas=tiendas)

# -------------------------------
# EDITAR VENTA
# -------------------------------
@venta_bp.route("/editar/<int:id_venta>", methods=["GET", "POST"])
@require_roles('administrador')
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

            # 2) Borrar los detalles antiguos
            DetalleVenta.query.filter_by(id_venta=venta.id_venta).delete()

            # 3) Actualizar cabecera
            venta.id_cliente = int(request.form.get("id_cliente", venta.id_cliente))
            venta.fecha = request.form.get("fecha") or venta.fecha

            # 4) Agregar nuevos detalles
            total = 0
            detalles = parsear_detalles(request.form)
            if not detalles:
                flash("⚠️ Debes agregar al menos un producto.", "danger")
                db.session.rollback()
                return redirect(url_for("venta.editar_venta", id_venta=id_venta))

            for det in detalles.values():
                id_producto = int(det.get("id_producto", 0))
                cantidad = int(det.get("cantidad", 0))

                if cantidad <= 0:
                    flash("⚠️ La cantidad debe ser > 0.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                # Precio SIEMPRE desde la base de datos 
                producto = Producto.query.get_or_404(id_producto)
                precio = float(producto.precio)
                subtotal = cantidad * precio

                inventario = Inventario.query.filter_by(id_producto=id_producto, id_tienda=id_tienda).first()
                if not inventario:
                    flash(f"❌ No hay inventario para '{producto.nombre}' en la tienda de la venta.", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                if inventario.cantidad < cantidad:
                    flash(f"❌ Stock insuficiente para {producto.nombre}. Disponible: {inventario.cantidad}", "danger")
                    db.session.rollback()
                    return redirect(url_for("venta.editar_venta", id_venta=id_venta))

                inventario.cantidad -= cantidad
                total += subtotal

                db.session.add(DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                ))

            venta.total = total
            db.session.commit()
            flash("✅ Venta actualizada correctamente.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al actualizar venta: {str(e)}", "danger")
            return redirect(url_for("venta.editar_venta", id_venta=id_venta))

    return render_template("editar_venta.html", venta=venta, clientes=clientes, productos=productos, tiendas=tiendas)

# -------------------------------
# ELIMINAR VENTA
# -------------------------------
@venta_bp.route("/eliminar/<int:id_venta>", methods=["POST"])
@require_roles('administrador')
def eliminar_venta(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    id_tienda = venta.id_tienda

    try:
        for detalle in venta.detalles:
            inv = Inventario.query.filter_by(id_producto=detalle.id_producto, id_tienda=id_tienda).first()
            if inv:
                inv.cantidad += detalle.cantidad
            db.session.delete(detalle)

        db.session.delete(venta)
        db.session.commit()
        flash("🗑️ Venta eliminada y stock restaurado correctamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ No se pudo eliminar la venta: {str(e)}", "danger")

    return redirect(url_for("dashboard"))
