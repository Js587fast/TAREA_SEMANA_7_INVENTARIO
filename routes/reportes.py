from flask import Blueprint, send_file, request
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from models import db, Inventario, Producto, Tienda, Venta, Cliente, Proveedor

reportes_bp = Blueprint('reportes', __name__)

# ======= Funciones para obtener datos usando SQLAlchemy =======
def obtener_datos_inventario():
    data = db.session.query(
        Inventario.id_inventario.label("ID"),
        Producto.nombre.label("Producto"),
        Tienda.nombre.label("Tienda"),
        Inventario.cantidad.label("Cantidad")
    ).join(Producto, Inventario.id_producto == Producto.id_producto
    ).join(Tienda, Inventario.id_tienda == Tienda.id_tienda
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_ventas():
    data = db.session.query(
        Venta.id_venta.label("ID"),
        Venta.fecha.label("Fecha"),
        Venta.total.label("Total"),
        Cliente.nombre.label("Cliente")
    ).join(Cliente, Venta.id_cliente == Cliente.id_cliente
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_clientes():
    data = db.session.query(
        Cliente.id_cliente.label("ID"),
        Cliente.nombre.label("Nombre"),
        Cliente.email.label("Email"),
        Cliente.telefono.label("Telefono")
    ).all()
    return [dict(row._mapping) for row in data]

def obtener_datos_proveedores():
    data = db.session.query(
        Proveedor.id_proveedor.label("ID"),
        Proveedor.nombre.label("Nombre"),
        Proveedor.contacto.label("Contacto")
    ).all()
    return [dict(row._mapping) for row in data]

# ======= Funciones para generar Excel y PDF =======
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
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, titulo)

    # Encabezados
    c.setFont("Helvetica-Bold", 12)
    y = height - 100
    x_positions = [50, 150, 300, 450, 600]  # Ajusta según columnas

    for idx, key in enumerate(data[0].keys() if data else []):
        c.drawString(x_positions[idx], y, key)
    y -= 20

    # Contenido
    c.setFont("Helvetica", 12)
    for row in data:
        for idx, value in enumerate(row.values()):
            c.drawString(x_positions[idx], y, str(value))
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# ======= Función para crear rutas de reportes =======
def crear_ruta_reporte(nombre, funcion_datos, titulo):
    @reportes_bp.route(f'/reporte/{nombre}')
    def reporte():
        formato = request.args.get('formato', 'excel')
        data = funcion_datos()
        if formato.lower() == 'pdf':
            pdf = generar_pdf(data, titulo=titulo)
            return send_file(pdf, download_name=f"reporte_{nombre}.pdf", as_attachment=True)
        else:
            excel = generar_excel(data)
            return send_file(excel, download_name=f"reporte_{nombre}.xlsx", as_attachment=True)
    reporte.__name__ = f"reporte_{nombre}"
    return reporte

# ======= Crear rutas =======
crear_ruta_reporte("inventario", obtener_datos_inventario, "Reporte de Inventario")
crear_ruta_reporte("ventas", obtener_datos_ventas, "Reporte de Ventas")
crear_ruta_reporte("clientes", obtener_datos_clientes, "Reporte de Clientes")
crear_ruta_reporte("proveedores", obtener_datos_proveedores, "Reporte de Proveedores")
