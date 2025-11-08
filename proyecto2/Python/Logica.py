from Conexion import DB 
from bson.objectid import ObjectId 
import datetime

class GestorEntidad:
    """Clase base para gestionar colecciones, mapas de ID/Nombre y operaciones CRUD."""
    
    def __init__(self, nombre_coleccion, clave_nombre="name"):
        # Verifica si la conexión a la base de datos (DB) falló previamente.
        if DB is None:
            raise ConnectionError("La conexión a la base de datos no está disponible.")
            
        self.coleccion = DB[nombre_coleccion] # Asigna la colección de MongoDB (ej: DB['users']).
        self.clave_nombre = clave_nombre # Clave del campo que se usará para el mapeo (ej: 'name' o 'email').
        self.mapa_nombre_a_id = {} # Diccionario cache para mapear { "Nombre/Email": ObjectId(...) }.

    def cargar_mapa(self):
        """Carga el mapa {Nombre/Email: ID} de la colección para consultas rápidas."""
        self.mapa_nombre_a_id.clear() # Limpia el mapa anterior.
        try:
            # Busca todos los documentos, seleccionando solo el ID y la clave de nombre/email.
            entidades = self.coleccion.find({}, {"_id": 1, self.clave_nombre: 1})
            for entidad in entidades:
                if self.clave_nombre in entidad:
                    # Rellena el mapa cache: Clave=Nombre/Email, Valor=ObjectId.
                    self.mapa_nombre_a_id[entidad[self.clave_nombre]] = entidad["_id"]
            print(f"Cargados {len(self.mapa_nombre_a_id)} elementos en '{self.coleccion.name}'.")
        except Exception as e:
            print(f"Error cargando el mapa para {self.coleccion.name}: {e}")
            
    def obtener_todos_los_nombres(self):
        """Retorna una lista de todos los nombres (o emails) para OptionMenus/Checkboxes."""
        return list(self.mapa_nombre_a_id.keys())
    
    def obtener_id_por_nombre(self, nombre):
        """Retorna el ObjectId (el ID único de MongoDB) dado un nombre o email."""
        return self.mapa_nombre_a_id.get(nombre) # Busca en el mapa cache.

    # --- Operaciones CRUD Genéricas ---
    
    def obtener_todos(self):
        """Retorna todos los documentos de la colección como una lista."""
        try:
            return list(self.coleccion.find()) # Realiza la consulta a la base de datos.
        except Exception as e:
            print(f"Error obteniendo todos los documentos para {self.coleccion.name}: {e}")
            return []

    def crear_uno(self, datos):
        """Inserta un nuevo documento en la colección."""
        try:
            resultado = self.coleccion.insert_one(datos)
            self.cargar_mapa() # El mapa debe recargarse para incluir el nuevo elemento.
            return resultado.inserted_id # Retorna el ID generado por MongoDB.
        except Exception as e:
            print(f"Error creando el documento en {self.coleccion.name}: {e}")
            return None

    def actualizar_uno(self, id_objeto, nuevos_datos):
        """Actualiza un documento por su ObjectId."""
        try:
            # Usa $set para actualizar solo los campos en 'nuevos_datos'.
            resultado = self.coleccion.update_one({"_id": id_objeto}, {"$set": nuevos_datos})
            self.cargar_mapa() # Recarga el mapa por si el nombre/email fue actualizado.
            return resultado.modified_count # Retorna cuántos documentos fueron modificados (debería ser 1 o 0).
        except Exception as e:
            print(f"Error actualizando el documento en {self.coleccion.name}: {e}")
            return 0

    def eliminar_uno(self, id_objeto):
        """Elimina un documento por su ObjectId."""
        try:
            resultado = self.coleccion.delete_one({"_id": id_objeto})
            self.cargar_mapa() # Recarga el mapa para eliminar la referencia del elemento borrado.
            return resultado.deleted_count # Retorna cuántos documentos fueron eliminados (debería ser 1 o 0).
        except Exception as e:
            print(f"Error eliminando el documento en {self.coleccion.name}: {e}")
            return 0

# --- Clases Específicas que Heredan de GestorEntidad ---

class GestorUsuario(GestorEntidad):
    def __init__(self):
        # Llama al constructor de la clase base, usando "email" como clave_nombre.
        super().__init__("users", clave_nombre="email") 
        
    def autenticar(self, email, password):
        """Verifica el email y la contraseña contra la base de datos."""
        try:
            # Busca un documento que coincida con el email Y la contraseña.
            # NOTA: En una app real, la contraseña debe estar hasheada (no en texto plano).
            usuario = self.coleccion.find_one({"email": email, "password": password})
            return usuario # Retorna el documento del usuario si la autenticación es exitosa, sino None.
        except Exception as e:
            print(f"Error de autenticación: {e}")
            return None

class GestorCategoria(GestorEntidad):
    def __init__(self):
        # Usa la colección "categories" y "name" como clave.
        super().__init__("categories", clave_nombre="name")
        
class GestorEtiqueta(GestorEntidad):
    def __init__(self):
        # Usa la colección "tags" y "name" como clave.
        super().__init__("tags", clave_nombre="name")
        
# --- Instancias Globales de Gestores ---
# Estas son las instancias que se importan en Menu.py y Login.py.
gestor_usuarios = GestorUsuario()
gestor_categorias = GestorCategoria()
gestor_etiquetas = GestorEtiqueta()

class GestorArticulo:
    """Clase específica para Artículos. No hereda de GestorEntidad porque usa agregación compleja."""
    def __init__(self):
        if DB is None:
            raise ConnectionError("La conexión a la base de datos no está disponible.")
        self.coleccion_articulos = DB["articles"] # Referencia directa a la colección.
    
    def obtener_coleccion(self):
        """Retorna el objeto de la colección 'articles'."""
        # Se usa para ejecutar comandos de agregación directamente desde Menu.py.
        return self.coleccion_articulos
        
gestor_articulos = GestorArticulo() # Instancia global para el gestor de artículos.