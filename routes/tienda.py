from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Tienda
from utils.security import require_roles  # 🔐 control de roles

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')


# ---- Listar Tiendas (visible para usuario y administrador) ----
@tienda_bp.route("/")
@require_roles('usuario', 'administrador')
def index():
    tiendas = Tienda.query.all()
    return render_template("tiendas.html", tiendas=tiendas)


# ---- Crear Tienda (solo administrador) ----
@tienda_bp.route("/nuevo", methods=["GET", "POST"])
@require_roles('administrador')
def nueva_tienda():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        ubicacion = request.form.get("ubicacion", "").strip()
        contacto = request.form.get("contacto", "").strip()
        email = request.form.get("email", "").strip()

        if not nombre:
            flash("⚠️ El nombre de la tienda es obligatorio.", "warning")
            return redirect(url_for("tienda.nueva_tienda"))

        nueva = Tienda(
            nombre=nombre,
            ubicacion=ubicacion,
            contacto=contacto,
            email=email
        )
        db.session.add(nueva)
        db.session.commit()

        flash(f"✅ Tienda «{nombre}» registrada correctamente.", "success")
        return redirect(url_for("tienda.index"))

    return render_template("nueva_tienda.html")


# ---- Editar Tienda (solo administrador) ----
@tienda_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@require_roles('administrador')
def editar_tienda(id):
    t = Tienda.query.get_or_404(id)

    if request.method == "POST":
        t.nombre = request.form.get("nombre", "").strip()
        t.ubicacion = request.form.get("ubicacion", "").strip()
        t.contacto = request.form.get("contacto", "").strip()
        t.email = request.form.get("email", "").strip()

        if not t.nombre:
            flash("⚠️ El nombre de la tienda es obligatorio.", "warning")
            return redirect(url_for("tienda.editar_tienda", id=id))

        db.session.commit()
        flash(f"✅ Tienda «{t.nombre}» actualizada correctamente.", "success")
        return redirect(url_for("tienda.index"))

    return render_template("editar_tienda.html", tienda=t)


# ---- Eliminar Tienda (solo administrador, por POST) ----
@tienda_bp.route("/eliminar/<int:id>", methods=["POST"])
@require_roles('administrador')
def eliminar_tienda(id):
    t = Tienda.query.get_or_404(id)
    try:
        db.session.delete(t)
        db.session.commit()
        flash(f"🗑️ Tienda «{t.nombre}» eliminada correctamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ No se pudo eliminar la tienda: {str(e)}", "danger")

    return redirect(url_for("tienda.index"))
