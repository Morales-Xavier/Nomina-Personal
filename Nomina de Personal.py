import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import requests
import pyBCV
import xlsxwriter
from tkinter import filedialog
import os
import traceback
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta







ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# -------------------------------------------------
# Inicializar BD
# -------------------------------------------------
def inicializar_bd():
    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL
        )
    """)
    
    cursor.execute("DELETE FROM empresas")

    
    cursor.execute("INSERT INTO empresas (nombre, contrasena) VALUES (?, ?)",
                       ("Inversiones Alejandr@ 2012", "Alejandr@2012"))
   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cargo TEXT,
            salario REAL
        )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nominas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        total_bs REAL NOT NULL,
        total_usd REAL NOT NULL
    )
""")

    conn.commit()
    conn.close()


def verificar_login_db(nombre, contrasena):
    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empresas WHERE nombre=? AND contrasena=?", (nombre, contrasena))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None


# -------------------------------------------------
# Función GLOBAL para cargar la nómina
# -------------------------------------------------

def obtener_tasa_bcv():
    try:
        bcv = pyBCV.Currency()
        tasa = bcv.get_rate('USD')  
        return float(tasa)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo obtener la tasa del BCV:\n{e}")
        return 0.0



def cargar_nomina(tabla_nomina, total_label, tasa_label, total_usd_label):
    tabla_nomina.delete(*tabla_nomina.get_children())
    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT cedula, nombre, cargo, salario FROM empleados")
    total = 0
    for row in cursor.fetchall():
        try:
            salario = float(str(row[3]).replace(" Bs.", "").strip())
            semanal = salario / 4
            tabla_nomina.insert("", "end", values=(row[0], row[1], row[2], f"{semanal:.2f} Bs."))
            total += semanal
        except ValueError:
            tabla_nomina.insert("", "end", values=row)

    conn.close()


    # obtener tasa BCV
    tasa = obtener_tasa_bcv()
    tasa_label.configure(text=f"Tasa BCV: {tasa:.2f} Bs/$")


    #Calcula el total en dolares
    if tasa > 0:
        total_usd = total / tasa
        total_usd_label.configure(text=f"Equivalente en Dólares: {total_usd:.2f} $")
    else:
        total_usd_label.configure(text="Equivalente en Dólares: Error")

    total_label.configure(text=f"Total General de Sueldos: {total:.2f} Bs.")
    
    
    # Fuciones de la nomina # 
    
def crear_nomina(tabla_nomina):
    fecha_inicio_str = simpledialog.askstring("Nueva Nómina", "Ingrese la fecha de inicio (dd/mm/aaaa):")
    if not fecha_inicio_str:
        return
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%d/%m/%Y")
        fecha_fin = fecha_inicio + timedelta(days=6)
        fecha_fin_str = fecha_fin.strftime("%d/%m/%Y")
    except:
        messagebox.showerror("Error", "Formato de fecha inválido. Use dd/mm/aaaa")
        return

    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO nominas (fecha_inicio, fecha_fin) VALUES (?, ?)", 
                   (fecha_inicio_str, fecha_fin_str))
    nomina_id = cursor.lastrowid

    # Calcular sueldo semanal de cada empleado
    cursor.execute("SELECT id, salario FROM empleados")
    for emp in cursor.fetchall():
        emp_id, salario = emp
        try:
            salario = float(str(salario).replace(" Bs.", "").strip())
            semanal = salario / 4
            cursor.execute("INSERT INTO detalle_nomina (nomina_id, empleado_id, sueldo_semanal) VALUES (?,?,?)",
                           (nomina_id, emp_id, semanal))
        except:
            continue
    conn.commit()
    conn.close()

    messagebox.showinfo("Éxito", f"Nómina creada del {fecha_inicio_str} al {fecha_fin_str}")
    mostrar_nomina_por_fecha(tabla_nomina, fecha_inicio_str)

    
def mostrar_nomina_por_fecha(tabla_nomina, fecha_inicio_str):
    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.cedula, e.nombre, e.cargo, d.sueldo_semanal
        FROM detalle_nomina d
        JOIN empleados e ON e.id = d.empleado_id
        JOIN nominas n ON n.id = d.nomina_id
        WHERE n.fecha_inicio = ?
    """, (fecha_inicio_str,))
    filas = cursor.fetchall()
    conn.close()
    
def buscar_nomina(tabla_nomina):
    fecha_inicio_str = simpledialog.askstring("Buscar Nómina", "Ingrese la fecha de inicio (dd/mm/aaaa):")
    if not fecha_inicio_str:
        return

def eliminar_nomina(tabla_nomina):
    fecha_inicio_str = simpledialog.askstring("Eliminar Nómina", "Ingrese la fecha de inicio (dd/mm/aaaa):")
    if not fecha_inicio_str:
        return

    confirm = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar la nómina con fecha {fecha_inicio_str}?")
    if not confirm:
        return

    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM nominas WHERE fecha_inicio=?", (fecha_inicio_str,))
    nomina = cursor.fetchone()
    if not nomina:
        messagebox.showwarning("No encontrada", f"No existe nómina con fecha {fecha_inicio_str}")
        conn.close()
        return
    
    
    nomina_id = nomina[0]
    cursor.execute("DELETE FROM detalle_nomina WHERE nomina_id=?", (nomina_id,))
    cursor.execute("DELETE FROM nominas WHERE id=?", (nomina_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Éxito", f"Nómina del {fecha_inicio_str} eliminada")
    tabla_nomina.delete(*tabla_nomina.get_children())


    conn = sqlite3.connect("empresas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_inicio, fecha_fin FROM nominas WHERE fecha_inicio=?", (fecha_inicio_str,))
    nomina = cursor.fetchone()
    conn.close()

    if nomina:
        messagebox.showinfo("Nómina encontrada", f"Nómina del {nomina[0]} al {nomina[1]}")
        mostrar_nomina_por_fecha(tabla_nomina, fecha_inicio_str)
    else:
        messagebox.showwarning("No encontrada", f"No existe nómina con fecha {fecha_inicio_str}")
    
    tabla_nomina.delete(*tabla_nomina.get_children())

    for fila in fila:
        tabla_nomina.insert("", "end", values=fila)


def exportar_nomina(tabla_nomina):
    if not tabla_nomina.get_children():
        messagebox.showwarning("Advertencia", "No hay datos para exportar")
        return

    ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                        filetypes=[("Archivos Excel", "*.xlsx")],
                                        title="Guardar Nómina como")
    if not ruta:
        return

    workbook = xlsxwriter.Workbook(ruta)
    worksheet = workbook.add_worksheet("Nómina")

    # ---------- FORMATOS ----------
    formato_titulo = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    formato_fecha = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter'
    })

    formato_encabezado = workbook.add_format({
        'bold': True,
        'bg_color': '#1F4E78',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    formato_celda = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })

    formato_numero = workbook.add_format({
        'num_format': '#,##0.00 "Bs."',
        'align': 'right',
        'border': 1
    })

    formato_total = workbook.add_format({
        'bold': True,
        'bg_color': '#FFD966',  
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    formato_dolar = workbook.add_format({
        'num_format': '#,##0.00 "US$"',
        'align': 'right',
        'border': 1
    })

    # ---------- TÍTULO Y FECHA ----------
    worksheet.merge_range("A1:D1", "Nómina de Personal", formato_titulo)

    fecha = datetime.now().strftime("Generada el %d/%m/%Y")
    worksheet.merge_range("A2:D2", fecha, formato_fecha)

    fila_inicio = 3  

    # ---------- ENCABEZADOS ----------
    encabezados = ["Cédula", "Nombre", "Cargo", "Salario (Bs.)"]
    for col_num, encabezado in enumerate(encabezados):
        worksheet.write(fila_inicio, col_num, encabezado, formato_encabezado)

    # ---------- DATOS ----------
    start_data_row = fila_inicio + 1
    items = tabla_nomina.get_children()
    num_rows = len(items)

    for idx, item in enumerate(items):
        row_index = start_data_row + idx
        fila = tabla_nomina.item(item, "values")
        worksheet.write(row_index, 0, fila[0], formato_celda)  
        worksheet.write(row_index, 1, fila[1], formato_celda)  
        worksheet.write(row_index, 2, fila[2], formato_celda)  
        try:
            salario = float(str(fila[3]).replace(" Bs.", "").replace("Bs.", "").strip())
            worksheet.write(row_index, 3, salario, formato_numero)
        except Exception:
            worksheet.write(row_index, 3, fila[3], formato_celda)

    # ---------- AJUSTE DE COLUMNAS ----------
    worksheet.set_column("A:A", 15)
    worksheet.set_column("B:B", 25)
    worksheet.set_column("C:C", 20)
    worksheet.set_column("D:D", 18)

    # ---------- TOTAL + TASA + TOTAL EN $ ----------
    total_row_index = start_data_row + num_rows

    if num_rows > 0:
        inicio_excel = fila_inicio + 2
        fin_excel = fila_inicio + 1 + num_rows

        # TOTAL en Bs
        worksheet.write(total_row_index, 2, "TOTAL Bs.", formato_total)
        worksheet.write_formula(total_row_index, 3,
                                f"=SUM(D{inicio_excel}:D{fin_excel})",
                                formato_numero)

        # Pedir la tasa al usuario
        tasa = simpledialog.askfloat("Tasa del día", "Ingrese la tasa de cambio (Bs. -> US$):", minvalue=0.1)
        if tasa is None:
            tasa = 1.0  # Valor por defecto si el usuario cancela

        # Escribir tasa
        worksheet.write(total_row_index + 1, 2, "Tasa del día", formato_total)
        worksheet.write(total_row_index + 1, 3, tasa, formato_numero)

        # TOTAL en US$
        worksheet.write(total_row_index + 2, 2, "TOTAL US$", formato_total)
        worksheet.write_formula(total_row_index + 2, 3,
                                f"D{total_row_index+1}/{tasa}",
                                formato_dolar)

    else:
        worksheet.write(start_data_row, 2, "TOTAL Bs.", formato_total)
        worksheet.write(start_data_row, 3, 0, formato_numero)

    workbook.close()
    messagebox.showinfo("Éxito", f"Nómina exportada con formato a:\n{ruta}")

# -------------------------------------------------
# Ventana Principal
# -------------------------------------------------
VentanaPrincipal = ctk.CTk()
VentanaPrincipal.title("Nómina de Personal")
ancho_pantalla = VentanaPrincipal.winfo_screenwidth()
alto_pantalla = VentanaPrincipal.winfo_screenheight()
VentanaPrincipal.geometry(f"{ancho_pantalla}x{alto_pantalla}+0+0")
VentanaPrincipal.withdraw()


def construir_menu_principal():
    tabview = ctk.CTkTabview(VentanaPrincipal, width=ancho_pantalla - 50, height=alto_pantalla - 100)
    tabview.pack(padx=20, pady=20, fill="both", expand=True)

    # --- Tab Nómina ---
    tab_nomina = tabview.add("Nómina")

    frame_nomina = ctk.CTkFrame(tab_nomina)
    frame_nomina.pack(fill="both", expand=True, padx=20, pady=20)
    

    # --- Tabla de nómina ---
    frame_tabla_nomina = ctk.CTkFrame(frame_nomina)
    frame_tabla_nomina.pack(fill="both", expand=True, padx=20, pady=20)

    tabla_nomina = ttk.Treeview(frame_tabla_nomina, columns=("cedula", "nombre", "cargo", "salario"), show="headings")
    tabla_nomina.heading("cedula", text="Cédula")
    tabla_nomina.heading("nombre", text="Nombre")
    tabla_nomina.heading("cargo", text="Cargo")
    tabla_nomina.heading("salario", text="Salario")
    tabla_nomina.pack(fill="both", expand=True)

    scroll_y_nomina = ctk.CTkScrollbar(frame_tabla_nomina, command=tabla_nomina.yview)
    scroll_y_nomina.pack(side="right", fill="y")
    tabla_nomina.configure(yscrollcommand=scroll_y_nomina.set)

    # --- Totales ---
    total_label = ctk.CTkLabel(frame_nomina, text="Total General de Sueldos: 0 Bs.", font=("Arial", 16, "bold"))
    total_label.pack(pady=10) 
    
    tasa_label = ctk.CTkLabel(frame_nomina, text="Tasa BCV: 0.00 Bs/$", font=("Arial", 14))
    tasa_label.pack()

    total_usd_label = ctk.CTkLabel(frame_nomina, text="Equivalente en Dólares: 0.00 $", font=("Arial", 14, "bold"))
    total_usd_label.pack(pady=5)

    # --- Tab Empleados ---
    tab_empleados = tabview.add("Empleados")

    frame_form = ctk.CTkFrame(tab_empleados)
    frame_form.pack(side="left", fill="y", padx=20, pady=20)
    
    # Botón para exportar nómina
    ctk.CTkButton(frame_nomina, text="Exportar Nómina a Excel", fg_color="#64c27b", hover_color="#308a47",
              command=lambda: exportar_nomina(tabla_nomina)).pack(pady=10)

    ctk.CTkButton(frame_nomina, text="Crear Nueva Nómina", fg_color="#007bff", hover_color="#0056b3", command=lambda: crear_nomina(tabla_nomina)).pack(pady=5)
    ctk.CTkButton(frame_nomina, text="Buscar Nómina", fg_color="#b0b300", hover_color="#817f00", command=lambda: buscar_nomina(tabla_nomina)).pack(pady=5)
    ctk.CTkButton(frame_nomina, text="Eliminar Nómina", fg_color="red", hover_color="#aa0000",
                  command=lambda: eliminar_nomina(tabla_nomina)).pack(pady=5)


    ctk.CTkLabel(frame_form, text="Cédula:").pack()
    entry_cedula = ctk.CTkEntry(frame_form, width=200)
    entry_cedula.pack(pady=5)

    ctk.CTkLabel(frame_form, text="Nombre:").pack()
    entry_nombre = ctk.CTkEntry(frame_form, width=200)
    entry_nombre.pack(pady=5)

    ctk.CTkLabel(frame_form, text="Cargo:").pack()
    entry_cargo = ctk.CTkOptionMenu(
        frame_form,
        values=["Encargado", "Carnicero", "Deshuesador", "Cajera","Administrador","Community Manager"],
        width=200
    )
    entry_cargo.pack(pady=5)
    
    # --- Función para limpiar las entradas ---
    def limpiar_entries():
        entry_cedula.delete(0, "end")
        entry_nombre.delete(0, "end")
        entry_salario.delete(0, "end")
        entry_cargo.set("Encargado")  


    # --- Salario con Bs. ---
    ctk.CTkLabel(frame_form, text="Salario:").pack()
    salario_var = ctk.StringVar()

    def formatear_salario(*args):
        valor = salario_var.get().replace(" Bs.", "").strip()
        if valor != "":
            salario_var.set(valor + " Bs.")

    salario_var.trace_add("write", formatear_salario)

    entry_salario = ctk.CTkEntry(frame_form, textvariable=salario_var, width=200)
    entry_salario.pack(pady=5)

    # --- Tabla empleados ---
    frame_tabla = ctk.CTkFrame(tab_empleados)
    frame_tabla.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
        background="#1e1e1e",
        foreground="white",
        fieldbackground="#1e1e1e",
        rowheight=25
    )
    style.map("Treeview",
        background=[("selected", "#2a8cff")],
        foreground=[("selected", "white")]
    )

    tabla = ttk.Treeview(frame_tabla, columns=("cedula", "nombre", "cargo", "salario"), show="headings")
    tabla.heading("cedula", text="Cédula")
    tabla.heading("nombre", text="Nombre")
    tabla.heading("cargo", text="Cargo")
    tabla.heading("salario", text="Salario")
    tabla.pack(fill="both", expand=True)

    scroll_y = ctk.CTkScrollbar(frame_tabla, command=tabla.yview)
    scroll_y.pack(side="right", fill="y")
    tabla.configure(yscrollcommand=scroll_y.set)

    # --- Funciones CRUD ---
    def cargar_empleados():
        tabla.delete(*tabla.get_children())
        conn = sqlite3.connect("empresas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT cedula, nombre, cargo, salario FROM empleados")
        for row in cursor.fetchall():
            tabla.insert("", "end", values=row)
        conn.close()

    def agregar_empleado():
        cedula = entry_cedula.get()
        nombre = entry_nombre.get()
        cargo = entry_cargo.get()
        salario = entry_salario.get()

        if cedula == "" or nombre == "":
            messagebox.showwarning("Error", "Cédula y Nombre son obligatorios")
            return

        conn = sqlite3.connect("empresas.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO empleados (cedula,nombre,cargo,salario) VALUES (?,?,?,?)",
                           (cedula, nombre, cargo, salario))
            conn.commit()
            messagebox.showinfo("Éxito", "Empleado agregado")
            cargar_empleados()
            cargar_nomina(tabla_nomina, total_label, tasa_label, total_usd_label)
            limpiar_entries()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "La cédula ya existe")
        conn.close()

    def eliminar_empleado():
        seleccionado = tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Error", "Selecciona un empleado de la tabla")
            return

        cedula = tabla.item(seleccionado, "values")[0]

        confirm = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar al empleado con cédula {cedula}?")
        if confirm:
            conn = sqlite3.connect("empresas.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM empleados WHERE cedula=?", (cedula,))
            conn.commit()
            conn.close()
            tabla.delete(seleccionado)
            messagebox.showinfo("Éxito", "Empleado eliminado")
            cargar_nomina(tabla_nomina, total_label, tasa_label, total_usd_label)
            limpiar_entries()


    def actualizar_empleado():
        seleccionado = tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Error", "Selecciona un empleado de la tabla")
            return

        cedula = tabla.item(seleccionado, "values")[0]

        nuevo_nombre = entry_nombre.get()
        nuevo_cargo = entry_cargo.get()
        nuevo_salario = entry_salario.get()

        if nuevo_nombre == "" or nuevo_salario == "":
            messagebox.showwarning("Error", "Nombre y salario son obligatorios")
            return

        conn = sqlite3.connect("empresas.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE empleados SET nombre=?, cargo=?, salario=? WHERE cedula=?",
                       (nuevo_nombre, nuevo_cargo, nuevo_salario, cedula))
        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", "Empleado actualizado")
        cargar_empleados()
        cargar_nomina(tabla_nomina, total_label, tasa_label, total_usd_label)
        limpiar_entries()
            
            

    # --- Botones ---
    ctk.CTkButton(frame_form, text="Guardar Empleado", fg_color="green", hover_color= "#308a47", command=agregar_empleado).pack(pady=10)
    ctk.CTkButton(frame_form, text="Eliminar Seleccionado", fg_color="red", hover_color="#aa0000",
                  command=eliminar_empleado).pack(pady=10)
    ctk.CTkButton(frame_form, text="Actualizar Empleado", fg_color="#1E90FF",
                  hover_color="#0056b3", command=actualizar_empleado).pack(pady=10)

    # Cargar datos al inicio
    cargar_nomina(tabla_nomina, total_label, tasa_label, total_usd_label)
    cargar_empleados()


# -------------------------------------------------
# Login
# -------------------------------------------------
def abrir_login():
    login = ctk.CTkToplevel()
    login.title("Autenticación")
    login.geometry("400x300")
    login.grab_set()

    def centrar_ventana(ventana, ancho, alto):
        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana.update_idletasks()

    centrar_ventana(login, 400, 300)

    titulo = ctk.CTkLabel(login, text="Acceso a la Nómina", font=("Arial", 20, "bold"))
    titulo.pack(pady=15)

    ctk.CTkLabel(login, text="Nombre de la Empresa:").pack(pady=5)
    entry_empresa = ctk.CTkEntry(login, width=250, placeholder_text="Empresa")
    entry_empresa.pack(pady=5)

    ctk.CTkLabel(login, text="Contraseña:").pack(pady=5)
    entry_pass = ctk.CTkEntry(login, width=250, placeholder_text="Contraseña", show="*")
    entry_pass.pack(pady=5)

    def verificar_login():
        empresa = entry_empresa.get()
        password = entry_pass.get()
        if empresa == "" or password == "":
            messagebox.showwarning("Error", "Todos los campos son obligatorios")
            return

        if verificar_login_db(empresa, password):
            messagebox.showinfo("Acceso", "Bienvenido al sistema")
            login.destroy()
            VentanaPrincipal.deiconify()
            construir_menu_principal()
        else:
            messagebox.showerror("Error", "Empresa o contraseña incorrecta")

    ctk.CTkButton(login, text="Ingresar", command=verificar_login).pack(pady=20)


# -------------------------------------------------
# Main
# -------------------------------------------------
inicializar_bd()
abrir_login()
VentanaPrincipal.mainloop()
