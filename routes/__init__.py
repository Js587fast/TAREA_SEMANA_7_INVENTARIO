from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Proveedor, Producto, Cliente, Tienda, Inventario, Venta, DetalleVenta


