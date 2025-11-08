import customtkinter as ctk
from pymongo import MongoClient
from bson.objectid import ObjectId
from tkinter import messagebox
import datetime

# --- 1. CONFIGURACIÓN INICIAL ---

class BlogApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Blog - Proyecto 2")
        self.root.geometry("800x650")
        
        try:
            self.client = MongoClient("mongodb://localhost:27017/")
            self.db = self.client["proyecto2"]
            self.articles_collection = self.db["articles"]
            self.users_collection = self.db["users"]
            self.categories_collection = self.db["categories"]
            self.tags_collection = self.db["tags"]
            # <-- NUEVO: Añadimos la colección de comentarios
            self.comments_collection = self.db["comments"] 
            
            self.load_user_map()
            self.load_category_map()
            self.load_tag_map()
            
            print("¡Conexión a MongoDB exitosa!")
        except Exception as e:
            print(f"Error al conectar a MongoDB: {e}")
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a MongoDB:\n{e}")
            self.root.quit()
            return

        # --- Interfaz Principal ---
        self.title_label = ctk.CTkLabel(master=self.root, text="Artículos del Blog", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=(20, 10))

        self.controls_frame = ctk.CTkFrame(master=self.root)
        self.controls_frame.pack(pady=5, padx=20, fill="x")

        self.search_entry = ctk.CTkEntry(master=self.controls_frame, width=300, placeholder_text="Buscar por título o texto...")
        self.search_entry.pack(side="left", padx=(10, 5), fill="x", expand=True)

        self.load_button = ctk.CTkButton(master=self.controls_frame, text="Buscar / Recargar", command=self.load_articles)
        self.load_button.pack(side="left", padx=5)

        self.create_button = ctk.CTkButton(master=self.controls_frame, text="Crear Nuevo Artículo", command=self.open_create_window, fg_color="#3B82F6")
        self.create_button.pack(side="right", padx=(5, 10))

        self.articles_textbox = ctk.CTkTextbox(master=self.root, width=760, height=450, font=("Consolas", 13))
        self.articles_textbox.pack(pady=10, padx=20, fill="both", expand=True)
        self.articles_textbox.configure(state="disabled")

        self.load_articles()

    # --- Funciones de Carga de Mapas (Sin cambios) ---
    def load_user_map(self):
        self.user_map = {}
        try:
            users = self.users_collection.find({}, {"name": 1})
            for user in users:
                if "name" in user:
                    self.user_map[user["name"]] = user["_id"]
        except Exception as e:
            print(f"Error al cargar usuarios: {e}")

    def load_category_map(self):
        self.category_map = {}
        try:
            categories = self.categories_collection.find({}, {"name": 1})
            for cat in categories:
                if "name" in cat:
                    self.category_map[cat["name"]] = cat["_id"]
            print(f"Cargadas {len(self.category_map)} categorías.")
        except Exception as e:
            print(f"Error al cargar categorías: {e}")

    def load_tag_map(self):
        self.tag_map = {}
        try:
            tags = self.tags_collection.find({}, {"name": 1})
            for tag in tags:
                if "name" in tag:
                    self.tag_map[tag["name"]] = tag["_id"]
            print(f"Cargados {len(self.tag_map)} tags.")
        except Exception as e:
            print(f"Error al cargar tags: {e}")

    # --- FUNCIÓN "R" (READ) - ¡¡MODIFICADA para incluir comentarios!! ---
    def load_articles(self):
        print("Cargando artículos...")
        search_term = self.search_entry.get()
        mongo_filter = {}
        if search_term:
            regex_query = {"$regex": search_term, "$options": "i"}
            mongo_filter = {
                "$or": [
                    {"title": regex_query}, {"text": regex_query},
                    {"0.title": regex_query}, {"0.text": regex_query}
                ]
            }
        
        pipeline = [
            { "$match": mongo_filter },
            { "$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            { "$lookup": {"from": "categories", "localField": "categories", "foreignField": "_id", "as": "category_details"}},
            { "$lookup": {"from": "tags", "localField": "tags", "foreignField": "_id", "as": "tag_details"}},
            # <-- NUEVO: $lookup para comentarios
            { 
                "$lookup": {
                    "from": "comments",
                    "localField": "_id",         # El _id del artículo
                    "foreignField": "article_id",# Coincide con el article_id en comments
                    "as": "comment_details"
                }
            },
            { "$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}}
        ]
        
        try:
            self.articles_textbox.configure(state="normal")
            self.articles_textbox.delete("1.0", "end")
            articles = self.articles_collection.aggregate(pipeline)
            text_to_display = ""
            count = 0
            
            for article in articles:
                count += 1
                
                # --- CORRECCIÓN DE ERROR 'data' ---
                # Inicializamos las variables ANTES del if/elif
                title = "Sin Título"
                text_preview = "Sin texto..."
                
                # Estructura 1 (anidada con "0")
                if "0" in article and isinstance(article["0"], dict):
                    data = article.get("0", {})
                    title = data.get("title", "Sin Título (Anidado)")
                    text_preview = data.get("text", "")[:70] + "..."
                
                # Estructura 2 (limpia)
                elif "title" in article:
                    title = article.get("title", "Sin Título")
                    text_preview = article.get("text", "")[:70] + "..."
                # --- FIN DE CORRECCIÓN ---

                author_name = article.get('author_details', {}).get('name', 'Usuario Desconocido')
                cat_names = [cat.get('name') for cat in article.get('category_details', [])]
                tag_names = [tag.get('name') for tag in article.get('tag_details', [])]

                # <-- NUEVO: Formatear comentarios
                comments_list = article.get('comment_details', [])
                comments_text = ""
                if not comments_list:
                    comments_text = "      (Sin comentarios)\n"
                else:
                    for comment in comments_list:
                        # En tu estructura, 'name' es el nombre de quien comenta
                        comment_author = comment.get('name', 'Anónimo') 
                        comment_content = comment.get('text', '...')
                        comments_text += f"      > {comment_author}: {comment_content}\n"
                # --- Fin de formato de comentarios ---

                text_to_display += f"--- {title} ---\n"
                text_to_display += f"ID: {article['_id']}\n"
                text_to_display += f"Autor: {author_name}\n"
                text_to_display += f"Categorías: {', '.join(cat_names) or 'Ninguna'}\n"
                text_to_display += f"Tags: {', '.join(tag_names) or 'Ninguno'}\n"
                text_to_display += f"Texto: {text_preview}\n"
                # <-- NUEVO: Añadimos los comentarios al display
                text_to_display += "Comentarios:\n"
                text_to_display += comments_text
                text_to_display += "-"*80 + "\n\n"
            
            if count == 0:
                text_to_display = f"No se encontraron artículos que coincidan con '{search_term}'."
                
            self.articles_textbox.insert("1.0", text_to_display)
            self.articles_textbox.configure(state="disabled")
            
        except Exception as e:
            print(f"Error al procesar artículos: {e}")
            messagebox.showerror("Error al Cargar", f"Error al procesar artículos: {e}")

    # --- FUNCIÓN "C" (CREATE) - Abrir ventana ---
    def open_create_window(self):
        print("Abriendo ventana de creación...")
        
        create_window = ctk.CTkToplevel(self.root)
        create_window.title("Crear Nuevo Artículo")
        create_window.geometry("500x700")
        create_window.transient(self.root)
        
        # --- ¡¡MODIFICADO CON SCROLL!! ---
        # El frame principal de la ventana ahora es un ScrollableFrame
        form_frame = ctk.CTkScrollableFrame(master=create_window) 
        form_frame.pack(pady=20, padx=20, fill="both", expand=True)
        # --- FIN DE LA MODIFICACIÓN ---

        ctk.CTkLabel(master=form_frame, text="Título:", font=("Arial", 14)).pack(anchor="w", padx=10)
        title_entry = ctk.CTkEntry(master=form_frame, width=400, font=("Arial", 14))
        title_entry.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(master=form_frame, text="Texto:", font=("Arial", 14)).pack(anchor="w", padx=10)
        text_box = ctk.CTkTextbox(master=form_frame, height=150, font=("Arial", 14))
        text_box.pack(pady=5, padx=10, fill="both", expand=True)

        ctk.CTkLabel(master=form_frame, text="Autor:", font=("Arial", 14)).pack(anchor="w", padx=10)
        user_names = list(self.user_map.keys()) or ["No hay usuarios"]
        user_option_menu = ctk.CTkOptionMenu(master=form_frame, values=user_names)
        user_option_menu.pack(pady=5, padx=10, fill="x")

        # --- Checkboxes para Categorías ---
        ctk.CTkLabel(master=form_frame, text="Categorías:", font=("Arial", 14)).pack(anchor="w", padx=10, pady=(10,0))
        cat_frame = ctk.CTkScrollableFrame(master=form_frame, height=100)
        cat_frame.pack(pady=5, padx=10, fill="x")
        
        category_vars_map = []
        for name, _id in self.category_map.items():
            var = ctk.IntVar(value=0)
            cb = ctk.CTkCheckBox(master=cat_frame, text=name, variable=var)
            cb.pack(anchor="w", padx=10)
            category_vars_map.append((var, _id))

        # --- Checkboxes para Tags ---
        ctk.CTkLabel(master=form_frame, text="Tags:", font=("Arial", 14)).pack(anchor="w", padx=10, pady=(10,0))
        tag_frame = ctk.CTkScrollableFrame(master=form_frame, height=100)
        tag_frame.pack(pady=5, padx=10, fill="x")
        
        tag_vars_map = []
        for name, _id in self.tag_map.items():
            var = ctk.IntVar(value=0)
            cb = ctk.CTkCheckBox(master=tag_frame, text=name, variable=var)
            cb.pack(anchor="w", padx=10)
            tag_vars_map.append((var, _id))

        # --- Botón Guardar ---
        save_button = ctk.CTkButton(master=form_frame, 
                                    text="Guardar Artículo", 
                                    fg_color="green",
                                    command=lambda: self.save_new_article(
                                        create_window,
                                        title_entry.get(),
                                        text_box.get("1.0", "end-1c"),
                                        user_option_menu.get(),
                                        category_vars_map,
                                        tag_vars_map
                                    ))
        save_button.pack(pady=20, padx=10)
        
    # --- FUNCIÓN "C" (CREATE) - Lógica de guardado (Sin cambios) ---
    def save_new_article(self, window, title, text, user_name, category_vars_map, tag_vars_map):
        print("Intentando guardar nuevo artículo...")
        
        if not title or not text:
            messagebox.showwarning("Campos Vacíos", "El Título y el Texto son obligatorios.", parent=window)
            return
            
        try:
            user_id = self.user_map.get(user_name)
            if not user_id:
                messagebox.showerror("Error", "Autor no válido.", parent=window)
                return

            category_ids = []
            for var, _id in category_vars_map:
                if var.get() == 1:
                    category_ids.append(_id)

            tag_ids = []
            for var, _id in tag_vars_map:
                if var.get() == 1:
                    tag_ids.append(_id)

            new_article = {
                "title": title,
                "text": text,
                "date": datetime.datetime.now(),
                "user_id": user_id,
                "categories": category_ids,
                "tags": tag_ids
            }
            
            inserted = self.articles_collection.insert_one(new_article)
            print(f"Artículo insertado con ID: {inserted.inserted_id}")
            
            messagebox.showinfo("Éxito", "Artículo creado exitosamente.", parent=window)
            window.destroy()
            self.load_articles()

        except Exception as e:
            print(f"Error al guardar: {e}")
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el artículo:\n{e}", parent=window)


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app_root = ctk.CTk()
    app_logic = BlogApp(app_root)
    app_root.mainloop()