from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, DetalleVenta, Venta, Producto, Cliente, Tienda
from utils.security import require_roles  # 🔐 Importamos el decorador para roles

# -------------------------------
# BLUEPRINT DETALLE
# -------------------------------
detalle_bp = Blueprint('detalle', __name__, url_prefix='/detalle')


# -------------------------------
# NUEVO DETALLE (solo administradores)
# -------------------------------
@detalle_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
def nuevo_detalle():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()

    if request.method == "POST":
        try:
            id_cliente = int(request.form.get("id_cliente", 0))
            id_tienda = int(request.form.get("id_tienda", 0))

            if not id_cliente or not id_tienda:
                flash("⚠️ Debes seleccionar cliente y tienda.", "warning")
                return redirect(url_for("detalle.nuevo_detalle"))

            # Crear venta nueva
            venta = Venta(id_cliente=id_cliente, id_tienda=id_tienda, total=0)
            db.session.add(venta)
            db.session.flush()  # Se obtiene id_venta antes de commit

            # Se procesan detalles del formulario
            detalles = {}
            for key, value in request.form.items():
                if key.startswith("detalles"):
                    # ejemplo key = detalles[0][id_producto]
                    parts = key.strip("]").split("[")
                    idx = parts[1]
                    campo = parts[2]
                    detalles.setdefault(idx, {})[campo] = value

            total_venta = 0
            for d in detalles.values():
                id_producto = int(d["id_producto"])
                cantidad = int(d["cantidad"])
                precio_unitario = float(d["precio_unitario"])

                producto = Producto.query.get_or_404(id_producto)

                # Validar stock
                if producto.stock < cantidad:
                    flash(f"❌ Stock insuficiente para {producto.nombre}", "danger")
                    db.session.rollback()
                    return redirect(url_for("detalle.nuevo_detalle"))

                subtotal = precio_unitario * cantidad
                total_venta += subtotal

                # Crear detalle
                detalle = DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                )
                db.session.add(detalle)

                # Actualizar stock
                producto.stock -= cantidad

            venta.total = total_venta
            db.session.commit()

            flash("✅ Venta y detalles registrados correctamente.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al guardar detalle: {str(e)}", "danger")
            return redirect(url_for("detalle.nuevo_detalle"))

    return render_template(
        "nuevo_detalle.html",
        clientes=clientes,
        productos=productos,
        tiendas=tiendas
    )


# -------------------------------
# EDITAR DETALLE (solo administradores)
# -------------------------------
@detalle_bp.route("/editar/<int:id_detalle>", methods=["GET", "POST"])
@require_roles('administrador')
def editar_detalle(id_detalle):
    detalle = DetalleVenta.query.get_or_404(id_detalle)
    ventas = Venta.query.all()
    productos = Producto.query.all()

    if request.method == "POST":
        try:
            id_venta = int(request.form["id_venta"])
            id_producto = int(request.form["id_producto"])
            cantidad_nueva = int(request.form["cantidad"])

            producto = Producto.query.get_or_404(id_producto)

            # Validar stock considerando diferencia
            diferencia = cantidad_nueva - detalle.cantidad
            if diferencia > 0 and producto.stock < diferencia:
                flash(f"No hay stock suficiente para aumentar a {cantidad_nueva} unidades.", "danger")
                return redirect(url_for("detalle.editar_detalle", id_detalle=id_detalle))

            # Ajustar stock
            producto.stock -= diferencia

            # Actualizar detalle
            detalle.id_venta = id_venta
            detalle.id_producto = id_producto
            detalle.cantidad = cantidad_nueva
            detalle.subtotal = float(producto.precio) * cantidad_nueva

            # Recalcular total venta
            venta = Venta.query.get_or_404(id_venta)
            venta.total = sum(d.subtotal for d in venta.detalles)

            db.session.commit()
            flash("✅ Detalle actualizado y stock ajustado correctamente.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al actualizar el detalle: {str(e)}", "danger")
            return redirect(url_for("detalle.editar_detalle", id_detalle=id_detalle))

    return render_template(
        "editar_detalle.html",
        detalle=detalle,
        ventas=ventas,
        productos=productos
    )


# -------------------------------
# ELIMINAR DETALLE (solo administradores)
# -------------------------------
@detalle_bp.route("/eliminar/<int:id_detalle>", methods=["POST"])
@require_roles('administrador')
def eliminar_detalle(id_detalle):
    detalle = DetalleVenta.query.get_or_404(id_detalle)
    venta = detalle.venta
    producto = detalle.producto

    try:
        # Devolver stock
        producto.stock += detalle.cantidad

        # Borrar detalle
        db.session.delete(detalle)
        db.session.commit()

        # Recalcular total de la venta
        venta.total = sum(d.subtotal for d in venta.detalles)
        db.session.commit()

        flash("🗑️ Detalle eliminado y stock devuelto correctamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error al eliminar el detalle: {str(e)}", "danger")

    return redirect(url_for("dashboard"))
