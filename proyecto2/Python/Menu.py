import customtkinter as ctk
from tkinter import messagebox
import datetime
from bson.objectid import ObjectId

# Importaciones de nuestros módulos
from Conexion import MongoDBConnection, DB # Importamos DB
from Logica import (
    user_manager, 
    category_manager, 
    tag_manager, 
    article_manager
)

class MainMenuApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión CRUD - Blog de Recetas")
        self.root.geometry("1000x700")
        
        # ¡CHEQUEO IMPORTANTE!
        # Verificamos la conexión global al inicio
        if DB is None:
            messagebox.showerror("Error Global", "La conexión global a la DB falló. Revisa que mongod esté corriendo.")
            self.root.quit()
            return
            
        # Ya no creamos 'self.db_conn', usamos la global
        self.articles_collection = article_manager.get_collection()
        self.current_frame = None

        # Cargar mapas al inicio
        user_manager.load_map()
        category_manager.load_map()
        tag_manager.load_map()

        # --- Configuración de Layout ---
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self.root, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Espacio para el botón de salir

        ctk.CTkLabel(self.sidebar_frame, text="Menú Principal", font=("Arial", 18, "bold")).pack(pady=20)
        
        self.article_button = ctk.CTkButton(self.sidebar_frame, text="1. Artículos (CRUD)", command=lambda: self.select_frame_by_name("articles"))
        self.article_button.pack(pady=10, padx=20, fill="x")
        
        self.category_button = ctk.CTkButton(self.sidebar_frame, text="2. Categorías (CRUD)", command=lambda: self.select_frame_by_name("categories"))
        self.category_button.pack(pady=10, padx=20, fill="x")

        self.tag_button = ctk.CTkButton(self.sidebar_frame, text="3. Tags (CRUD)", command=lambda: self.select_frame_by_name("tags"))
        self.tag_button.pack(pady=10, padx=20, fill="x")
        
        self.user_button = ctk.CTkButton(self.sidebar_frame, text="4. Usuarios (CRUD)", command=lambda: self.select_frame_by_name("users"))
        self.user_button.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkButton(self.sidebar_frame, text="Salir", command=self.root.quit, fg_color="red").pack(side="bottom", pady=20, padx=20, fill="x")

        # --- Frame de Contenido Principal ---
        self.main_content_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        
        # --- Creación de los Frames ---
        self.frames = {
            "articles": self.create_article_frame(),
            "categories": self.create_generic_crud_frame("Categorías", category_manager, name_key="name"),
            "tags": self.create_generic_crud_frame("Tags", tag_manager, name_key="name"),
            "users": self.create_generic_crud_frame("Usuarios", user_manager, name_key="email")
        }
        
        # Iniciar en la vista de artículos
        self.select_frame_by_name("articles")

    def select_frame_by_name(self, name):
        """Muestra el frame seleccionado y actualiza los datos."""
        for frame in self.frames.values():
            frame.grid_forget()
            
        self.current_frame = self.frames[name]
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        # Cargar datos frescos al cambiar de pestaña
        if name == "articles":
            self.load_articles()
        elif name in ["categories", "tags", "users"]:
            manager = user_manager if name == "users" else category_manager if name == "categories" else tag_manager
            self.load_generic_list(manager, self.current_frame.textbox, self.current_frame.name_key)


    # --- LÓGICA DE GESTIÓN DE ARTÍCULOS ---

    def create_article_frame(self):
        """Crea y configura el frame para la gestión de Artículos."""
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        
        ctk.CTkLabel(frame, text="Gestión de Artículos", font=("Arial", 20, "bold")).pack(pady=10)
        
        controls_frame = ctk.CTkFrame(frame)
        controls_frame.pack(pady=5, padx=10, fill="x")
        
        search_entry = ctk.CTkEntry(controls_frame, width=300, placeholder_text="Buscar por título, texto, autor, categoría o tag...")
        search_entry.pack(side="left", padx=(10, 5), fill="x", expand=True)

        ctk.CTkButton(controls_frame, text="Buscar / Recargar", command=self.load_articles).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Crear Nuevo", command=self.open_article_creation_window, fg_color="#3B82F6").pack(side="right", padx=(5, 10))

        self.article_textbox = ctk.CTkTextbox(frame, width=760, height=450, font=("Consolas", 13))
        self.article_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.article_textbox.configure(state="disabled")

        action_frame = ctk.CTkFrame(frame)
        action_frame.pack(pady=5, padx=10, fill="x")

        self.article_id_entry = ctk.CTkEntry(action_frame, placeholder_text="ID de Artículo para acción", width=250)
        self.article_id_entry.pack(side="left", padx=(10, 5))
        
        ctk.CTkButton(action_frame, text="Editar Artículo", command=self.open_article_edit_window, fg_color="orange").pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Eliminar Artículo", command=self.delete_article, fg_color="red").pack(side="left", padx=5)

        frame.search_entry = search_entry 
        return frame

    def load_articles(self):
        """Carga y muestra la lista de artículos, aplicando el filtro de búsqueda."""
        
        # --- LÓGICA DE FILTRO (MODIFICADA) ---
        search_entry = self.frames["articles"].search_entry
        search_term = search_entry.get()
        mongo_filter = {} # Por defecto, el filtro está vacío (busca todo)
        
        if search_term:
            regex_query = {"$regex": search_term, "$options": "i"}
            
            # ¡MODIFICADO! Ahora el $or busca en 5 campos
            mongo_filter = {
                "$or": [
                    {"title": regex_query}, 
                    {"text": regex_query},
                    {"author_details.name": regex_query},  # <-- NUEVO
                    {"category_details.name": regex_query},# <-- NUEVO
                    {"tag_details.name": regex_query}     # <-- NUEVO
                ]
            }
        
        # --- PIPELINE DE AGREGACIÓN (MODIFICADO) ---
        pipeline = [
            # 1. Traemos todas las relaciones PRIMERO
            { "$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            { "$lookup": {"from": "categories", "localField": "categories", "foreignField": "_id", "as": "category_details"}},
            { "$lookup": {"from": "tags", "localField": "tags", "foreignField": "_id", "as": "tag_details"}},
            
            # 2. Desanidamos el autor para facilitar la búsqueda
            { "$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}},
            
            # 3. ¡NUEVA POSICIÓN! Aplicamos el filtro DESPUÉS de los joins
            { "$match": mongo_filter }
        ]
        
        try:
            self.article_textbox.configure(state="normal")
            self.article_textbox.delete("1.0", "end")
            
            articles = self.articles_collection.aggregate(pipeline) 
            text_to_display = ""
            count = 0
            
            for article in articles:
                count += 1
                title = article.get("title", "Sin Título")
                text_preview = article.get("text", "")[:70] + "..."
                date_str = article.get("date", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")

                author_name = article.get('author_details', {}).get('name', 'Usuario Desconocido')
                cat_names = [cat.get('name') for cat in article.get('category_details', []) if cat.get('name')]
                tag_names = [tag.get('name') for tag in article.get('tag_details', []) if tag.get('name')]

                text_to_display += f"--- {title} ---\n"
                text_to_display += f"ID: {article['_id']}\n"
                text_to_display += f"Fecha: {date_str}\n"
                text_to_display += f"Autor: {author_name}\n"
                text_to_display += f"Categorías: {', '.join(cat_names) or 'Ninguna'}\n"
                text_to_display += f"Tags: {', '.join(tag_names) or 'Ninguno'}\n"
                text_to_display += f"Texto: {text_preview}\n"
                text_to_display += "-"*80 + "\n\n"
            
            if count == 0:
                text_to_display = f"No se encontraron artículos que coincidan con '{search_term}'." if search_term else "No hay artículos en la base de datos."
                
            self.article_textbox.insert("1.0", text_to_display)
            self.article_textbox.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error al Cargar", f"Error en la agregación de artículos: {e}")

    def open_article_creation_window(self):
        """Abre la ventana para crear un nuevo artículo."""
        self.open_article_form(is_edit=False)

    def open_article_edit_window(self):
        """Abre la ventana para editar un artículo existente."""
        article_id = self.article_id_entry.get()
        if not article_id:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del artículo que desea editar.")
            return

        try:
            article = self.articles_collection.find_one({"_id": ObjectId(article_id)})
            if not article:
                messagebox.showerror("No Encontrado", f"Artículo con ID '{article_id}' no existe.")
                return
            self.open_article_form(is_edit=True, article=article)
        except Exception as e:
            messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido: {e}")

    def open_article_form(self, is_edit, article=None):
        """Genera el formulario de creación/edición de artículos."""
        window = ctk.CTkToplevel(self.root)
        window.title("Editar Artículo" if is_edit else "Crear Nuevo Artículo")
        window.geometry("600x700")
        window.grab_set() # Modal
        
        # Recarga los managers para el formulario
        user_manager.load_map()
        category_manager.load_map()
        tag_manager.load_map()
        
        form_frame = ctk.CTkScrollableFrame(window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(form_frame, text="Título:").pack(padx=10, pady=(10, 0), anchor="w")
        title_entry = ctk.CTkEntry(form_frame, width=500)
        title_entry.pack(padx=10, pady=5)
        
        # Text
        ctk.CTkLabel(form_frame, text="Texto:").pack(padx=10, pady=(10, 0), anchor="w")
        text_box = ctk.CTkTextbox(form_frame, width=500, height=200)
        text_box.pack(padx=10, pady=5)
        
        # Author
        ctk.CTkLabel(form_frame, text="Autor:").pack(padx=10, pady=(10, 0), anchor="w")
        users = user_manager.get_all_names()
        user_option_menu = ctk.CTkOptionMenu(form_frame, values=users if users else ["No hay usuarios"])
        user_option_menu.pack(padx=10, pady=5, anchor="w")

        # Checkboxes
        ctk.CTkLabel(form_frame, text="Categorías:").pack(padx=10, pady=(10, 0), anchor="w")
        category_vars_map = self._setup_checkboxes(form_frame, category_manager)
        
        ctk.CTkLabel(form_frame, text="Tags:").pack(padx=10, pady=(10, 0), anchor="w")
        tag_vars_map = self._setup_checkboxes(form_frame, tag_manager)

        # Precargar datos
        if is_edit and article:
            title_entry.insert(0, article.get("title", ""))
            text_box.insert("1.0", article.get("text", ""))
            
            # Busca el email del autor por su ID
            author_email = user_manager.get_name_by_id(article.get("user_id")) # Método invertido
            if author_email:
                user_option_menu.set(author_email)

            self._check_initial_values(category_vars_map, article.get("categories", []))
            self._check_initial_values(tag_vars_map, article.get("tags", []))

        # Botón Guardar
        save_command = lambda: self.save_article(
            window, article['_id'] if is_edit else None, title_entry.get(),
            text_box.get("1.0", "end-1c"), user_option_menu.get(),
            category_vars_map, tag_vars_map
        )
        save_button = ctk.CTkButton(master=form_frame, 
                                     text="Guardar Cambios" if is_edit else "Crear Artículo", 
                                     fg_color="green",
                                     command=save_command)
        save_button.pack(pady=20, padx=10)

    def _setup_checkboxes(self, parent_frame, manager):
        """Función auxiliar para crear un conjunto de checkboxes a partir de un manager."""
        map_list = []
        names = manager.get_all_names() 
        
        container = ctk.CTkScrollableFrame(parent_frame, height=100) # Frame con scroll
        container.pack(padx=10, pady=5, fill="x")
        
        for name in names:
            var = ctk.IntVar(value=0)
            obj_id = manager.get_id_by_name(name)
            
            checkbox = ctk.CTkCheckBox(container, text=name, variable=var)
            checkbox.pack(anchor="w", padx=10)
            map_list.append((var, obj_id))
        
        return map_list
    
    def _check_initial_values(self, vars_map, current_ids):
        """Auxiliar para marcar los checkboxes que ya están seleccionados."""
        for var, obj_id in vars_map:
            if obj_id in current_ids:
                var.set(1)

    def save_article(self, window, article_id, title, text, user_name, category_vars_map, tag_vars_map):
        """Lógica para guardar (crear o editar) un artículo."""
        if not title or not text or user_name == "No hay usuarios":
            messagebox.showwarning("Campos Requeridos", "El Título, Texto y Autor son obligatorios.", parent=window)
            return
            
        try:
            user_id = user_manager.get_id_by_name(user_name)
            if not user_id:
                messagebox.showerror("Error", "Autor no válido.", parent=window)
                return

            category_ids = [ _id for var, _id in category_vars_map if var.get() == 1 ]
            tag_ids = [ _id for var, _id in tag_vars_map if var.get() == 1 ]

            new_article_data = {
                "title": title,
                "text": text,
                "user_id": user_id,
                "categories": category_ids,
                "tags": tag_ids 
            }
            
            if article_id:
                new_article_data["last_modified"] = datetime.datetime.now()
                self.articles_collection.update_one({"_id": article_id}, {"$set": new_article_data})
                messagebox.showinfo("Éxito", "Artículo actualizado exitosamente.", parent=window)
            else:
                new_article_data["date"] = datetime.datetime.now()
                self.articles_collection.insert_one(new_article_data)
                messagebox.showinfo("Éxito", "Artículo creado exitosamente.", parent=window)

            window.destroy()
            self.load_articles() 
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el artículo:\n{e}", parent=window)
    
    def delete_article(self):
        """Elimina un artículo por ID."""
        article_id = self.article_id_entry.get()
        if not article_id:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del artículo que desea eliminar.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el artículo con ID: {article_id}?", parent=self.root):
            try:
                result = self.articles_collection.delete_one({"_id": ObjectId(article_id)})
                if result.deleted_count > 0:
                    messagebox.showinfo("Éxito", "Artículo eliminado exitosamente.")
                    self.article_id_entry.delete(0, 'end')
                    self.load_articles() 
                else:
                    messagebox.showerror("Error", "No se encontró el artículo con ese ID.")
            except Exception as e:
                messagebox.showerror("ID Inválido", f"El ID proporcionado no es válido o hubo un error: {e}")


    # --- LÓGICA DE GESTIÓN GENÉRICA (Tags, Categorías, Usuarios) ---
    
    def create_generic_crud_frame(self, title, manager, name_key="name"):
        """Crea un frame CRUD genérico para Tags, Categorías o Usuarios."""
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        
        ctk.CTkLabel(frame, text=f"Gestión de {title}", font=("Arial", 20, "bold")).pack(pady=10)
        
        # Controles (Crear)
        create_frame = ctk.CTkFrame(frame)
        create_frame.pack(pady=5, padx=10, fill="x")

        input_label = "Nombre:" if name_key == "name" else "Email:"
        ctk.CTkLabel(create_frame, text=input_label).pack(side="left", padx=(10, 5))
        
        create_entry = ctk.CTkEntry(create_frame, placeholder_text=f"Nuevo {input_label.lower().replace(':','')}", width=250)
        create_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ctk.CTkButton(create_frame, text=f"Crear {title[:-1]}", command=lambda: self.create_generic_item(manager, create_entry.get(), name_key, create_entry)).pack(side="left", padx=(5, 10))

        # Textbox para mostrar la lista
        textbox = ctk.CTkTextbox(frame, width=760, height=450, font=("Consolas", 13))
        textbox.pack(pady=10, padx=10, fill="both", expand=True)
        textbox.configure(state="disabled")

        # Controles (Editar/Eliminar)
        action_frame = ctk.CTkFrame(frame)
        action_frame.pack(pady=5, padx=10, fill="x")

        id_entry = ctk.CTkEntry(action_frame, placeholder_text="ID del elemento para acción", width=250)
        id_entry.pack(side="left", padx=(10, 5))

        edit_entry = ctk.CTkEntry(action_frame, placeholder_text=f"Nuevo {input_label.lower().replace(':','')}", width=250)
        edit_entry.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            action_frame, 
            text="Actualizar", 
            command=lambda: self.update_generic_item(manager, id_entry.get(), edit_entry.get(), name_key, edit_entry),
            fg_color="orange"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame, 
            text="Eliminar", 
            command=lambda: self.delete_generic_item(manager, id_entry.get()),
            fg_color="red"
        ).pack(side="left", padx=(5, 10))

        frame.textbox = textbox
        frame.name_key = name_key
        frame.create_entry = create_entry
        frame.id_entry = id_entry
        
        return frame

    def load_generic_list(self, manager, textbox, name_key):
        """Carga y muestra la lista de entidades genéricas (Tags, Categorías, Usuarios)."""
        manager.load_map() 
        data_list = manager.get_all() 
        
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        
        text_to_display = f"--- Lista de {manager.collection.name.capitalize()} ---\n\n"
        
        if not data_list:
            text_to_display += "No hay elementos."
        else:
            for item in data_list:
                key_value = item.get(name_key, "N/A")
                text_to_display += f"ID: {item['_id']} | {name_key.capitalize()}: {key_value}\n"
                
                if name_key == "email" and item.get("name"):
                    text_to_display += f"  Nombre: {item['name']}\n"
                
                if name_key == "email" and item.get("password"):
                    text_to_display += f"  Contraseña: *** (oculta)\n" # Ocultar contraseña
                
                text_to_display += "-"*40 + "\n"
                
        textbox.insert("1.0", text_to_display)
        textbox.configure(state="disabled")

    def create_generic_item(self, manager, value, name_key, entry_widget):
        """Crea una nueva entidad genérica (Tag, Categoría, Usuario)."""
        if not value:
            messagebox.showwarning("Faltan Datos", f"El campo {name_key.capitalize()} es obligatorio.")
            return

        data = {name_key: value}
        if manager.collection.name == "users":
            # NOTA: Esto es inseguro, se debe usar hasheo
            data = {"email": value, "name": "Usuario Nuevo", "password": "123"} 
            
        inserted_id = manager.create_one(data) 
        
        if inserted_id:
            messagebox.showinfo("Éxito", f"{manager.collection.name[:-1].capitalize()} creado exitosamente con ID: {inserted_id}")
            entry_widget.delete(0, 'end')
            self.select_frame_by_name(manager.collection.name) 
        else:
            messagebox.showerror("Error", f"No se pudo crear el elemento en {manager.collection.name}.")

    def update_generic_item(self, manager, item_id, new_value, name_key, entry_widget):
        """Actualiza una entidad genérica por ID."""
        if not item_id or not new_value:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID y el nuevo valor.")
            return

        try:
            obj_id = ObjectId(item_id)
            data_to_update = {name_key: new_value}
            
            modified_count = manager.update_one(obj_id, data_to_update) 
            
            if modified_count > 0:
                messagebox.showinfo("Éxito", f"{manager.collection.name[:-1].capitalize()} actualizado exitosamente.")
                entry_widget.delete(0, 'end')
                self.select_frame_by_name(manager.collection.name) 
            else:
                messagebox.showwarning("Advertencia", "No se encontró el elemento o no hubo cambios.")

        except Exception as e:
            messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido o hubo un error: {e}")

    def delete_generic_item(self, manager, item_id):
        """Elimina una entidad genérica por ID."""
        if not item_id:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del elemento que desea eliminar.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar el elemento con ID: {item_id} de {manager.collection.name}?", parent=self.root):
            try:
                result = manager.delete_one(ObjectId(item_id))
                
                if result > 0:
                    messagebox.showinfo("Éxito", f"Elemento de {manager.collection.name} eliminado exitosamente.")
                    frame = self.frames[manager.collection.name]
                    frame.id_entry.delete(0, 'end')
                    self.select_frame_by_name(manager.collection.name) 
                else:
                    messagebox.showerror("Error", "No se encontró el elemento con ese ID.")
            except Exception as e:
                messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido o hubo un error: {e}")


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app_root = ctk.CTk()
    app_logic = MainMenuApp(app_root) 
    app_root.mainloop()