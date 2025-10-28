from flask import Flask, redirect, url_for, session, render_template, request, flash
from datetime import timedelta
from extensions import db
from models import Proveedor, Producto, Cliente, Tienda, Inventario, Venta, DetalleVenta, Usuario

# Se importan Blueprints
from routes.auth import auth_bp
from routes.proveedor import proveedor_bp
from routes.producto import producto_bp
from routes.cliente import cliente_bp
from routes.tienda import tienda_bp
from routes.inventario import inventario_bp
from routes.venta import venta_bp
from routes.detalle import detalle_bp
from routes.reportes import reportes_bp

# -------------------------------
# CONFIGURACIÓN BASE DE LA APP
# -------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/inventario_pymes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Tiempo máximo de inactividad antes de cerrar sesión
app.permanent_session_lifetime = timedelta(minutes=5)

# -------------------------------
# RENOVAR SESIÓN AUTOMÁTICAMENTE
# -------------------------------
@app.before_request
def make_session_permanent():
    """Renueva el tiempo de sesión en cada request"""
    session.permanent = True

# -------------------------------
# CONTROL DE ACCESO GLOBAL POR ROL
# -------------------------------
@app.before_request
def restringir_acceso_por_rol():
    """
    Limita los módulos visibles según el rol.
    - administrador: acceso total
    - usuario: solo tienda, inventario, reportes
    """

    # Si no hay endpoint (por ejemplo, 404 intermedio), no hacer nada
    if request.endpoint is None:
        return

    # --- EXCEPCIONES PÚBLICAS ---
    # 1) Archivos estáticos y favicon
    if request.endpoint == "static" or request.path.startswith("/static/") or request.path == "/favicon.ico":
        return

    # 2) Todo el blueprint de auth (login, register, logout, etc.)
    if request.blueprint == "auth":
        return
    
    # --- VERIFICAR LOGIN ---
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # --- CONTROL POR ROL ---
    rol = (session.get("rol") or "").lower()
    bp = request.blueprint  
    endpoint = request.endpoint

    # Administrador: acceso completo
    if rol == "administrador":
        return

    # Usuario: solo blueprints permitidos
    allowed_for_usuario = {"tienda", "inventario", "reportes"}

    if rol == "usuario":
        # permite dashboard (sin blueprint)
        if bp is None and endpoint == "dashboard":
            return
        if bp not in allowed_for_usuario:
            flash("No tienes permisos para acceder a este módulo.", "warning")
            return redirect(url_for("dashboard"))

    # Rol desconocido: restringido
    if bp not in allowed_for_usuario and not (bp is None and endpoint == "dashboard"):
        flash("No tienes permisos para acceder a este módulo.", "warning")
        return redirect(url_for("dashboard"))


# -------------------------------
# INICIALIZAR BASE DE DATOS
# -------------------------------
db.init_app(app)

# -------------------------------
# REGISTRAR BLUEPRINTS
# -------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(producto_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(tienda_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(venta_bp)
app.register_blueprint(detalle_bp)
app.register_blueprint(reportes_bp)


# -------------------------------
# DECORADOR login_required
# -------------------------------
def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


# -------------------------------
# DASHBOARD PRINCIPAL
# -------------------------------
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    """Panel principal con estadísticas generales"""
    pr_inventarios = {}
    inventarios = Inventario.query.all()
    for inv in inventarios:
        pr_inventarios[inv.id_producto] = pr_inventarios.get(inv.id_producto, 0) + inv.cantidad

    return render_template(
        "dashboard.html",
        proveedores=Proveedor.query.all(),
        productos=Producto.query.all(),
        clientes=Cliente.query.all(),
        tiendas=Tienda.query.all(),
        inventarios=inventarios,
        ventas=Venta.query.all(),
        detalleventas=DetalleVenta.query.all(),
        pr_inventarios=pr_inventarios
    )


# -------------------------------
# EJECUCIÓN
# -------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crea tablas si no existen
    app.run(debug=True)
