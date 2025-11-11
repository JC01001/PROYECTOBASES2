from pymongo import MongoClient 
from tkinter import messagebox 
import sys 

# --- Configuración de la Conexión ---
# Define la URL de conexión al servidor de MongoDB (AHORA APUNTA A ATLAS).
MONGO_URL = "mongodb://localhost:27017/" 
# Define el nombre de la base de datos que se va a utilizar.
DB_NAME = "Blog_Recetas"

class ConexionMongoDB:
    """Clase para gestionar la conexión a MongoDB y el objeto de la base de datos."""
    
    def __init__(self, raiz=None):
        """
        Inicializa la conexión.
        'raiz' es un parámetro opcional para manejar 
        errores de conexión de forma gráfica. Si se proporciona, muestra un error y sale de la app.
        """
        self.cliente = None # Inicializa el cliente de MongoDB a None.
        self.db = None      # Inicializa el objeto de la base de datos a None.
        
        try:
            # Crea una instancia de MongoClient intentando conectarse a la URL definida.
            self.cliente = MongoClient(MONGO_URL)
            # Prueba la conexión con el comando 'ping' (petición rápida al servidor).
            self.cliente.admin.command('ping') 
            # Si el ping es exitoso, selecciona la base de datos específica.
            self.db = self.cliente[DB_NAME]
            print("¡Conexión a MongoDB exitosa!")
            
        except Exception as e:
            # Captura cualquier error de conexión (servidor apagado, URL incorrecta, etc.).
            error_msg = f"Error al conectar a MongoDB en {MONGO_URL}: {e}"
            print(error_msg)
            
            if raiz:
                # Si se llamó desde una, muestra una advertencia gráfica.
                messagebox.showerror("Error de Conexión", error_msg)
                # Sale de la aplicación de la GUI.
                raiz.quit()
            else:
                sys.exit(1)

    def obtener_db(self):
        """Retorna el objeto de la base de datos (db)."""
        return self.db

# --- Configuración de Instancia Global ---
# Este bloque garantiza que la conexión se intente una vez al cargar el módulo.
try:
    # Intenta crear la conexión.
    gestor_db = ConexionMongoDB()
    # Almacena el objeto de la base de datos en la variable global DB.
    DB = gestor_db.obtener_db()
except:
    # Si la conexión falla, DB se establece a None.
    # Esto es manejado por los gestores en Logica.py.
    DB = None