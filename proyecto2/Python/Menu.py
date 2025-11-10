import customtkinter as ctk 
from tkinter import messagebox 
import datetime 
from bson.objectid import ObjectId 

# Importaciones de nuestros módulos
from Conexion import ConexionMongoDB, DB # Importa la variable global DB para el chequeo de conexión.
from Logica import (
    gestor_usuarios, # Gestor de la colección 'users'.
    gestor_categorias, # Gestor de la colección 'categories'.
    gestor_etiquetas, # Gestor de la colección 'tags'.
    gestor_articulos, # Gestor de la colección 'articles'.
    gestor_comentarios # Gestor de la colección 'comentarios'
)

class AppMenuPrincipal:
    
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Gestión CRUD - Blog de Recetas")
        self.raiz.geometry("1000x700")
        
        # --- Chequeo de Conexión ---
        if DB is None:
            # Si DB es None, significa que la conexión falló en Conexion.py.
            messagebox.showerror("Error Global", "La conexión global a la DB falló. Revisa que mongod esté corriendo.")
            self.raiz.quit()
            return
            
        # Obtenemos la referencia a la colección de artículos.
        self.coleccion_articulos = gestor_articulos.obtener_coleccion()
        self.frame_actual = None # Para rastrear el frame visible.

        # Cargar los mapas de los managers al inicio para los OptionMenus y Checkboxes.
        gestor_usuarios.cargar_mapa()
        gestor_categorias.cargar_mapa()
        gestor_etiquetas.cargar_mapa()

        # --- Configuración de Layout (Grid) ---
        self.raiz.grid_columnconfigure(1, weight=1) # Columna de contenido principal expandible.
        self.raiz.grid_rowconfigure(0, weight=1) # Fila principal expandible.

        # --- Barra Lateral (Sidebar) ---
        self.frame_sidebar = ctk.CTkFrame(self.raiz, width=180, corner_radius=0)
        self.frame_sidebar.grid(row=0, column=0, sticky="nsew")
        self.frame_sidebar.grid_rowconfigure(5, weight=1) # Empuja el botón "Salir" al fondo.

        ctk.CTkLabel(self.frame_sidebar, text="Menú Principal", font=("Arial", 18, "bold")).pack(pady=20)
        
        # Botones para cambiar la vista (Artículos, Categorías, Tags, Usuarios).
        self.boton_articulos = ctk.CTkButton(self.frame_sidebar, text="1. Artículos (CRUD)", command=lambda: self.seleccionar_frame_por_nombre("articles"))
        self.boton_articulos.pack(pady=10, padx=20, fill="x")
        
        self.boton_categorias = ctk.CTkButton(self.frame_sidebar, text="2. Categorías (CRUD)", command=lambda: self.seleccionar_frame_por_nombre("categories"))
        self.boton_categorias.pack(pady=10, padx=20, fill="x")

        self.boton_tags = ctk.CTkButton(self.frame_sidebar, text="3. Tags (CRUD)", command=lambda: self.seleccionar_frame_por_nombre("tags"))
        self.boton_tags.pack(pady=10, padx=20, fill="x")
        
        self.boton_usuarios = ctk.CTkButton(self.frame_sidebar, text="4. Usuarios (CRUD)", command=lambda: self.seleccionar_frame_por_nombre("users"))
        self.boton_usuarios.pack(pady=10, padx=20, fill="x")
        
        # Botón de Salir.
        ctk.CTkButton(self.frame_sidebar, text="Salir", command=self.raiz.quit, fg_color="red").pack(side="bottom", pady=20, padx=20, fill="x")

        # --- Frame de Contenido Principal ---
        self.frame_contenido_principal = ctk.CTkFrame(self.raiz, corner_radius=0)
        self.frame_contenido_principal.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_contenido_principal.grid_columnconfigure(0, weight=1)
        self.frame_contenido_principal.grid_rowconfigure(0, weight=1)
        
        # --- Creación de los Frames ---
        self.frames = {
            "articles": self.crear_frame_articulos(),
            # Usa la función genérica para crear frames de CRUD simples:
            "categories": self.crear_frame_crud_generico("Categorías", gestor_categorias, clave_nombre="name"),
            "tags": self.crear_frame_crud_generico("Tags", gestor_etiquetas, clave_nombre="name"),
            "users": self.crear_frame_crud_generico("Usuarios", gestor_usuarios, clave_nombre="email")
        }
        
        # Muestra la vista de artículos por defecto.
        self.seleccionar_frame_por_nombre("articles")

    def seleccionar_frame_por_nombre(self, nombre):
        """Oculta todos los frames y muestra el seleccionado, recargando su lista de datos."""
        for frame in self.frames.values():
            frame.grid_forget() # Oculta el frame.
            
        self.frame_actual = self.frames[nombre]
        self.frame_actual.grid(row=0, column=0, sticky="nsew") # Muestra el frame.

        # Cargar datos frescos al cambiar de pestaña
        if nombre == "articles":
            self.cargar_articulos() # Carga de artículos (con lógica de agregación/join).
        elif nombre in ["categories", "tags", "users"]:
            # Obtiene el manager correcto para la carga genérica.
            if nombre == "users": manager = gestor_usuarios
            elif nombre == "categories": manager = gestor_categorias
            else: manager = gestor_etiquetas
            # Carga la lista genérica.
            self.cargar_lista_generica(manager, self.frame_actual.textbox, self.frame_actual.clave_nombre)


    # --- LÓGICA DE GESTIÓN DE ARTÍCULOS ---

    def crear_frame_articulos(self):
        """Crea y configura el frame para la gestión de Artículos."""
        frame = ctk.CTkFrame(self.frame_contenido_principal, fg_color="transparent")
        
        ctk.CTkLabel(frame, text="Gestión de Artículos", font=("Arial", 20, "bold")).pack(pady=10)
        
        # Frame para controles de búsqueda/creación
        frame_controles = ctk.CTkFrame(frame)
        frame_controles.pack(pady=5, padx=10, fill="x")
        
        # Entrada de búsqueda.
        entrada_busqueda = ctk.CTkEntry(frame_controles, width=300, placeholder_text="Buscar por título, texto, autor, categoría o tag...")
        entrada_busqueda.pack(side="left", padx=(10, 5), fill="x", expand=True)

        # Botones de acción.
        ctk.CTkButton(frame_controles, text="Buscar / Recargar", command=self.cargar_articulos).pack(side="left", padx=5)
        ctk.CTkButton(frame_controles, text="Crear Nuevo", command=self.abrir_ventana_creacion_articulo, fg_color="#3B82F6").pack(side="right", padx=(5, 10))

        # Textbox para mostrar la lista de artículos.
        self.caja_texto_articulos = ctk.CTkTextbox(frame, width=760, height=450, font=("Consolas", 13))
        self.caja_texto_articulos.pack(pady=10, padx=10, fill="both", expand=True)
        self.caja_texto_articulos.configure(state="disabled")

        # Frame para acciones de edición/eliminación.
        frame_accion = ctk.CTkFrame(frame)
        frame_accion.pack(pady=5, padx=10, fill="x")

        # Entrada para el ID del artículo a modificar.
        self.entrada_id_articulo = ctk.CTkEntry(frame_accion, placeholder_text="ID de Artículo para acción", width=250)
        self.entrada_id_articulo.pack(side="left", padx=(10, 5))
        
        ctk.CTkButton(frame_accion, text="Editar Artículo", command=self.abrir_ventana_edicion_articulo, fg_color="orange").pack(side="left", padx=5)
        ctk.CTkButton(frame_accion, text="Eliminar Artículo", command=self.eliminar_articulo, fg_color="red").pack(side="left", padx=5)

        frame.entrada_busqueda = entrada_busqueda # Almacena la referencia a la entrada de búsqueda en el frame.
        return frame

    def cargar_articulos(self):
        """Carga y muestra la lista de artículos con filtro y detalle de relaciones."""
        
        # --- LÓGICA DE FILTRO ---
        entrada_busqueda = self.frames["articles"].entrada_busqueda
        termino_busqueda = entrada_busqueda.get()
        filtro_mongo = {} 
        
        if termino_busqueda:
            # Crea una consulta de expresión regular insensible a mayúsculas/minúsculas.
            consulta_regex = {"$regex": termino_busqueda, "$options": "i"}
            
            # Aplica el filtro $or para buscar en múltiples campos, incluyendo los campos JOIN.
            filtro_mongo = {
                "$or": [
                    {"title": consulta_regex}, 
                    {"text": consulta_regex},
                    {"author_details.email": consulta_regex},  # Búsqueda por email del autor.
                    {"category_details.name": consulta_regex}, # Búsqueda por nombre de categoría.
                    {"tag_details.name": consulta_regex}      # Búsqueda por nombre de tag.
                ]
            }
        
        # --- PIPELINE DE AGREGACIÓN (Simula los JOINs SQL) ---
        pipeline = [
            # 1. $lookup: Trae la información del Autor (user_id -> users._id).
            { "$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            # 2. $lookup: Trae la información de las Categorías (categories -> categories._id).
            { "$lookup": {"from": "categories", "localField": "categories", "foreignField": "_id", "as": "category_details"}},
            # 3. $lookup: Trae la información de los Tags (tags -> tags._id).
            { "$lookup": {"from": "tags", "localField": "tags", "foreignField": "_id", "as": "tag_details"}},
            
            # 4. $unwind: Desanida el arreglo de 'author_details' (que solo tiene un elemento).
            #    'preserveNullAndEmptyArrays': True permite que muestre artículos sin autor (aunque no debería).
            { "$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}},
            
            # 5. $match: Aplica el filtro de búsqueda DESPUÉS de haber cargado todos los detalles.
            { "$match": filtro_mongo }
        ]
        
        try:
            self.caja_texto_articulos.configure(state="normal")
            self.caja_texto_articulos.delete("1.0", "end")
            
            # Ejecuta la agregación en la colección de artículos.
            articulos = self.coleccion_articulos.aggregate(pipeline) 
            texto_a_mostrar = ""
            contador = 0
            
            for articulo in articulos:
                contador += 1
                titulo = articulo.get("title", "Sin Título")
                texto_previo = articulo.get("text", "")[:70] + "..."
                fecha_str = articulo.get("date", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")

                # Extrae los nombres de los detalles unidos (JOINed)
                nombre_autor = articulo.get('author_details', {}).get('email', 'Usuario Desconocido') # Usamos email como identificador.
                nombres_cats = [cat.get('name') for cat in articulo.get('category_details', []) if cat.get('name')]
                nombres_tags = [tag.get('name') for tag in articulo.get('tag_details', []) if tag.get('name')]

                # Formatea la salida
                texto_a_mostrar += f"--- {titulo} ---\n"
                texto_a_mostrar += f"ID: {articulo['_id']}\n"
                texto_a_mostrar += f"Fecha: {fecha_str}\n"
                texto_a_mostrar += f"Autor: {nombre_autor}\n"
                texto_a_mostrar += f"Categorías: {', '.join(nombres_cats) or 'Ninguna'}\n"
                texto_a_mostrar += f"Tags: {', '.join(nombres_tags) or 'Ninguno'}\n"
                texto_a_mostrar += f"Texto: {texto_previo}\n"
                texto_a_mostrar += "-"*80 + "\n\n"
            
            if contador == 0:
                texto_a_mostrar = f"No se encontraron artículos que coincidan con '{termino_busqueda}'." if termino_busqueda else "No hay artículos en la base de datos."
                
            self.caja_texto_articulos.insert("1.0", texto_a_mostrar)
            self.caja_texto_articulos.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error al Cargar", f"Error en la agregación de artículos: {e}")

    # Funciones auxiliares para abrir el formulario (Crear/Editar)

    def abrir_ventana_creacion_articulo(self):
        """Abre el formulario para crear un nuevo artículo."""
        self.abrir_formulario_articulo(es_edicion=False)

    def abrir_ventana_edicion_articulo(self):
        """Abre el formulario para editar un artículo existente."""
        id_articulo = self.entrada_id_articulo.get()
        if not id_articulo:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del artículo que desea editar.")
            return

        try:
            # Busca el artículo por ID.
            articulo = self.coleccion_articulos.find_one({"_id": ObjectId(id_articulo)})
            if not articulo:
                messagebox.showerror("No Encontrado", f"Artículo con ID '{id_articulo}' no existe.")
                return
            self.abrir_formulario_articulo(es_edicion=True, articulo=articulo)
        except Exception as e:
            messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido: {e}")

    def abrir_formulario_articulo(self, es_edicion, articulo=None):
        """Genera y muestra el formulario de creación/edición de artículos."""
        ventana = ctk.CTkToplevel(self.raiz) # Crea una ventana de nivel superior (modal).
        ventana.title("Editar Artículo" if es_edicion else "Crear Nuevo Artículo")
        ventana.geometry("600x700")
        ventana.grab_set() # Hace que la ventana sea modal (bloquea la principal).
        
        # Recarga los mapas para asegurar que los selectores y checkboxes tengan los datos más recientes.
        gestor_usuarios.cargar_mapa()
        gestor_categorias.cargar_mapa()
        gestor_etiquetas.cargar_mapa()
        
        frame_formulario = ctk.CTkScrollableFrame(ventana) # Frame con scrollbar.
        frame_formulario.pack(fill="both", expand=True, padx=20, pady=20)

        
        # Widgets del formulario: Título, Texto, Autor (OptionMenu), Categorías (Checkboxes), Tags (Checkboxes).
        
        # Título
        ctk.CTkLabel(frame_formulario, text="Título:").pack(padx=10, pady=(10, 0), anchor="w")
        entrada_titulo = ctk.CTkEntry(frame_formulario, width=500)
        entrada_titulo.pack(padx=10, pady=5)
        
        # Texto
        ctk.CTkLabel(frame_formulario, text="Texto:").pack(padx=10, pady=(10, 0), anchor="w")
        caja_texto = ctk.CTkTextbox(frame_formulario, width=500, height=200)
        caja_texto.pack(padx=10, pady=5)
        
        # Autor (Selector OptionMenu)
        ctk.CTkLabel(frame_formulario, text="Autor:").pack(padx=10, pady=(10, 0), anchor="w")
        usuarios = gestor_usuarios.obtener_todos_los_nombres()
        menu_opciones_usuario = ctk.CTkOptionMenu(frame_formulario, values=usuarios if usuarios else ["No hay usuarios"])
        menu_opciones_usuario.pack(padx=10, pady=5, anchor="w")

        # Categorías (Checkboxes)
        ctk.CTkLabel(frame_formulario, text="Categorías:").pack(padx=10, pady=(10, 0), anchor="w")
        # _setup_checkboxes retorna una lista de tuplas (variable_tkinter, object_id)
        mapa_vars_categoria = self._configurar_checkboxes(frame_formulario, gestor_categorias) 
        
        # Tags (Checkboxes)
        ctk.CTkLabel(frame_formulario, text="Tags:").pack(padx=10, pady=(10, 0), anchor="w")
        mapa_vars_tag = self._configurar_checkboxes(frame_formulario, gestor_etiquetas)

        # Precargar datos si es edición
        if es_edicion and articulo:
            entrada_titulo.insert(0, articulo.get("title", ""))
            caja_texto.insert("1.0", articulo.get("text", ""))
            
            # Se necesita un método auxiliar en Logica.py para obtener el nombre (email) a partir del ID.
            # (Este método no está en el código base, pero es necesario para que funcione la edición del autor).
            # Asumiendo que existe:
            # nombre_autor = user_manager.obtener_nombre_por_id(articulo.get("user_id")) 
            # if nombre_autor:
            #    menu_opciones_usuario.set(nombre_autor)
            
            # Marcar checkboxes iniciales.
            self._marcar_valores_iniciales(mapa_vars_categoria, articulo.get("categories", []))
            self._marcar_valores_iniciales(mapa_vars_tag, articulo.get("tags", []))

        # Botón Guardar
        comando_guardar = lambda: self.guardar_articulo(
            ventana, articulo['_id'] if es_edicion else None, entrada_titulo.get(),
            caja_texto.get("1.0", "end-1c"), menu_opciones_usuario.get(),
            mapa_vars_categoria, mapa_vars_tag
        )
        boton_guardar = ctk.CTkButton(master=frame_formulario, 
                                          text="Guardar Cambios" if es_edicion else "Crear Artículo", 
                                          fg_color="green",
                                          command=comando_guardar)
        boton_guardar.pack(pady=20, padx=10)
        if es_edicion and articulo:
        # El ID del artículo actual.
         id_articulo = articulo['_id'] 
        
        ctk.CTkLabel(frame_formulario, text="--- Comentarios ---", font=("Arial", 16, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        
        # 1. Caja de texto para mostrar comentarios existentes
        caja_comentarios = ctk.CTkTextbox(frame_formulario, width=500, height=150, font=("Consolas", 11))
        caja_comentarios.pack(padx=10, pady=5)
        caja_comentarios.configure(state="disabled")
        
        # Función para cargar y mostrar los comentarios
        def recargar_comentarios():
            comentarios = gestor_comentarios.obtener_comentarios_por_articulo(id_articulo)
            caja_comentarios.configure(state="normal")
            caja_comentarios.delete("1.0", "end")
            texto = f"({len(comentarios)} Comentarios)\n"
            
            for c in comentarios:
                autor_email = c.get('author_details', {}).get('email', 'Desconocido')
                fecha_str = c.get('date', datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")
                texto += f"[{autor_email} - {fecha_str}]: {c.get('text', '')}\n"
                texto += "---" + "\n"
                
            caja_comentarios.insert("1.0", texto)
            caja_comentarios.configure(state="disabled")

        recargar_comentarios() # Carga inicial

        # 2. Entrada para nuevo comentario
        ctk.CTkLabel(frame_formulario, text="Agregar Comentario:").pack(padx=10, pady=(10, 0), anchor="w")
        entrada_comentario = ctk.CTkEntry(frame_formulario, width=400, placeholder_text="Escribe tu comentario...")
        entrada_comentario.pack(side="left", padx=(10, 5))
        
        # Lógica para guardar el nuevo comentario
        def agregar_comentario_action():
            texto = entrada_comentario.get()
            # NOTA: Debes tener el ID del usuario LOGUEADO globalmente.
            # Por ahora, usaremos un ID de usuario por defecto (el ID del autor del artículo)
            # o, idealmente, el ID de un usuario que guardaste al hacer login.
            
            # --- CAMBIAR ESTO: Asumiremos que el usuario logueado es el autor del artículo ---
            # DEBES REEMPLAZAR 'articulo.get("user_id")' por una variable global
            # que guarde el ID del usuario que hizo login.
            id_usuario_actual = articulo.get("user_id") 

            if not texto:
                messagebox.showwarning("Vacío", "El comentario no puede estar vacío.", parent=ventana)
                return

            resultado = gestor_comentarios.crear_comentario(id_articulo, id_usuario_actual, texto)
            
            if resultado:
                messagebox.showinfo("Éxito", "Comentario agregado.", parent=ventana)
                entrada_comentario.delete(0, 'end') # Limpia el campo
                recargar_comentarios() # Recarga la vista de comentarios
            else:
                messagebox.showerror("Error", "No se pudo agregar el comentario.", parent=ventana)


        ctk.CTkButton(frame_formulario, text="Comentar", command=agregar_comentario_action).pack(side="left", padx=(5, 10))

    def _configurar_checkboxes(self, frame_padre, gestor):
        """Función auxiliar para crear un conjunto de checkboxes de un gestor (Categorías/Tags)."""
        lista_mapa = []
        nombres = gestor.obtener_todos_los_nombres() 
        
        contenedor = ctk.CTkScrollableFrame(frame_padre, height=100) # Frame con scroll para los checkboxes.
        contenedor.pack(padx=10, pady=5, fill="x")
        
        for nombre in nombres:
            variable = ctk.IntVar(value=0) # Variable para rastrear el estado (0=desmarcado, 1=marcado).
            id_objeto = gestor.obtener_id_por_nombre(nombre)
            
            checkbox = ctk.CTkCheckBox(contenedor, text=nombre, variable=variable)
            checkbox.pack(anchor="w", padx=10)
            lista_mapa.append((variable, id_objeto)) # Almacena la variable y el ID asociado.
        
        return lista_mapa
    
    def _marcar_valores_iniciales(self, mapa_vars, ids_actuales):
        """Auxiliar para marcar los checkboxes que ya están seleccionados en edición."""
        for variable, id_objeto in mapa_vars:
            if id_objeto in ids_actuales:
                variable.set(1)

    def guardar_articulo(self, ventana, id_articulo, titulo, texto, nombre_usuario, mapa_vars_categoria, mapa_vars_tag):
        """Lógica para guardar (crear o editar) un artículo en la base de datos."""
        if not titulo or not texto or nombre_usuario == "No hay usuarios":
            messagebox.showwarning("Campos Requeridos", "El Título, Texto y Autor son obligatorios.", parent=ventana)
            return
            
        try:
            # Obtiene el ObjectId del autor usando el mapa cache del gestor.
            id_usuario = gestor_usuarios.obtener_id_por_nombre(nombre_usuario)
            if not id_usuario:
                messagebox.showerror("Error", "Autor no válido.", parent=ventana)
                return

            # Filtra y recolecta los IDs de las categorías y tags marcados.
            ids_categorias = [ _id for var, _id in mapa_vars_categoria if var.get() == 1 ]
            ids_tags = [ _id for var, _id in mapa_vars_tag if var.get() == 1 ]

            # Crea el documento base.
            datos_nuevo_articulo = {
                "title": titulo,
                "text": texto,
                "user_id": id_usuario,
                "categories": ids_categorias,
                "tags": ids_tags 
            }
            
            if id_articulo:
                # Si hay ID, es una ACTUALIZACIÓN
                datos_nuevo_articulo["last_modified"] = datetime.datetime.now()
                self.coleccion_articulos.update_one({"_id": id_articulo}, {"$set": datos_nuevo_articulo})
                messagebox.showinfo("Éxito", "Artículo actualizado exitosamente.", parent=ventana)
            else:
                # Si no hay ID, es una CREACIÓN
                datos_nuevo_articulo["date"] = datetime.datetime.now()
                self.coleccion_articulos.insert_one(datos_nuevo_articulo)
                messagebox.showinfo("Éxito", "Artículo creado exitosamente.", parent=ventana)

            ventana.destroy() # Cierra la ventana modal.
            self.cargar_articulos() # Recarga la lista principal para ver los cambios.
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el artículo:\n{e}", parent=ventana)
    
    def eliminar_articulo(self):
        """Elimina un artículo por ID."""
        id_articulo = self.entrada_id_articulo.get()
        if not id_articulo:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del artículo que desea eliminar.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el artículo con ID: {id_articulo}?", parent=self.raiz):
            try:
                # Usa ObjectId para la eliminación.
                resultado = self.coleccion_articulos.delete_one({"_id": ObjectId(id_articulo)})
                if resultado.deleted_count > 0:
                    messagebox.showinfo("Éxito", "Artículo eliminado exitosamente.")
                    self.entrada_id_articulo.delete(0, 'end')
                    self.cargar_articulos() 
                else:
                    messagebox.showerror("Error", "No se encontró el artículo con ese ID.")
            except Exception as e:
                messagebox.showerror("ID Inválido", f"El ID proporcionado no es válido o hubo un error: {e}")


    # --- LÓGICA DE GESTIÓN GENÉRICA (Tags, Categorías, Usuarios) ---
    
    def crear_frame_crud_generico(self, titulo, gestor, clave_nombre="name"):
        """Crea un frame CRUD genérico reutilizable para entidades simples."""
        frame = ctk.CTkFrame(self.frame_contenido_principal, fg_color="transparent")
        
        ctk.CTkLabel(frame, text=f"Gestión de {titulo}", font=("Arial", 20, "bold")).pack(pady=10)
        
        # ... [El resto de la construcción de widgets genéricos es similar a create_article_frame] ...
        # (Se omite por brevedad en los comentarios, pero sigue la misma lógica).

        # Controles (Crear)
        frame_crear = ctk.CTkFrame(frame)
        frame_crear.pack(pady=5, padx=10, fill="x")

        etiqueta_entrada = "Nombre:" if clave_nombre == "name" else "Email:"
        ctk.CTkLabel(frame_crear, text=etiqueta_entrada).pack(side="left", padx=(10, 5))
        
        entrada_crear = ctk.CTkEntry(frame_crear, placeholder_text=f"Nuevo {etiqueta_entrada.lower().replace(':','')}", width=250)
        entrada_crear.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ctk.CTkButton(frame_crear, text=f"Crear {titulo[:-1]}", command=lambda: self.crear_item_generico(gestor, entrada_crear.get(), clave_nombre, entrada_crear)).pack(side="left", padx=(5, 10))

        # Textbox para mostrar la lista
        caja_texto = ctk.CTkTextbox(frame, width=760, height=450, font=("Consolas", 13))
        caja_texto.pack(pady=10, padx=10, fill="both", expand=True)
        caja_texto.configure(state="disabled")

        # Controles (Editar/Eliminar)
        frame_accion = ctk.CTkFrame(frame)
        frame_accion.pack(pady=5, padx=10, fill="x")

        entrada_id = ctk.CTkEntry(frame_accion, placeholder_text="ID del elemento para acción", width=250)
        entrada_id.pack(side="left", padx=(10, 5))

        entrada_editar = ctk.CTkEntry(frame_accion, placeholder_text=f"Nuevo {etiqueta_entrada.lower().replace(':','')}", width=250)
        entrada_editar.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            frame_accion, 
            text="Actualizar", 
            command=lambda: self.actualizar_item_generico(gestor, entrada_id.get(), entrada_editar.get(), clave_nombre, entrada_editar),
            fg_color="orange"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_accion, 
            text="Eliminar", 
            command=lambda: self.eliminar_item_generico(gestor, entrada_id.get()),
            fg_color="red"
        ).pack(side="left", padx=(5, 10))

        # Almacena referencias necesarias en el frame
        frame.textbox = caja_texto
        frame.clave_nombre = clave_nombre
        frame.entrada_crear = entrada_crear
        frame.entrada_id = entrada_id
        
        return frame

    def cargar_lista_generica(self, gestor, caja_texto, clave_nombre):
        """Carga y muestra la lista de entidades genéricas (Tags, Categorías, Usuarios)."""
        gestor.cargar_mapa() # Recarga el mapa cache antes de obtener todo.
        lista_datos = gestor.obtener_todos() # Llama al CRUD genérico LECTURA.
        
        caja_texto.configure(state="normal")
        caja_texto.delete("1.0", "end")
        
        texto_a_mostrar = f"--- Lista de {gestor.coleccion.name.capitalize()} ---\n\n"
        
        if not lista_datos:
            texto_a_mostrar += "No hay elementos."
        else:
            for item in lista_datos:
                valor_clave = item.get(clave_nombre, "N/A")
                texto_a_mostrar += f"ID: {item['_id']} | {clave_nombre.capitalize()}: {valor_clave}\n"
                
                if clave_nombre == "email" and item.get("name"):
                    texto_a_mostrar += f"  Nombre: {item['name']}\n"
                
                if clave_nombre == "email" and item.get("password"):
                    texto_a_mostrar += f"  Contraseña: *** (oculta)\n" # Ocultar la contraseña por seguridad.
                
                texto_a_mostrar += "-"*40 + "\n"
                
        caja_texto.insert("1.0", texto_a_mostrar)
        caja_texto.configure(state="disabled")

    def crear_item_generico(self, gestor, valor, clave_nombre, widget_entrada):
        """Crea una nueva entidad genérica (Tag, Categoría, Usuario)."""
        if not valor:
            messagebox.showwarning("Faltan Datos", f"El campo {clave_nombre.capitalize()} es obligatorio.")
            return

        datos = {clave_nombre: valor}
        # Lógica especial para Usuarios (asigna nombre y contraseña por defecto).
        if gestor.coleccion.name == "users":
            datos = {"email": valor, "name": "Usuario Nuevo", "password": "123"} 
            
        id_insertado = gestor.crear_uno(datos) # Llama al CRUD genérico CREACIÓN.
        
        if id_insertado:
            messagebox.showinfo("Éxito", f"{gestor.coleccion.name[:-1].capitalize()} creado exitosamente con ID: {id_insertado}")
            widget_entrada.delete(0, 'end')
            self.seleccionar_frame_por_nombre(gestor.coleccion.name) # Recarga la lista.
        else:
            messagebox.showerror("Error", f"No se pudo crear el elemento en {gestor.coleccion.name}.")

    def actualizar_item_generico(self, gestor, id_item, nuevo_valor, clave_nombre, widget_entrada):
        """Actualiza una entidad genérica por ID."""
        if not id_item or not nuevo_valor:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID y el nuevo valor.")
            return

        try:
            id_objeto = ObjectId(id_item)
            datos_a_actualizar = {clave_nombre: nuevo_valor}
            
            # Llama al CRUD genérico ACTUALIZACIÓN.
            modificado_count = gestor.actualizar_uno(id_objeto, datos_a_actualizar) 
            
            if modificado_count > 0:
                messagebox.showinfo("Éxito", f"{gestor.coleccion.name[:-1].capitalize()} actualizado exitosamente.")
                widget_entrada.delete(0, 'end')
                self.seleccionar_frame_por_nombre(gestor.coleccion.name) # Recarga la lista.
            else:
                messagebox.showwarning("Advertencia", "No se encontró el elemento o no hubo cambios.")

        except Exception as e:
            messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido o hubo un error: {e}")

    def eliminar_item_generico(self, gestor, id_item):
        """Elimina una entidad genérica por ID."""
        if not id_item:
            messagebox.showwarning("Faltan Datos", "Ingrese el ID del elemento que desea eliminar.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar el elemento con ID: {id_item} de {gestor.coleccion.name}?", parent=self.raiz):
            try:
                # Llama al CRUD genérico ELIMINACIÓN.
                resultado = gestor.eliminar_uno(ObjectId(id_item))
                
                if resultado > 0:
                    messagebox.showinfo("Éxito", f"Elemento de {gestor.coleccion.name} eliminado exitosamente.")
                    frame = self.frames[gestor.coleccion.name]
                    frame.entrada_id.delete(0, 'end')
                    self.seleccionar_frame_por_nombre(gestor.coleccion.name) # Recarga la lista.
                else:
                    messagebox.showerror("Error", "No se encontró el elemento con ese ID.")
            except Exception as e:
                messagebox.showerror("ID Inválido", f"El ID proporcionado no es un ObjectId válido o hubo un error: {e}")


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    # Configuración de apariencia antes de crear la ventana principal.
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    raiz_app = ctk.CTk()
    logica_app = AppMenuPrincipal(raiz_app) 
    raiz_app.mainloop() # Inicia el bucle de la GUI.