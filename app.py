# app.py
from flask import Flask, redirect, url_for, session, render_template, request, flash
from datetime import timedelta, date, datetime   
from extensions import db
from models import Proveedor, Producto, Cliente, Tienda, Inventario, Venta, DetalleVenta, Usuario

# Blueprints
from routes.auth import auth_bp
from routes.proveedor import proveedor_bp
from routes.producto import producto_bp
from routes.cliente import cliente_bp
from routes.tienda import tienda_bp
from routes.inventario import inventario_bp
from routes.venta import venta_bp
from routes.detalle import detalle_bp
from routes.reportes import reportes_bp

# --------------------------------
# Configuración de la aplicación
# --------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey123"  # ⚠️ cámbiala a un valor seguro en producción

# Base de datos: inventario_pymes (MySQL)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/inventario_pymes"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(minutes=10)

# Inicializar DB
db.init_app(app)

# --------------------------------
# Inyectar date/datetime en TODAS las plantillas 
# --------------------------------
@app.context_processor
def inject_datetime():
    # Disponibles en Jinja: {{ date }} y {{ datetime }}
    return {"date": date, "datetime": datetime}

# --------------------------------
# Filtro Jinja para CLP
# --------------------------------
@app.template_filter("clp")
def formato_clp(value):
    """
    Formatea un número a CLP: $1.234 CLP
    Acepta int, float, Decimal o str numérico.
    """
    from decimal import Decimal, InvalidOperation
    try:
        v = Decimal(str(value))
        # Redondeo a entero de CLP
        entero = int(v.to_integral_value(rounding="ROUND_HALF_UP"))
        # Separador miles con punto
        return f"${entero:,} CLP".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        # Si no se puede formatear, lo devuelve tal cual
        return f"${value} CLP"

# --------------------------------
# Control de sesión y roles
# --------------------------------
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.before_request
def restringir_acceso_por_rol():
    """
    - Permite recursos estáticos y blueprint 'auth' sin login.
    - Si no hay login => redirige al login.
    - Rol 'administrador' => acceso completo.
    - Rol 'usuario' => solo 'tienda', 'inventario', 'reportes' + dashboard.
    """
    if request.endpoint is None:
        return

    # Archivos estáticos / favicon
    if request.endpoint == "static" or request.path.startswith("/static/") or request.path == "/favicon.ico":
        return

    # Autenticación (login, registro, logout, etc.)
    if request.blueprint == "auth":
        return

    # Verificar sesión
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Control por rol
    rol = (session.get("rol") or "").lower()
    bp = request.blueprint
    endpoint = request.endpoint

    if rol == "administrador":
        return

    allowed_for_usuario = {"tienda", "inventario", "reportes"}
    if rol == "usuario":
        # Permitir dashboard (sin blueprint)
        if bp is None and endpoint == "dashboard":
            return
        if bp not in allowed_for_usuario:
            flash("No tienes permisos para acceder a este módulo.", "warning")
            return redirect(url_for("dashboard"))

# --------------------------------
# Decorador login_required
# --------------------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------
# Rutas principales
# --------------------------------
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    """
    Panel principal con listados y acciones rápidas.
    Los montos en las plantillas pueden usarse como:
      {{ v.total|clp }}  ó  {{ (d.subtotal / d.cantidad)|clp }}
    """
    inventarios = Inventario.query.all()
    return render_template(
        "dashboard.html",
        proveedores=Proveedor.query.all(),
        productos=Producto.query.all(),
        clientes=Cliente.query.all(),
        tiendas=Tienda.query.all(),
        inventarios=inventarios,
        ventas=Venta.query.all(),
        detalleventas=DetalleVenta.query.all(),
    )

# --------------------------------
# Registrar Blueprints
# --------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(producto_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(tienda_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(venta_bp)
app.register_blueprint(detalle_bp)
app.register_blueprint(reportes_bp)

# --------------------------------
# Ejecutar app
# --------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crea tablas si no existen (útil en desarrollo)
    app.run(debug=True)
