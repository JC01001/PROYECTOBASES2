from pymongo import MongoClient
from tkinter import messagebox
import sys

# Define la URL de conexión
MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "Blog_Recetas"

class MongoDBConnection:
    """Clase para gestionar la conexión a MongoDB y el objeto de la base de datos."""
    
    def __init__(self, root=None):
        """
        Inicializa la conexión.
        root es opcional, se usa para mostrar errores de TKinter y salir de la app.
        """
        self.client = None
        self.db = None
        
        try:
            self.client = MongoClient(MONGO_URL)
            # Prueba la conexión para asegurar que las credenciales son válidas
            self.client.admin.command('ping') 
            self.db = self.client[DB_NAME]
            print("¡Conexión a MongoDB exitosa!")
            
        except Exception as e:
            error_msg = f"Error al conectar a MongoDB en {MONGO_URL}: {e}"
            print(error_msg)
            
            if root:
                # Si se proporciona la raíz de la GUI, muestra un error y sale
                messagebox.showerror("Error de Conexión", error_msg)
                root.quit()
            else:
                # Si no hay GUI, sale del script
                sys.exit(1)

    def get_db(self):
        """Retorna el objeto de la base de datos (db)."""
        return self.db

# Una instancia para usar en otros módulos
try:
    db_manager = MongoDBConnection()
    DB = db_manager.get_db()
except:
    # Si la conexión falla sin una raíz de Tkinter (e.g., al importar), DB será None
    DB = None