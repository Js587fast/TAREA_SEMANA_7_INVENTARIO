from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Tienda
from functools import wraps

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')


# ---- Decorador para exigir login ----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para continuar", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---- Listar Tiendas ----
@tienda_bp.route("/")
@login_required
def index():
    tiendas = Tienda.query.all()
    return render_template("tiendas.html", tiendas=tiendas)


# ---- Crear Tienda ----
@tienda_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nueva_tienda():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        ubicacion = request.form.get("ubicacion")

        if not nombre:
            flash("⚠️ El nombre de la tienda es obligatorio.", "danger")
            return redirect(url_for("tienda.nueva_tienda"))

        nueva = Tienda(nombre=nombre, ubicacion=ubicacion)
        db.session.add(nueva)
        db.session.commit()
        flash("✅ Tienda registrada correctamente", "success")
        return redirect(url_for("tienda.index"))

    return render_template("nueva_tienda.html")


# ---- Editar Tienda ----
@tienda_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_tienda(id):
    t = Tienda.query.get_or_404(id)

    if request.method == "POST":
        t.nombre = request.form.get("nombre")
        t.ubicacion = request.form.get("ubicacion")

        if not t.nombre:
            flash("⚠️ El nombre de la tienda es obligatorio.", "danger")
            return redirect(url_for("tienda.editar_tienda", id=id))

        db.session.commit()
        flash("✅ Tienda actualizada correctamente", "success")
        return redirect(url_for("tienda.index"))

    return render_template("editar_tienda.html", tienda=t)


# ---- Eliminar Tienda ----
@tienda_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_tienda(id):
    t = Tienda.query.get_or_404(id)

    try:
        db.session.delete(t)
        db.session.commit()
        flash("🗑️ Tienda eliminada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ No se pudo eliminar la tienda: {str(e)}", "danger")

    return redirect(url_for("tienda.index"))
