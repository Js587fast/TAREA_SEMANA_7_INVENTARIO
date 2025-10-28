Inventario PYMES – Tarea Semana 9

Sistema de administración de inventario orientado a pequeñas y medianas empresas, desarrollado con Python (Flask), MySQL y SQLAlchemy. Forma parte de las entregas semanales del proyecto académico Inventario PYMES.

Objetivo:

Optimizar la gestion de inventarios, ventas, clientes, proveedores y tiendas a través de una interfaz web dinámica con autenticación y control de roles (Administrador / Usuario).

Estructura del proyecto:
inventario_pymes/
├── app.py
├── models.py
├── extensions.py
├── utils/security.py
├── routes/
│   ├── auth.py
│   ├── cliente.py
│   ├── proveedor.py
│   ├── producto.py
│   ├── tienda.py
│   ├── inventario.py
│   ├── venta.py
│   ├── detalle.py
│   └── reportes.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── inventarios.html
│   └── ...
├── static/
│   ├── css/style.css
│   └── imagenes/imagen_fondo.jpg
└── tests/ui_test.py



Tecnologías:

Componente	Tecnología
Lenguaje	Python 3.12
Framework	Flask
ORM	SQLAlchemy
Base de datos	MySQL
Frontend	HTML5, CSS3, Bootstrap 5
Control de versiones	Git + GitHub

Funcionalidades principales:

•	 Login y autenticación de usuarios.
•	 Control de inventario y actualización automática de stock.
•	 Administración de clientes, proveedores, productos y tiendas.
•	 Generación de reportes en PDF y Excel.
•	 Interfaz moderna y responsiva.
•	 Roles de usuario: Administrador / Usuario.

Ejecución local:

1.	1. Clonar el repositorio: git clone https://github.com/Js587fast/TAREA_SEMANA_9_INVENTARIO.git
2.	2. Crear entorno virtual e instalar dependencias: python -m venv venv, venv\Scripts\activate, pip install -r requirements.txt
3.	3. Ejecutar el proyecto: flask run
4.	4. Abrir en el navegador: http://127.0.0.1:5000

Autor: Juan Silva
Repositorio: https://github.com/Js587fast/TAREA_SEMANA_9_INVENTARIO
