from extensions import db
from datetime import date
from sqlalchemy import event
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------
# MODELO USUARIO
# -------------------
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default="usuario")  # usuario | administrador

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # ✅ Manejo de hashes vacíos o inválidos para evitar ValueError
        if not self.password_hash:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

# -------------------
# MODELOS INVENTARIO
# -------------------

class Proveedor(db.Model):
    __tablename__ = 'Proveedor'
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    contacto = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __repr__(self):
        return f"<Proveedor {self.nombre}>"

class Producto(db.Model):
    __tablename__ = 'Producto'
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)

    id_proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.id_proveedor'))
    proveedor = db.relationship(
        "Proveedor",
        backref=db.backref("productos", cascade="all, delete-orphan")
    )

    __table_args__ = (
        db.CheckConstraint('precio >= 0', name='check_precio_no_negativo'),
        db.CheckConstraint('stock >= 0', name='check_stock_no_negativo'),
        db.Index('idx_producto_nombre', 'nombre'),
    )

    def __repr__(self):
        return f"<Producto {self.nombre} ${self.precio} Stock:{self.stock}>"

class Cliente(db.Model):
    __tablename__ = 'Cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    telefono = db.Column(db.String(20))

    def __repr__(self):
        return f"<Cliente {self.nombre}>"

class Tienda(db.Model):
    __tablename__ = 'Tienda'
    id_tienda = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(150))

    def __repr__(self):
        return f"<Tienda {self.nombre}>"

class Inventario(db.Model):
    __tablename__ = 'Inventario'
    id_inventario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cantidad = db.Column(db.Integer, nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Producto.id_producto'), nullable=False)
    id_tienda = db.Column(db.Integer, db.ForeignKey('Tienda.id_tienda'), nullable=False)
    producto = db.relationship("Producto")
    tienda = db.relationship("Tienda")

    __table_args__ = (
        db.CheckConstraint('cantidad >= 0', name='check_inventario_cantidad_no_negativa'),
        db.UniqueConstraint('id_producto', 'id_tienda', name='uq_producto_tienda'),
    )

    def __repr__(self):
        return f"<Inventario prod:{self.id_producto} tienda:{self.id_tienda} cant:{self.cantidad}>"

class Venta(db.Model):
    __tablename__ = 'Venta'
    id_venta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    id_cliente = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    cliente = db.relationship("Cliente", backref="ventas")

    id_tienda = db.Column(db.Integer, db.ForeignKey('Tienda.id_tienda'), nullable=False)
    tienda = db.relationship("Tienda", backref="ventas")

    detalles = db.relationship(
        "DetalleVenta",
        backref="venta",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Venta #{self.id_venta} total:{self.total}>"

class DetalleVenta(db.Model):
    __tablename__ = 'DetalleVenta'
    id_detalle = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    id_venta = db.Column(db.Integer, db.ForeignKey('Venta.id_venta', ondelete="CASCADE"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Producto.id_producto'), nullable=False)
    producto = db.relationship("Producto")

    __table_args__ = (
        db.CheckConstraint('cantidad > 0', name='check_detalle_cantidad_positiva'),
        db.CheckConstraint('subtotal >= 0', name='check_detalle_subtotal_no_negativo'),
    )

    def __repr__(self):
        return f"<DetVenta venta:{self.id_venta} prod:{self.id_producto} cant:{self.cantidad} sub:{self.subtotal}>"

# Recalcular total de venta automáticamente
@event.listens_for(Venta.detalles, 'append')
@event.listens_for(Venta.detalles, 'remove')
def _recalcular_total(_target, _value, _initiator):
    venta = _target if isinstance(_target, Venta) else _value.venta
    if venta and venta.detalles:
        venta.total = sum(d.subtotal for d in venta.detalles)
    elif venta:
        venta.total = 0
