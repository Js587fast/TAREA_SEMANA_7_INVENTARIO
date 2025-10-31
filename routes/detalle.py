from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, DetalleVenta, Venta, Producto, Cliente, Tienda
from utils.security import require_roles

detalle_bp = Blueprint('detalle', __name__, url_prefix='/detalle')

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
                flash("⚠️ Selecciona cliente y tienda.", "warning")
                return redirect(url_for("detalle.nuevo_detalle"))

            venta = Venta(id_cliente=id_cliente, id_tienda=id_tienda, total=0)
            db.session.add(venta)
            db.session.flush()

            total_venta = 0
            detalles = {}

            for key, value in request.form.items():
                if key.startswith("detalles"):
                    parts = key.strip("]").split("[")
                    idx = parts[1]
                    campo = parts[2]
                    detalles.setdefault(idx, {})[campo] = value

            for d in detalles.values():
                id_producto = int(d["id_producto"])
                cantidad = int(d["cantidad"])
                producto = Producto.query.get_or_404(id_producto)

                if producto.stock < cantidad:
                    flash(f"❌ Stock insuficiente para {producto.nombre}", "danger")
                    db.session.rollback()
                    return redirect(url_for("detalle.nuevo_detalle"))

                subtotal = producto.precio * cantidad
                total_venta += subtotal

                detalle = DetalleVenta(
                    id_venta=venta.id_venta,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                )
                db.session.add(detalle)
                producto.stock -= cantidad

            venta.total = total_venta
            db.session.commit()
            flash("✅ Detalle registrado correctamente.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error: {str(e)}", "danger")
            return redirect(url_for("detalle.nuevo_detalle"))

    return render_template("nuevo_detalle.html", clientes=clientes, productos=productos, tiendas=tiendas)

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
            cantidad = int(request.form["cantidad"])
            producto = Producto.query.get_or_404(id_producto)

            detalle.id_venta = id_venta
            detalle.id_producto = id_producto
            detalle.cantidad = cantidad
            detalle.subtotal = producto.precio * cantidad

            venta = Venta.query.get_or_404(id_venta)
            venta.total = sum(d.subtotal for d in venta.detalles)

            db.session.commit()
            flash("✅ Detalle actualizado correctamente.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error al actualizar: {str(e)}", "danger")
            return redirect(url_for("detalle.editar_detalle", id_detalle=id_detalle))

    return render_template("editar_detalle.html", detalle=detalle, ventas=ventas, productos=productos)

@detalle_bp.route("/eliminar/<int:id_detalle>", methods=["POST"])
@require_roles('administrador')
def eliminar_detalle(id_detalle):
    detalle = DetalleVenta.query.get_or_404(id_detalle)
    producto = detalle.producto
    venta = detalle.venta

    try:
        producto.stock += detalle.cantidad
        db.session.delete(detalle)
        venta.total = sum(d.subtotal for d in venta.detalles)
        db.session.commit()
        flash("🗑️ Detalle eliminado correctamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error al eliminar: {str(e)}", "danger")

    return redirect(url_for("dashboard"))
