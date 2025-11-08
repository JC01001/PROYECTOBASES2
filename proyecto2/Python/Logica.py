from Conexion import DB 
from bson.objectid import ObjectId
import datetime

class EntityManager:
    """Clase base para gestionar colecciones, mapas de ID/Nombre y operaciones CRUD."""
    
    def __init__(self, collection_name, name_key="name"):
        if DB is None:
            raise ConnectionError("La conexión a la base de datos no está disponible.")
            
        self.collection = DB[collection_name] 
        self.name_key = name_key 
        self.name_to_id_map = {} # Cache para mapear { "Nombre/Email": ObjectId(...) }

    def load_map(self):
        """Carga el mapa {Nombre/Email: ID} de la colección para consultas rápidas."""
        self.name_to_id_map.clear()
        try:
            entities = self.collection.find({}, {"_id": 1, self.name_key: 1})
            for entity in entities:
                if self.name_key in entity:
                    self.name_to_id_map[entity[self.name_key]] = entity["_id"]
            print(f"Cargados {len(self.name_to_id_map)} elementos en '{self.collection.name}'.")
        except Exception as e:
            print(f"Error cargando el mapa para {self.collection.name}: {e}")
            
    def get_all_names(self):
        """Retorna una lista de todos los nombres (o emails) para OptionMenus/Checkboxes."""
        return list(self.name_to_id_map.keys())
    
    def get_id_by_name(self, name):
        """Retorna el ObjectId dado un nombre o email."""
        return self.name_to_id_map.get(name)

    # --- CRUD Genérico ---
    def get_all(self):
        """Retorna todos los documentos de la colección como una lista."""
        try:
            return list(self.collection.find()) 
        except Exception as e:
            print(f"Error obteniendo todos los documentos para {self.collection.name}: {e}")
            return []

    def create_one(self, data):
        """Inserta un nuevo documento en la colección."""
        try:
            result = self.collection.insert_one(data)
            self.load_map() 
            return result.inserted_id
        except Exception as e:
            print(f"Error creando el documento en {self.collection.name}: {e}")
            return None

    def update_one(self, object_id, new_data):
        """Actualiza un documento por su ObjectId."""
        try:
            result = self.collection.update_one({"_id": object_id}, {"$set": new_data})
            self.load_map()
            return result.modified_count
        except Exception as e:
            print(f"Error actualizando el documento en {self.collection.name}: {e}")
            return 0

    def delete_one(self, object_id):
        """Elimina un documento por su ObjectId."""
        try:
            result = self.collection.delete_one({"_id": object_id})
            self.load_map()
            return result.deleted_count
        except Exception as e:
            print(f"Error eliminando el documento en {self.collection.name}: {e}")
            return 0

# --- Clases Específicas ---

class UserManager(EntityManager):
    def __init__(self):
        super().__init__("users", name_key="email") 
        
    def authenticate(self, email, password):
        """Verifica el email y la contraseña contra la base de datos."""
        try:
            # NOTA: En una app real, la contraseña debe estar hasheada.
            user = self.collection.find_one({"email": email, "password": password})
            return user
        except Exception as e:
            print(f"Error de autenticación: {e}")
            return None

class CategoryManager(EntityManager):
    def __init__(self):
        super().__init__("categories", name_key="name")
        
class TagManager(EntityManager):
    def __init__(self):
        super().__init__("tags", name_key="name")
        
# Instancias globales para ser importadas en las interfaces
user_manager = UserManager()
category_manager = CategoryManager()
tag_manager = TagManager()

class ArticleManager:
    def __init__(self):
        if DB is None:
            raise ConnectionError("La conexión a la base de datos no está disponible.")
        self.articles_collection = DB["articles"]
    
    def get_collection(self):
        """Retorna el objeto de la colección 'articles'."""
        return self.articles_collection
        
article_manager = ArticleManager()