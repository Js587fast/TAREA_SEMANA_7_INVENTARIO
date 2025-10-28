# inventario_pymes/routes/reportes.py
from flask import Blueprint, send_file, request, flash
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
from models import db, Inventario, Producto, Tienda, Venta, Cliente, Proveedor, DetalleVenta
from utils.security import require_roles  # 🔐 permitir usuario/administrador

reportes_bp = Blueprint('reportes', __name__)

# =====================================================
# FUNCIONES PARA OBTENER DATOS
# =====================================================

def obtener_datos_inventario():
    """Inventario completo con producto y tienda."""
    data = db.session.query(
        Inventario.id_inventario.label("ID"),
        Producto.nombre.label("Producto"),
        Tienda.nombre.label("Tienda"),
        Inventario.cantidad.label("Cantidad Disponible")
    ).join(
        Producto, Inventario.id_producto == Producto.id_producto
    ).join(
        Tienda, Inventario.id_tienda == Tienda.id_tienda
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_ventas():
    """Ventas con cliente y total."""
    data = db.session.query(
        Venta.id_venta.label("ID Venta"),
        Venta.fecha.label("Fecha"),
        Venta.total.label("Total CLP"),
        Cliente.nombre.label("Cliente")
    ).join(
        Cliente, Venta.id_cliente == Cliente.id_cliente
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_clientes():
    """Clientes registrados."""
    data = db.session.query(
        Cliente.id_cliente.label("ID Cliente"),
        Cliente.nombre.label("Nombre"),
        Cliente.email.label("Email"),
        Cliente.telefono.label("Teléfono")
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_proveedores():
    """Proveedores registrados."""
    data = db.session.query(
        Proveedor.id_proveedor.label("ID Proveedor"),
        Proveedor.nombre.label("Nombre"),
        Proveedor.contacto.label("Contacto")
    ).all()
    return [dict(row._mapping) for row in data]

def _parse_fecha(value):
    """Parsea YYYY-MM-DD a date. Retorna None si es inválida."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None

def obtener_detalle_ventas(fecha_inicio=None, fecha_fin=None, cliente=None):
    """
    Detalle de ventas con filtros opcionales.
    fecha_inicio/fin: date | None
    cliente: int | None
    """
    query = db.session.query(
        DetalleVenta.id_detalle.label("ID Detalle"),
        Venta.id_venta.label("ID Venta"),
        Cliente.nombre.label("Cliente"),
        Tienda.nombre.label("Tienda"),
        Producto.nombre.label("Producto"),
        DetalleVenta.cantidad.label("Cantidad"),
        (DetalleVenta.subtotal / DetalleVenta.cantidad).label("Precio Unitario CLP"),
        DetalleVenta.subtotal.label("Subtotal CLP"),
        Venta.fecha.label("Fecha Venta")
    ).join(
        Venta, DetalleVenta.id_venta == Venta.id_venta
    ).join(
        Cliente, Venta.id_cliente == Cliente.id_cliente
    ).join(
        Tienda, Venta.id_tienda == Tienda.id_tienda
    ).join(
        Producto, DetalleVenta.id_producto == Producto.id_producto
    )

    if fecha_inicio:
        query = query.filter(Venta.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Venta.fecha <= fecha_fin)
    if cliente:
        query = query.filter(Venta.id_cliente == cliente)

    data = query.all()
    return [dict(row._mapping) for row in data]

# =====================================================
# FUNCIONES PARA GENERAR ARCHIVOS
# =====================================================

def generar_excel(data):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    output.seek(0)
    return output

def generar_pdf(data, titulo="Reporte"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 50, titulo)

    if not data:
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, "No hay datos para mostrar")
        c.save()
        buffer.seek(0)
        return buffer

    # Encabezados dinámicos
    keys = list(data[0].keys())
    c.setFont("Helvetica-Bold", 9)
    y = height - 80
    x_positions = [50 + (i * 100) for i in range(len(keys))]

    for idx, key in enumerate(keys):
        if idx < len(x_positions):
            c.drawString(x_positions[idx], y, str(key))
    y -= 15

    # Contenido
    c.setFont("Helvetica", 8)
    for row in data:
        for idx, value in enumerate(row.values()):
            if idx < len(x_positions):
                c.drawString(x_positions[idx], y, str(value))
        y -= 12
        if y < 40:  # salto de página
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 9)
            for idx, key in enumerate(keys):
                if idx < len(x_positions):
                    c.drawString(x_positions[idx], y, str(key))
            y -= 15
            c.setFont("Helvetica", 8)

    c.save()
    buffer.seek(0)
    return buffer

# =====================================================
# GENERADOR DE RUTAS CON CONTROL DE ROLES
# =====================================================

def crear_ruta_reporte(nombre, funcion_datos, titulo, con_filtros=False):
    @reportes_bp.route(f'/reporte/{nombre}')
    @require_roles('usuario', 'administrador')  # ambos roles pueden generar reportes
    def reporte():
        formato = (request.args.get('formato') or 'excel').lower()

        if con_filtros:
            # Parseo seguro de filtros
            fecha_inicio = _parse_fecha(request.args.get('fecha_inicio'))
            fecha_fin = _parse_fecha(request.args.get('fecha_fin'))
            cliente_raw = request.args.get('cliente')
            cliente = None
            try:
                cliente = int(cliente_raw) if cliente_raw else None
            except Exception:
                cliente = None

            data = funcion_datos(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                cliente=cliente
            )
        else:
            data = funcion_datos()

        if formato == 'pdf':
            pdf = generar_pdf(data, titulo=titulo)
            return send_file(pdf, download_name=f"reporte_{nombre}.pdf", as_attachment=True)
        else:  # default: excel
            excel = generar_excel(data)
            return send_file(excel, download_name=f"reporte_{nombre}.xlsx", as_attachment=True)

    # Asegurar endpoint único
    reporte.__name__ = f"reporte_{nombre}"
    return reporte

# =====================================================
# CREAR TODAS LAS RUTAS DISPONIBLES
# =====================================================
crear_ruta_reporte("inventario", obtener_datos_inventario, "Reporte de Inventario")
crear_ruta_reporte("ventas", obtener_datos_ventas, "Reporte de Ventas")
crear_ruta_reporte("clientes", obtener_datos_clientes, "Reporte de Clientes")
crear_ruta_reporte("proveedores", obtener_datos_proveedores, "Reporte de Proveedores")
crear_ruta_reporte("detalle_ventas", obtener_detalle_ventas, "Detalle de Ventas", con_filtros=True)
