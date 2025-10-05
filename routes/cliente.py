from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Cliente

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# ---- NUEVO: Listar clientes ----
@cliente_bp.route("/")
@login_required
def index():
    clientes = Cliente.query.all()
    return render_template("clientes.html", clientes=clientes)

# ---- Crear cliente ----
@cliente_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        c = Cliente(nombre=nombre, email=email, telefono=telefono)
        db.session.add(c)
        db.session.commit()
        flash("Cliente creado correctamente ✅", "success")
        return redirect(url_for("cliente.index"))
    return render_template("nuevo_cliente.html")

# ---- Editar cliente ----
@cliente_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cliente(id):
    c = Cliente.query.get_or_404(id)
    if request.method == "POST":
        c.nombre = request.form["nombre"]
        c.email = request.form.get("email")
        c.telefono = request.form.get("telefono")
        db.session.commit()
        flash("Cliente actualizado correctamente ✅", "success")
        return redirect(url_for("cliente.index"))
    return render_template("editar_cliente.html", cliente=c)

# ---- Eliminar cliente ----
@cliente_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_cliente(id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Cliente eliminado correctamente ✅", "success")
    return redirect(url_for("cliente.index"))
