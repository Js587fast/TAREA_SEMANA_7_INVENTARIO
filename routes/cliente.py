from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Cliente
from utils.security import require_roles  # 🔐 Control de roles

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')


# ---- Listar clientes (solo administradores) ----
@cliente_bp.route("/")
@require_roles('administrador')
def index():
    clientes = Cliente.query.all()
    return render_template("clientes.html", clientes=clientes)


# ---- Crear cliente (solo administradores) ----
@cliente_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre:
            flash("El nombre del cliente es obligatorio.", "warning")
            return redirect(url_for("cliente.nuevo_cliente"))

        nuevo = Cliente(nombre=nombre, email=email, telefono=telefono)
        db.session.add(nuevo)
        db.session.commit()
        flash("Cliente creado correctamente ✅", "success")
        return redirect(url_for("cliente.index"))

    return render_template("nuevo_cliente.html")


# ---- Editar cliente (solo administradores) ----
@cliente_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@require_roles('administrador')
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    if request.method == "POST":
        cliente.nombre = request.form.get("nombre", "").strip()
        cliente.email = request.form.get("email", "").strip()
        cliente.telefono = request.form.get("telefono", "").strip()

        db.session.commit()
        flash("Cliente actualizado correctamente ✅", "success")
        return redirect(url_for("cliente.index"))

    return render_template("editar_cliente.html", cliente=cliente)


# ---- Eliminar cliente (solo administradores, usando POST) ----
@cliente_bp.route("/eliminar/<int:id>", methods=["POST"])
@require_roles('administrador')
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado correctamente ✅", "success")
    return redirect(url_for("cliente.index"))
