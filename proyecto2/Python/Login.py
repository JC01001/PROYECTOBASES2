import customtkinter as ctk 
from tkinter import messagebox 
import subprocess 
import sys 
import os 

# Importaciones de nuestros módulos de lógica y conexión.
from Conexion import MongoDBConnection # Importa la clase de conexión (para manejar el inicio y errores).
from Logica import user_manager # Importa el gestor de usuarios para la autenticación.

class AppLogin:
    """Clase para la ventana de Inicio de Sesión."""
    def __init__(self, raiz):
        self.raiz = raiz # Almacena la ventana principal de Tkinter.
        self.raiz.title("Inicio de Sesión de Usuario")
        self.raiz.geometry("400x350")
        self.raiz.resizable(False, False) # Evita que la ventana se redimensione.
        
        # --- Manejo de Conexión ---
        # Inicializa la conexión. Si la conexión a MongoDB falla, llama a raiz.quit() 
        # para cerrar la aplicación de manera segura, mostrando un error de Tkinter.
        self.conn_db = MongoDBConnection(raiz=self.raiz) 

        # Carga inicial de datos de usuarios (necesario para el gestor de usuarios).
        user_manager.cargar_mapa()

        # --- Configuración y Creación de la Interfaz ---
        ctk.set_appearance_mode("dark") # Establece el tema oscuro.
        ctk.set_default_color_theme("blue") # Establece el color de acento azul.
        
        # Frame principal que contiene todos los widgets del login.
        frame_principal = ctk.CTkFrame(master=self.raiz, corner_radius=10)
        frame_principal.pack(pady=40, padx=40, fill="both", expand=True)

        # Título de la ventana de login.
        ctk.CTkLabel(master=frame_principal, text="Iniciar Sesión", font=("Arial", 20, "bold")).pack(pady=20)

        # Campo de entrada para el Email.
        ctk.CTkLabel(master=frame_principal, text="Correo Electrónico:").pack(padx=10, anchor="w")
        self.entrada_email = ctk.CTkEntry(master=frame_principal, placeholder_text="ejemplo@correo.com", width=300)
        self.entrada_email.pack(pady=5, padx=10)

        # Campo de entrada para la Contraseña.
        ctk.CTkLabel(master=frame_principal, text="Contraseña:").pack(padx=10, anchor="w")
        self.entrada_contrasena = ctk.CTkEntry(master=frame_principal, placeholder_text="********", show="*", width=300)
        self.entrada_contrasena.pack(pady=5, padx=10)

        # Botón de Login que llama a la función de autenticación.
        self.boton_login = ctk.CTkButton(master=frame_principal, text="Entrar", command=self.intentar_login, fg_color="#3B82F6")
        self.boton_login.pack(pady=20, padx=10)

    def intentar_login(self):
        """Intenta autenticar al usuario."""
        email = self.entrada_email.get()
        password = self.entrada_contrasena.get()
        
        if not email or not password:
            messagebox.showwarning("Error de Entrada", "Todos los campos son obligatorios.")
            return

        # LLAMADA A LA LÓGICA DE AUTENTICACIÓN (en Logica.py)
        # user_manager.authenticate() retorna el documento del usuario si es exitoso, sino None.
        usuario = user_manager.autenticar(email, password)
        
        if usuario:
            # Autenticación exitosa
            messagebox.showinfo("Éxito", f"Bienvenido, {usuario.get('name', email)}!")
            self.lanzar_aplicacion_principal() # Pasa al menú.
        else:
            # Autenticación fallida
            messagebox.showerror("Error de Autenticación", "Correo o contraseña incorrectos.")

    def lanzar_aplicacion_principal(self):
        """Cierra la ventana de Login y lanza Menu.py usando subprocess."""
        self.raiz.destroy() # Cierra la ventana actual (Login).
        
        try:
            # Construye la ruta absoluta al archivo Menu.py.
            ruta_menu = os.path.join(os.path.dirname(__file__), "Menu.py")
            # Inicia el script Menu.py en un proceso separado.
            subprocess.Popen([sys.executable, ruta_menu])
        except Exception as e:
            messagebox.showerror("Error de Aplicación", f"No se pudo iniciar el menú principal:\n{e}")


if __name__ == "__main__":
    # Bloque de ejecución principal
    raiz_login = ctk.CTk()
    app_login = AppLogin(raiz_login) 
    raiz_login.mainloop() # Inicia el bucle principal de la GUI.