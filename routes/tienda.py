from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Tienda

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@tienda_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nueva_tienda():
    if request.method == "POST":
        nombre = request.form["nombre"]
        ubicacion = request.form.get("ubicacion")
        t = Tienda(nombre=nombre, ubicacion=ubicacion)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("nueva_tienda.html")

@tienda_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_tienda(id):
    t = Tienda.query.get_or_404(id)
    if request.method == "POST":
        t.nombre = request.form["nombre"]
        t.ubicacion = request.form.get("ubicacion")
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("editar_tienda.html", tienda=t)

@tienda_bp.route("/eliminar/<int:id>")
@login_required
def eliminar_tienda(id):
    t = Tienda.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for("dashboard"))
