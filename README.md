Proyecto Nómina de Personal

Este proyecto es una aplicación desarrollada en Python (Tkinter + CustomTkinter) para la gestión de empleados y la generación de nóminas.
El entorno gráfico se ejecuta dentro de un contenedor Docker con soporte para noVNC, permitiendo acceder a la interfaz desde el navegador.

Requisitos previos

Tener instalado Docker Desktop

Conexión a internet para descargar las dependencias

Clonar el repositorio
git clone https://github.com/Morales-Xavier/Nomina-Personal.git
cd Nomina-Personal

Construir la imagen

Ejecuta el siguiente comando en la raíz del proyecto:

docker build -t nomina-personal .

Ejecutar el contenedor

Para iniciar el sistema:

docker run -d -p 6901:6901 --name nomina nomina-personal

Acceso a la aplicación

Abre tu navegador en:
http://localhost:6901

Desde ahí se carga la aplicación gráfica de la Nómina de Personal.

NOTAS

Si el puerto 6901 ya está en uso, cambia el mapeo con otro número (ejemplo: -p 6902:6901).

El archivo empleados.db se incluye como ejemplo; se puede reemplazar por otra base de datos según necesidad.

Para detener el contenedor:

docker stop nomina

Para eliminarlo completamente:

docker rm nomina
