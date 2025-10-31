from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Producto, Proveedor
from utils.security import require_roles  # <- Se importa nuevo decorador

producto_bp = Blueprint('producto', __name__, url_prefix='/producto')


# ---- Listar productos (solo administrador) ----
@producto_bp.route("/")
@require_roles('administrador')
def index():
    productos = Producto.query.all()
    return render_template("productos.html", productos=productos)


# ---- Crear producto (solo administrador) ----
@producto_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
def nuevo_producto():
    proveedores = Proveedor.query.all()

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        precio = float(request.form.get("precio", 0))
        stock = int(request.form.get("stock", 0))
        id_proveedor = request.form.get("id_proveedor")

        if not nombre:
            flash("El nombre del producto es obligatorio.", "warning")
            return redirect(url_for("producto.nuevo_producto"))

        pr = Producto(nombre=nombre, precio=precio, stock=stock, id_proveedor=id_proveedor)
        db.session.add(pr)
        db.session.commit()
        flash("Producto registrado correctamente.", "success")
        return redirect(url_for("producto.index"))

    return render_template("nuevo_producto.html", proveedores=proveedores)


# ---- Editar producto (solo administrador) ----
@producto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@require_roles('administrador')
def editar_producto(id):
    pr = Producto.query.get_or_404(id)
    proveedores = Proveedor.query.all()

    if request.method == "POST":
        pr.nombre = request.form["nombre"].strip()
        pr.precio = float(request.form.get("precio", 0))
        pr.stock = int(request.form.get("stock", 0))
        pr.id_proveedor = request.form.get("id_proveedor")
        db.session.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("producto.index"))

    return render_template("editar_producto.html", producto=pr, proveedores=proveedores)


# ---- Eliminar producto (solo administrador, uso de POST) ----
@producto_bp.route("/eliminar/<int:id>", methods=["POST"])
@require_roles('administrador')
def eliminar_producto(id):
    pr = Producto.query.get_or_404(id)
    db.session.delete(pr)
    db.session.commit()
    flash("Producto eliminado correctamente.", "info")
    return redirect(url_for("producto.index"))
