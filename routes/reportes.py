# inventario_pymes/routes/reportes.py
from flask import Blueprint, send_file, request, flash, redirect, url_for, session, render_template, make_response
from io import BytesIO, StringIO
import csv, json
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
from decimal import Decimal

from models import db, Inventario, Producto, Tienda, Venta, Cliente, Proveedor, DetalleVenta, Auditoria
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

# =====================================================
# ADMIN: RECALCULAR TOTALES + AUDITORÍA
# =====================================================

@reportes_bp.route("/admin/recalcular_totales", methods=["POST"])
@require_roles("administrador")
def admin_recalcular_totales():
    """
    Recalcula:
      - DetalleVenta.subtotal = cantidad * Producto.precio (precio actual)
      - Venta.total = SUM(DetalleVenta.subtotal)
    y registra auditoría con conteos.
    """
    try:
        # 1) Recalcular subtotales
        detalles = DetalleVenta.query.all()
        detalles_tocados = len(detalles)
        detalles_actualizados = 0

        for d in detalles:
            precio = Decimal(str(d.producto.precio or 0))
            cantidad = Decimal(str(d.cantidad or 0))
            nuevo_subtotal = cantidad * precio
            anterior_subtotal = Decimal(str(d.subtotal or 0))

            if nuevo_subtotal != anterior_subtotal:
                d.subtotal = nuevo_subtotal
                detalles_actualizados += 1
                db.session.add(d)

        db.session.flush()  # asegurar lectura actualizada en v.detalles

        # 2) Recalcular totales por venta
        ventas = Venta.query.all()
        ventas_tocadas = len(ventas)
        ventas_actualizadas = 0

        for v in ventas:
            total_nuevo = sum(Decimal(str(det.subtotal or 0)) for det in v.detalles)
            total_anterior = Decimal(str(v.total or 0))
            if total_nuevo != total_anterior:
                v.total = total_nuevo
                ventas_actualizadas += 1
                db.session.add(v)

        # 3) Auditoría
        usuario_id = session.get("user_id")
        usuario_nombre = session.get("username") or session.get("email") or "desconocido"
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        audit = Auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion="recalcular_totales",
            detalles=(
                f"Detalles tocados={detalles_tocados}, act={detalles_actualizados}; "
                f"Ventas tocadas={ventas_tocadas}, act={ventas_actualizadas}"
            ),
            detalles_json={
                "detalles_tocados": detalles_tocados,
                "detalles_actualizados": detalles_actualizados,
                "ventas_tocadas": ventas_tocadas,
                "ventas_actualizadas": ventas_actualizadas,
            },
            ip=ip,
        )
        db.session.add(audit)
        db.session.commit()

        flash(
            f"✅ Recalculo completado. "
            f"Detalles tocados: {detalles_tocados}, actualizados: {detalles_actualizados}. "
            f"Ventas tocadas: {ventas_tocadas}, actualizadas: {ventas_actualizadas}.",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ No se pudo recalcular: {str(e)}", "danger")

    return redirect(url_for("dashboard"))

# =====================================================
# ADMIN: AUDITORÍA (vista y CSV)
# =====================================================

@reportes_bp.route("/admin/auditoria")
@require_roles("administrador")
def ver_auditoria():
    logs = Auditoria.query.order_by(Auditoria.fecha_hora.desc()).limit(200).all()
    return render_template("auditoria.html", logs=logs)

@reportes_bp.route("/admin/auditoria.csv")
@require_roles("administrador")
def descargar_auditoria_csv():
    logs = Auditoria.query.order_by(Auditoria.fecha_hora.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha_hora","usuario_id","usuario_nombre","accion","detalles","detalles_json","ip"])
    for l in logs:
        writer.writerow([
            l.fecha_hora,
            l.usuario_id or "",
            l.usuario_nombre or "",
            l.accion,
            (l.detalles or "").replace("\n", " ").strip(),
            json.dumps(l.detalles_json, ensure_ascii=False) if l.detalles_json else "",
            l.ip or "",
        ])

    resp = make_response(output.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename=auditoria.csv"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp
