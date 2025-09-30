from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Proveedor(db.Model):
    __tablename__ = 'Proveedor'
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))


class Producto(db.Model):
    __tablename__ = 'Producto'
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.id_proveedor'))
    proveedor = db.relationship("Proveedor", backref="productos")


class Cliente(db.Model):
    __tablename__ = 'Cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    telefono = db.Column(db.String(20))


class Tienda(db.Model):
    __tablename__ = 'Tienda'
    id_tienda = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(150))


class Inventario(db.Model):
    __tablename__ = 'Inventario'
    id_inventario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cantidad = db.Column(db.Integer, nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Producto.id_producto'), nullable=False)
    id_tienda = db.Column(db.Integer, db.ForeignKey('Tienda.id_tienda'), nullable=False)
    producto = db.relationship("Producto")
    tienda = db.relationship("Tienda")


class Venta(db.Model):
    __tablename__ = 'Venta'
    id_venta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relaciones
    id_cliente = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    cliente = db.relationship("Cliente", backref="ventas")

    # Nueva relación con Tienda
    id_tienda = db.Column(db.Integer, db.ForeignKey('Tienda.id_tienda'), nullable=False)
    tienda = db.relationship("Tienda", backref="ventas")


class DetalleVenta(db.Model):
    __tablename__ = 'DetalleVenta'
    id_detalle = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    id_venta = db.Column(db.Integer, db.ForeignKey('Venta.id_venta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Producto.id_producto'), nullable=False)
    venta = db.relationship("Venta", backref="detalles")
    producto = db.relationship("Producto")
