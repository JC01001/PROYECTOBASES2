import customtkinter as ctk
from tkinter import messagebox
import subprocess
import sys
import os

from Conexion import MongoDBConnection 
from Logica import user_manager        

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio de Sesión de Usuario")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Inicializa la conexión (maneja la salida si falla)
        self.db_conn = MongoDBConnection(root=self.root) 

        # Carga de datos inicial
        user_manager.load_map()

        # --- Interfaz de Login ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        main_frame = ctk.CTkFrame(master=self.root, corner_radius=10)
        main_frame.pack(pady=40, padx=40, fill="both", expand=True)

        ctk.CTkLabel(master=main_frame, text="Iniciar Sesión", font=("Arial", 20, "bold")).pack(pady=20)

        # Email Entry
        ctk.CTkLabel(master=main_frame, text="Correo Electrónico:").pack(padx=10, anchor="w")
        self.email_entry = ctk.CTkEntry(master=main_frame, placeholder_text="ejemplo@correo.com", width=300)
        self.email_entry.pack(pady=5, padx=10)

        # Contraseña Entry
        ctk.CTkLabel(master=main_frame, text="Contraseña:").pack(padx=10, anchor="w")
        self.password_entry = ctk.CTkEntry(master=main_frame, placeholder_text="********", show="*", width=300)
        self.password_entry.pack(pady=5, padx=10)

        # Botón de Login 
        self.login_button = ctk.CTkButton(master=main_frame, text="Entrar", command=self.attempt_login, fg_color="#3B82F6")
        self.login_button.pack(pady=20, padx=10)

    def attempt_login(self):
        """Intenta autenticar al usuario."""
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showwarning("Error de Entrada", "Todos los campos son obligatorios.")
            return

        # LLAMADA A LA LÓGICA DE AUTENTICACIÓN
        user = user_manager.authenticate(email, password)
        
        if user:
            messagebox.showinfo("Éxito", f"Bienvenido, {user.get('name', email)}!")
            self.launch_main_app() 
        else:
            messagebox.showerror("Error de Autenticación", "Correo o contraseña incorrectos.")

    def launch_main_app(self):
        """Cierra la ventana de Login y lanza Menu.py."""
        self.root.destroy() 
        
        try:
            menu_path = os.path.join(os.path.dirname(__file__), "Menu.py")
            subprocess.Popen([sys.executable, menu_path])
        except Exception as e:
            messagebox.showerror("Error de Aplicación", f"No se pudo iniciar el menú principal:\n{e}")


if __name__ == "__main__":
    login_root = ctk.CTk()
    login_app = LoginApp(login_root) 
    login_root.mainloop()