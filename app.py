from flask import Flask, redirect, url_for, session, render_template
from datetime import timedelta
from extensions import db
from models import Proveedor, Producto, Cliente, Tienda, Inventario, Venta, DetalleVenta, Usuario

# Importar Blueprints
from routes.auth import auth_bp
from routes.proveedor import proveedor_bp
from routes.producto import producto_bp
from routes.cliente import cliente_bp
from routes.tienda import tienda_bp
from routes.inventario import inventario_bp
from routes.venta import venta_bp
from routes.detalle import detalle_bp
from routes.reportes import reportes_bp

app = Flask(__name__)
app.secret_key = "supersecretkey123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/inventario_pymes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Tiempo máximo de inactividad antes de cerrar sesión
app.permanent_session_lifetime = timedelta(minutes=5)

@app.before_request
def make_session_permanent():
    # Cada request renueva el tiempo de sesión
    session.permanent = True

# Inicializar DB
db.init_app(app)

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(producto_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(tienda_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(venta_bp)
app.register_blueprint(detalle_bp)
app.register_blueprint(reportes_bp)

# Decorador login_required
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    # --- Se calcula el stock total de cada producto ---
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crea tablas si no existen
    app.run(debug=True)
