# inventario_pymes/routes/detalle.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, DetalleVenta, Venta, Producto, Cliente, Tienda
from functools import wraps

# -------------------------------
# BLUEPRINT DETALLE
# -------------------------------
detalle_bp = Blueprint('detalle', __name__, url_prefix='/detalle')

# -------------------------------
# DECORADOR LOGIN
# -------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# NUEVO DETALLE (crea venta y detalle juntos)
# -------------------------------
@detalle_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_detalle():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    tiendas = Tienda.query.all()  # 👈 importante: traer tiendas

    if request.method == "POST":
        try:
            id_cliente = int(request.form["id_cliente"])
            id_tienda = int(request.form["id_tienda"])  # 👈 ahora pedimos la tienda

            # Crear venta nueva para el cliente y la tienda
            venta = Venta(id_cliente=id_cliente, id_tienda=id_tienda, total=0)
            db.session.add(venta)
            db.session.flush()  # obtener id_venta antes de commit

            # Procesar detalles dinámicos enviados por el formulario
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
                    flash(f"Stock insuficiente para {producto.nombre}", "danger")
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

            # Guardar total de la venta
            venta.total = total_venta

            db.session.commit()
            flash("Venta y detalles registrados correctamente ✅", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al guardar detalle: {str(e)}", "danger")
            return redirect(url_for("detalle.nuevo_detalle"))

    return render_template(
        "nuevo_detalle.html",
        clientes=clientes,
        productos=productos,
        tiendas=tiendas
    )

# -------------------------------
# EDITAR DETALLE
# -------------------------------
@detalle_bp.route("/editar/<int:id_detalle>", methods=["GET", "POST"])
@login_required
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
            flash("Detalle actualizado correctamente ✅", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el detalle: {str(e)}", "danger")
            return redirect(url_for("detalle.editar_detalle", id_detalle=id_detalle))

    return render_template(
        "editar_detalle.html",
        detalle=detalle,
        ventas=ventas,
        productos=productos
    )

# -------------------------------
# ELIMINAR DETALLE
# -------------------------------
@detalle_bp.route("/eliminar/<int:id_detalle>", methods=["POST"])
@login_required
def eliminar_detalle(id_detalle):
    detalle = DetalleVenta.query.get_or_404(id_detalle)
    venta = detalle.venta  # venta asociada

    # Devolver stock
    producto = detalle.producto
    producto.stock += detalle.cantidad

    # Borrar detalle
    db.session.delete(detalle)
    db.session.commit()

    # Recalcular total de la venta
    venta.total = sum(d.subtotal for d in venta.detalles)
    db.session.commit()

    flash("Detalle eliminado y stock devuelto correctamente ✅", "success")
    return redirect(url_for("dashboard"))
