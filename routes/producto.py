from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Producto, Proveedor

producto_bp = Blueprint('producto', __name__, url_prefix='/producto')

# ---- Decorador login_required ----
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---- Listar productos ----
@producto_bp.route("/")
@login_required
def index():
    productos = Producto.query.all()
    return render_template("productos.html", productos=productos)


# ---- Crear producto ----
@producto_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_producto():
    proveedores = Proveedor.query.all()
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = float(request.form["precio"])
        stock = int(request.form.get("stock", 0))
        id_proveedor = request.form.get("id_proveedor")
        pr = Producto(nombre=nombre, precio=precio, stock=stock, id_proveedor=id_proveedor)
        db.session.add(pr)
        db.session.commit()
        return redirect(url_for("producto.index"))   # 🔹 antes ibas al dashboard
    return render_template("nuevo_producto.html", proveedores=proveedores)


# ---- Editar producto ----
@producto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    pr = Producto.query.get_or_404(id)
    proveedores = Proveedor.query.all()
    if request.method == "POST":
        pr.nombre = request.form["nombre"]
        pr.precio = float(request.form["precio"])
        pr.stock = int(request.form.get("stock", 0))
        pr.id_proveedor = request.form.get("id_proveedor")
        db.session.commit()
        return redirect(url_for("producto.index"))   # 🔹 vuelve al listado de productos
    return render_template("editar_producto.html", producto=pr, proveedores=proveedores)


# ---- Eliminar producto ----
@producto_bp.route("/eliminar/<int:id>", methods=["POST"])  # usar POST es más seguro
@login_required
def eliminar_producto(id):
    pr = Producto.query.get_or_404(id)
    db.session.delete(pr)
    db.session.commit()
    return redirect(url_for("producto.index"))
