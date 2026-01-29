from ftplib import all_errors
import json
import time
from .exceptions import MondayAPIError
from .http import monday_request
from .fragments import ALL_COLUMNS_FRAGMENT
import logging
from datetime import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # o configurable vía entorno

class MondayClient:
    def __init__(self, api_key: str, base_url: str = "https://api.monday.com/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "API-Version": "2025-10"
        }

    def execute_query(
        self,
        query: str,
        *,
        return_key: str | None = None,
        log_query_preview: bool = False,
        timeout: float | None = None,
        variables: dict | None = None
        ) -> dict:
        """
        Ejecuta una consulta o mutación GraphQL contra la API de Monday.

        Este método actúa como la capa pública del cliente:
        - valida la query
        - opcionalmente registra una vista previa para debug
        - delega la ejecución HTTP, reintentos y manejo de errores a `monday_request`
        - valida la estructura de la respuesta
        - devuelve `data` o un subcampo concreto mediante `return_key`

        Parámetros
        ----------
        query : str
            Cadena GraphQL completa (query o mutation). Debe ser una cadena no vacía.
        return_key : str | None, opcional
            Si se indica, devuelve directamente `data[return_key]`. Útil para mutaciones
            que siempre devuelven un nodo raíz conocido (por ejemplo: "create_item").
        log_query_preview : bool, opcional
            Si es True, registra una vista previa de la query (primeros ~200 caracteres)
            para facilitar el debug, evitando volcar contenido sensible.
        timeout : float | None, opcional
            Timeout en segundos para la petición HTTP. Si es None, se usa el comportamiento
            por defecto de la capa de transporte.
        variables : dict | None, opcional
            Variables GraphQL asociadas a la query. Si es None, la petición se envía
            sin variables.

        Returns
        -------
        dict
            El objeto `data` devuelto por la API GraphQL, o `data[return_key]` si se ha
            especificado `return_key`.

        Raises
        ------
        ValueError
            Si `query` no es una cadena o está vacía.
        MondayAPIError
            Si ocurre un error HTTP, de red, de autenticación, de rate limit,
            o si la API GraphQL devuelve errores, o si la respuesta no contiene
            el campo `data`.
        """


        if not isinstance(query, str) or not query.strip():
            raise ValueError("execute_query: 'query' debe ser una cadena GraphQL no vacía")

        t0 = time.time()
        if log_query_preview:
            # Evitamos volcar todo por si hay datos sensibles
            preview = " ".join(query.split())[:200]
            logger.debug("GraphQL preview: %s%s", preview, "…" if len(preview) == 200 else "")

        resp = monday_request(self.base_url, self.headers, query, variables=variables, timeout=timeout)  # mantiene tu flujo actual

        # Validación de estructura
        if not isinstance(resp, dict):
            raise MondayAPIError(error_code='INVALID_RESPONSE', error_message=f"Respuesta inválida (tipo {type(resp).__name__}): {resp!r}", query=query)

        if "data" not in resp:
            raise MondayAPIError(error_code='INVALID_RESPONSE', error_message=f"Respuesta inesperada (sin 'data'): {resp!r}", query=query)
        

        data = resp["data"]

        if return_key is not None:
            if return_key not in data:
                raise MondayAPIError(error_code='KEY_NOT_EXISTS', error_message=f"Clave '{return_key}' no encontrada en data. Claves disponibles: {list(data.keys())}", query=query)
            return data[return_key]

        return data

    def test_connection(self) -> bool:
        """
        Verifica si la API de Monday.com está accesible y válida para la clave proporcionada.

        Envía una consulta sencilla al endpoint `me` y comprueba si la respuesta
        incluye el objeto de usuario actual.

        Returns
        -------
        bool
            True si la llamada GraphQL devolvió un objeto `me` válido; False si
            ocurrió un error (clave inválida, sin permisos, u otros errores de API).
        """
        query = """
        query {
            me {
                id
                name
                email
            }
        }
        """
        try:
            data = self.execute_query(query)
            return "me" in data
        except MondayAPIError as e:
            return False
    
    
    def get_boards(
            self,
            limit: int = 10,
            page: int = 1,
            
            fields: list[str] | str | None = None,
        ) -> list[dict]:
        """
        Devuelve una lista paginada de tableros (boards).

        Parámetros
        ----------
        limit : int, opcional
            Máximo de tableros a devolver (por defecto 10). Debe ser > 0.
        page : int, opcional
            Página a recuperar (por defecto 1). Debe ser >= 1.
        fields : list[str] | str | None, opcional
            Campos GraphQL a solicitar por board. Si es:
            - None  -> usa ['id','name','workspace_id','state','board_kind'].
            - list  -> cada elemento es una línea/campo que se unirá con "\n".
            - str   -> se inyecta tal cual (permite bloques complejos).

        Returns
        -------
        list[dict]
            Lista de boards con los campos solicitados.

        Raises
        ------
        ValueError
            Si `limit` <= 0 o `page` < 1.
        MondayAPIError
            Si la API devuelve errores.
        """
        if limit <= 0:
            raise ValueError(f"get_boards: 'limit' debe ser > 0")
        if page < 1:
            raise ValueError(f"get_boards: 'page' debe ser >= 1")

        if fields is None:
            fields_block = "\n".join(["id", "name", "workspace_id", "state", "board_kind"])
        elif isinstance(fields, list):
            if not all(isinstance(f, str) and f.strip() for f in fields):
                raise ValueError("get_boards: todos los elementos de 'fields' deben ser strings no vacíos")
            fields_block = "\n".join(fields)
        elif isinstance(fields, str):
            if not fields.strip():
                raise ValueError("get_boards: 'fields' string no puede estar vacío")
            fields_block = fields
        else:
            raise ValueError("get_boards: 'fields' debe ser None, list[str] o str")

        query = f"""
        query {{
        boards(limit: {limit}, page: {page}) {{
            {fields_block}
        }}
        }}
        """

        boards = self.execute_query(query, return_key="boards")
        logger.debug("get_boards: recuperados %d boards (limit=%d, page=%d)", len(boards), limit, page)
        return boards

    def get_all_items(
            self,
            board_id: int,
            limit: int = 50,
            *,
            subitems: str | None = None,
            fields: list[str] | str | None = None,
            columns_ids: list[str] | None = None,
            get_group: bool = False
        ) -> list[dict]:
        """
        Recupera **todos** los ítems de un tablero de Monday.com utilizando paginación
        por cursor (`items_page` / `next_items_page`).

        Este método itera automáticamente hasta agotar el cursor y devuelve la lista
        completa de ítems según los campos solicitados.

        Notas importantes
        -----------------
        - Los parámetros después de `*` son **keyword-only**, forzando llamadas explícitas
        y más legibles.
        - Si `fields` es None, se utiliza un bloque por defecto equivalente a:
        `id`, `name` y `column_values { ALL_COLUMNS_FRAGMENT }`, con filtrado opcional
        por `columns_ids`.
        - La paginación sigue el patrón oficial de Monday:
            1) `boards { items_page(limit) { cursor, items { ... } } }`
            2) Mientras `cursor` no sea null → `next_items_page(limit, cursor)`
        - Si `subitems` se indica, su contenido se inyecta directamente en el bloque
        de campos GraphQL (permite consultas avanzadas de subitems).

        Parámetros
        ----------
        board_id : int
            ID del tablero del que se quieren recuperar los ítems.
        limit : int, opcional
            Número de ítems por página en cada petición. Por defecto 50.
            Debe ser mayor que 0.
        subitems : str | None, keyword-only, opcional
            Bloque GraphQL adicional para recuperar subitems. Se inserta tal cual
            dentro del bloque de campos del ítem.
        fields : list[str] | str | None, keyword-only, opcional
            Campos GraphQL a solicitar por cada ítem:
            - None  → usa el bloque por defecto (`id`, `name`, `column_values`).
            - list[str] → cada elemento se unirá con saltos de línea.
            - str  → se inyecta directamente (permite bloques GraphQL complejos).
        columns_ids : list[str] | None, keyword-only, opcional
            Lista de IDs de columnas a devolver dentro de `column_values`.
            Si se indica, se genera `column_values(ids: [...]) { ... }`.
            Si es None, se devuelven todas las columnas definidas en el fragmento
            por defecto.
        get_group: bool = False
            Si se envia como True, la query devolverá el id y titulo del grupo al que pertenece el item

        Returns
        -------
        list[dict]
            Lista con todos los ítems del tablero, acumulados a través de todas
            las páginas de resultados.

        Raises
        ------
        ValueError
            Si `limit <= 0` o si los tipos/valores de `fields` no son válidos.
        MondayAPIError
            Si la API de Monday devuelve errores HTTP, GraphQL o una respuesta
            inesperada durante la paginación.

        Ejemplos
        --------
        >>> client.get_all_items(12345)
        >>> client.get_all_items(12345, fields=["id", "name"])
        >>> client.get_all_items(12345, columns_ids=["status", "date"])
        >>> client.get_all_items(12345, subitems="subitems { id name }")
        """


        # --- column_values(ids: ...) opcional ---
        ids_arg = f"(ids:{json.dumps(columns_ids)})" if columns_ids else ""

        subitems_query = subitems if subitems else ""
        group_query = "group { id title }" if get_group else ""

        # --- fields (mantener tu default) ---
        if fields is None:
            # Igual que tu versión, pero aplicando ids_arg si viene:
            fields_block = "\n".join([
                "id",
                "name",
                f"{group_query}"
                f"column_values{ids_arg} {{ {ALL_COLUMNS_FRAGMENT} }}",
                f"{subitems_query}",
                
            ])
        elif isinstance(fields, list):
            if not all(isinstance(f, str) and f.strip() for f in fields):
                raise ValueError("get_all_items: todos los 'fields' de la lista deben ser strings no vacíos")
            fields_block = "\n".join(fields)
        elif isinstance(fields, str):
            if not fields.strip():
                raise ValueError("get_all_items: 'fields' string no puede estar vacío")
            fields_block = fields
        else:
            raise ValueError("get_all_items: 'fields' debe ser None, list[str] o str")
        
        # 1) Primera página: items_page anidado en boards
        query_first = f"""
        query {{
        boards(ids: [{board_id}]) {{
            items_page(limit: {limit}) {{
            cursor
            items {{
                {fields_block}
            }}
            }}
        }}
        }}
        """

        data = self.execute_query(query_first)
        boards = data.get("boards", [])
        if not boards:
            logger.warning("No se recuperó ningún tablero para board_id=%s", board_id)
            return []

        page   = boards[0]["items_page"]
        items  = page.get("items", []) or []
        cursor = page.get("cursor")

        # 2) Mientras exista cursor, usar next_items_page en el root
        while cursor:
            query_next = f"""
            query {{
            next_items_page(limit: {limit}, cursor: "{cursor}") {{
                cursor
                items {{
                {fields_block}
                }}
            }}
            }}
            """
            nxt   = self.execute_query(query_next)
            page  = nxt.get("next_items_page", {})
            items.extend(page.get("items", []) or [])
            cursor = page.get("cursor")

        return items

    def create_item(
            self,
            board_id: int,
            item_name: str,
            *,
            group_id: str | None = None,
            columns: list[dict] | dict | None = None,
            fail_on_duplicate: bool = True,
            allow_name_in_columns: bool = False,
            create_labels_if_missing: bool = True,
            return_fields: list[str] | str | None = None,
        ) -> dict:
        """
        Crea un item en un tablero de Monday.com.

        Esta función acepta los valores de columnas "en bruto" (misma estructura que
        `create_column_values`) y los convierte internamente mediante esa helper,
        para que el caller no tenga que llamarla por separado.

        Parámetros
        ----------
        board_id : int
            ID del tablero donde crear el item.
        item_name : str
            Nombre del item (columna “Name” de Monday).
        group_id : str | None, keyword-only
            Grupo destino. Si es None, Monday usará el grupo por defecto.
        columns : list[dict] | dict | None, keyword-only
            - list[dict]: entradas con la forma:
                {"id": "status", "type": "status", "value": "Hecho"}
            u otras variantes que tu `create_column_values` soporta.
            - dict: column_values ya renderizado (por compatibilidad).
            - None: sin valores de columna adicionales.
        fail_on_duplicate : bool, keyword-only
            Se pasa a `create_column_values` para controlar ids duplicadas.
        allow_name_in_columns : bool, keyword-only
            Si False (por defecto), se prohíbe que `columns` incluya la columna
            'name' para evitar conflicto con `item_name`.
        create_labels_if_missing : bool, keyword-only
            Activar creación de etiquetas si no existen (Status/Dropdown).
        return_fields : list[str] | str | None, keyword-only
            Campos a devolver del nodo `create_item`. Si:
            - None -> "id"
            - list -> se unirán con saltos de línea
            - str  -> se inyecta tal cual (permite bloques complejos)

        Returns
        -------
        dict
            El subobjeto `data.create_item` con los campos solicitados.

        Raises
        ------
        ValueError
            Tipos/valores inválidos, o conflicto entre `item_name` y columna 'name'.
        MondayAPIError
            Errores devueltos por la API.

        Ejemplos
        --------
        >>> client.create_item(
        ...     12345, "Nuevo lead",
        ...     columns=[
        ...         {"id":"status","type":"status","value":"Nuevo"},
        ...         {"id":"email","type":"email","value":{"email":"a@b.com","text":"Contacto"}}],
        ... )
        {'id': '987654321'}

        >>> # También admite column_values ya construidos:
        >>> client.create_item(12345, "Ticket", columns={"status": {"index": 1}})
        {'id': '...'}
        """

        if not isinstance(board_id, (int, str)):
            raise ValueError("create_item: 'board_id' debe ser int o str")

        if isinstance(board_id, int) and board_id <= 0:
            raise ValueError("create_item: 'board_id' debe ser un entero > 0")

        if isinstance(board_id, str) and not board_id.strip():
            raise ValueError("create_item: 'board_id' string no puede estar vacío")
        
        if not isinstance(item_name, str) or not item_name.strip():
            raise ValueError("create_item: 'item_name' debe ser una cadena no vacía")
        if return_fields is None:
            fields_block = "id"
        elif isinstance(return_fields, list):
            if not all(isinstance(f, str) and f.strip() for f in return_fields):
                raise ValueError("create_item: 'return_fields' lista debe contener strings no vacíos")
            fields_block = "\n".join(return_fields)
        elif isinstance(return_fields, str):
            if not return_fields.strip():
                raise ValueError("create_item: 'return_fields' string no puede estar vacío")
            fields_block = return_fields
        else:
            raise ValueError("create_item: 'return_fields' debe ser None, list[str] o str")

        # 1) Normalizar column_values
        if columns is None:
            column_values: dict = {}
        elif isinstance(columns, dict):
            column_values = columns  # compatibilidad: ya vienen renderizados
        elif isinstance(columns, list):
            column_values = self.create_column_values(columns, fail_on_duplicate=fail_on_duplicate)
        else:
            raise ValueError("create_item: 'columns' debe ser None, dict o list[dict]")

        # 2) Evitar conflicto con 'name' salvo que se permita explícitamente
        if not allow_name_in_columns and ("name" in column_values or "pulse.name" in column_values):
            raise ValueError(
                "create_item: no incluyas la columna 'name' en 'columns'; "
                "usa el parámetro 'item_name' o establece allow_name_in_columns=True bajo tu responsabilidad."
            )

        # 3) Serializar column_values como JSON string (GraphQL exige string JSON escapado)
        #    Técnica: primero dumps a dict -> str JSON; luego re-dumps para que el GraphQL reciba comillas escapadas.
        colvals_json = json.dumps(column_values, ensure_ascii=False, separators=(",", ":"))
        colvals_arg = json.dumps(colvals_json, ensure_ascii=False)  # string JSON escapado

        # 4) Construir args
        args = [f"board_id: {board_id}"]
        if group_id:
            args.append(f'group_id: "{group_id}"')
        args.append(f'item_name: {json.dumps(item_name, ensure_ascii=False)}')
        if create_labels_if_missing:
            args.append("create_labels_if_missing: true")
        args.append(f"column_values: {colvals_arg}")
        args_str = ", ".join(args)

        mutation = f"""
        mutation {{
        create_item({args_str}) {{
            {fields_block}
        }}
        }}
        """

        return self.execute_query(mutation, return_key="create_item")


    def create_subitem(
            self,
            parent_item_id: int,
            subitem_name: str,
            *,
            columns: list[dict] | dict | None = None,
            fail_on_duplicate: bool = True,
            create_labels_if_missing: bool = True,
            return_fields: list[str] | str | None = None,
        ) -> dict:
        """
        Crea un subítem bajo un ítem padre en Monday.com.

        Ahora también se permite incluir la columna 'name' en `columns` para
        sobreescribir el nombre inicial.

        Parámetros
        ----------
        parent_item_id : int
            ID del ítem padre bajo el que se creará el subítem.
        subitem_name : str
            Texto que se asignará como nombre del subítem (si además pasas 'name'
            en `columns`, ese valor puede sobrescribirlo).
        columns : list[dict] | dict | None, keyword-only
            - list[dict]: entradas como {"id": "...", "type": "...", "value": ...}
            que `create_column_values` sabrá normalizar.
            - dict: column_values ya renderizado (compatibilidad).
            - None: sin valores de columna adicionales.
        fail_on_duplicate : bool, keyword-only
            Propagado a `create_column_values` (control de IDs duplicadas).
        create_labels_if_missing : bool, keyword-only
            Activa la creación de labels inexistentes (Status/Dropdown).
        return_fields : list[str] | str | None, keyword-only
            Campos a devolver del nodo `create_subitem`.

        Returns
        -------
        dict
            El subobjeto `data.create_subitem` con los campos solicitados.
        """
        import json

        if not isinstance(parent_item_id, int) or parent_item_id <= 0:
            raise ValueError("create_subitem: 'parent_item_id' debe ser un entero > 0")
        if not isinstance(subitem_name, str) or not subitem_name.strip():
            raise ValueError("create_subitem: 'subitem_name' debe ser una cadena no vacía")

        # --- Campos de retorno ---
        if return_fields is None:
            fields_block = "id"
        elif isinstance(return_fields, list):
            if not all(isinstance(f, str) and f.strip() for f in return_fields):
                raise ValueError("create_subitem: 'return_fields' lista debe contener strings no vacíos")
            fields_block = "\n".join(return_fields)
        elif isinstance(return_fields, str):
            if not return_fields.strip():
                raise ValueError("create_subitem: 'return_fields' string no puede estar vacío")
            fields_block = return_fields
        else:
            raise ValueError("create_subitem: 'return_fields' debe ser None, list[str] o str")

        # --- Normalizar column_values ---
        if columns is None:
            column_values: dict = {}
        elif isinstance(columns, dict):
            column_values = columns
        elif isinstance(columns, list):
            column_values = self.create_column_values(columns, fail_on_duplicate=fail_on_duplicate)
        else:
            raise ValueError("create_subitem: 'columns' debe ser None, dict o list[dict]")

        # --- Serializar para GraphQL ---
        json_payload = json.dumps(column_values, ensure_ascii=False, separators=(",", ":"))
        escaped = json.dumps(json_payload, ensure_ascii=False)

        args = [
            f"parent_item_id: {parent_item_id}",
            f'item_name: {json.dumps(subitem_name, ensure_ascii=False)}',
        ]
        if create_labels_if_missing:
            args.append("create_labels_if_missing: true")
        args.append(f"column_values: {escaped}")
        args_str = ", ".join(args)

        mutation = f"""
        mutation {{
        create_subitem({args_str}) {{
            {fields_block}
        }}
        }}
        """

        return self.execute_query(mutation, return_key="create_subitem")

    def update_simple_column_value(
        self,
        item_id: int,
        board_id: int,
        column_id: str,
        value: str,
        *,
        return_fields: list[str] | str | None = None,
    ) -> dict:
        """
        Actualiza el valor de **una** columna sencilla de un ítem (mutación `change_simple_column_value`).

        Importante
        ----------
        - Este método **no** usa `create_column_values`. El `value` se pasa **como string** en los args GraphQL.
        - `value` es **obligatorio**. Para **borrar** el contenido de la columna, pásalo como **cadena vacía**: "".
        - Si la columna espera JSON (p. ej. una `date`), debes pasar **tú** el JSON **serializado como string**:
            value='{"date":"2025-09-24"}'

        Parámetros
        ----------
        item_id : int
            ID del ítem a modificar.
        board_id : int
            ID del tablero del ítem.
        column_id : str
            ID de la columna a actualizar.
        value : str, keyword-only
            String a establecer. Ejemplos:
            - Texto simple: "Hola mundo"
            - Número en columnas numéricas: "123.45"
            - Limpiar valor: ""   (cadena vacía)
            - Fecha: '{"date":"2025-09-24"}' (JSON serializado en string)
        return_fields : list[str] | str | None, keyword-only
            Campos a devolver de `change_simple_column_value`. Por defecto "id".

        Returns
        -------
        dict
            Subobjeto `data.change_simple_column_value` con los campos solicitados.

        Raises
        ------
        ValueError
            Si los parámetros son inválidos.
        MondayAPIError
            Si la API devuelve errores.
        """
        import json

        if not isinstance(item_id, int) or item_id <= 0:
            raise ValueError("update_simple_column_value: 'item_id' debe ser entero > 0")
        if not isinstance(board_id, int) or board_id <= 0:
            raise ValueError("update_simple_column_value: 'board_id' debe ser entero > 0")
        if not isinstance(column_id, str) or not column_id.strip():
            raise ValueError("update_simple_column_value: 'column_id' debe ser string no vacío")
        if not isinstance(value, str):
            raise ValueError("update_simple_column_value: 'value' debe ser str (usa '' para borrar)")

        # Campos de retorno
        if return_fields is None:
            fields_block = "id"
        elif isinstance(return_fields, list):
            if not all(isinstance(f, str) and f.strip() for f in return_fields):
                raise ValueError("update_simple_column_value: 'return_fields' lista con strings no vacíos")
            fields_block = "\n".join(return_fields)
        elif isinstance(return_fields, str):
            if not return_fields.strip():
                raise ValueError("update_simple_column_value: 'return_fields' string no puede estar vacío")
            fields_block = return_fields
        else:
            raise ValueError("update_simple_column_value: 'return_fields' debe ser None, list[str] o str")

        # Escapar como literal de GraphQL (string entrecomillado)
        value_arg = json.dumps(value, ensure_ascii=False)
        column_id_arg = json.dumps(column_id, ensure_ascii=False)

        query = f"""
        mutation {{
        change_simple_column_value(
            item_id: {item_id},
            board_id: {board_id},
            column_id: {column_id_arg},
            value: {value_arg}
        ) {{
            {fields_block}
        }}
        }}
        """

        return self.execute_query(query, return_key="change_simple_column_value")
    
    def update_multiple_column_values(
            self,
            item_id: int,
            board_id: int,
            columns: list[dict] | dict,
            *,
            fail_on_duplicate: bool = True,
            create_labels_if_missing: bool = True,
            return_fields: list[str] | str | None = None,
        ) -> dict:
        """
        Actualiza **varias** columnas de un ítem (mutación `change_multiple_column_values`).

        - Acepta `columns` “en bruto” (lista de dicts) con la misma forma que entiende
        `create_column_values`, y esta función se encargará de **normalizarlas**.
        - Si ya traes un `dict` listo (column_values renderizado), también se acepta.
        - `column_values` se envía como **string JSON** (doble `json.dumps`).

        Parámetros
        ----------
        item_id : int
            ID del ítem a actualizar.
        board_id : int
            ID del tablero que contiene el ítem.
        columns : list[dict] | dict
            - list[dict]: e.g.
                [
                {"id":"status","type":"status","value":"Hecho"},
                {"id":"date","type":"date","value":{"date":"2025-09-24"}}
                ]
            - dict: column_values ya renderizado (compatibilidad).
        fail_on_duplicate : bool, keyword-only
            Se pasa a `create_column_values` para controlar IDs duplicadas.
        create_labels_if_missing : bool, keyword-only
            Activa la creación de etiquetas inexistentes (Status/Dropdown).
        return_fields : list[str] | str | None, keyword-only
            Campos que quieres del nodo `change_multiple_column_values` (por defecto "id").

        Returns
        -------
        dict
            Subobjeto `data.change_multiple_column_values` con los campos solicitados.

        Raises
        ------
        ValueError
            Si los parámetros son inválidos o `columns` está vacío.
        MondayAPIError
            Si la API devuelve errores.
        """
        import json

        # ---- Validaciones básicas ----
        if not isinstance(item_id, int) or item_id <= 0:
            raise ValueError("update_multiple_column_values: 'item_id' debe ser entero > 0")
        if not isinstance(board_id, int) or board_id <= 0:
            raise ValueError("update_multiple_column_values: 'board_id' debe ser entero > 0")
        if isinstance(columns, list) and len(columns) == 0:
            raise ValueError("update_multiple_column_values: 'columns' no puede ser lista vacía")
        if not isinstance(columns, (list, dict)):
            raise ValueError("update_multiple_column_values: 'columns' debe ser list[dict] o dict")

        # ---- Preparar column_values ----
        if isinstance(columns, dict):
            column_values = columns  # ya renderizado (compat)
        else:
            column_values = self.create_column_values(columns, fail_on_duplicate=fail_on_duplicate)

        # GraphQL exige string JSON -> doble dumps
        colvals_json = json.dumps(column_values, ensure_ascii=False, separators=(",", ":"))
        colvals_arg = json.dumps(colvals_json, ensure_ascii=False)

        # ---- Campos de retorno ----
        if return_fields is None:
            fields_block = "id"
        elif isinstance(return_fields, list):
            if not all(isinstance(f, str) and f.strip() for f in return_fields):
                raise ValueError("update_multiple_column_values: 'return_fields' lista con strings no vacíos")
            fields_block = "\n".join(return_fields)
        elif isinstance(return_fields, str):
            if not return_fields.strip():
                raise ValueError("update_multiple_column_values: 'return_fields' string no puede estar vacío")
            fields_block = return_fields
        else:
            raise ValueError("update_multiple_column_values: 'return_fields' debe ser None, list[str] o str")

        args = [
            f"item_id: {item_id}",
            f"board_id: {board_id}",
            f"column_values: {colvals_arg}",
        ]
        if create_labels_if_missing:
            args.append("create_labels_if_missing: true")
        args_str = ", ".join(args)

        mutation = f"""
        mutation {{
        change_multiple_column_values({args_str}) {{
            {fields_block}
        }}
        }}
        """

        return self.execute_query(mutation, return_key="change_multiple_column_values")




    def get_items_by_column_value(
        self,
        board_id: int,
        column_id: str,
        value: str,
        fields: list[str] | None = None,
        operator: str = "any_of",
        limit: int = 200
    ) -> list[dict]:
        """
        Recupera uno o varios ítems de un tablero filtrando por el valor de una columna,
        y paginando automáticamente hasta obtener todos los resultados o agotar el cursor.

        Ejecuta primero una consulta anidada en `boards { items_page }` con filtro
        `query_params.rules`, y luego, mientras el campo `cursor` no sea null,
        va solicitando páginas adicionales a `next_items_page` en el root, acumulando
        todos los ítems en una lista.

        Parameters
        ----------
        board_id : int
            ID del tablero de Monday.com donde buscar.
        column_id : str
            ID de la columna en la que aplicar el filtro.
        value : str
            Valor que se comparará contra el contenido de la columna.
        fields : list[str] | None, optional
            Lista de campos GraphQL a solicitar para cada ítem. Si es None,
            se usarán por defecto `['id', 'name', 'column_values{...}']`
            Con todos los tipos de columnas diferentes en la query, ... on xxxx.
        operator : str, optional
            Operador de comparación permitido por GraphQL (e.g. `any_of`, `not_any_of`,
            `is_empty`, `greater_than`, `contains_text`, etc.). Por defecto `"any_of"`.
            Lista completa de operadores en la doc: any_of, not_any_of, is_empty,
            is_not_empty, greater_than, greater_than_or_equals, lower_than,
            lower_than_or_equal, between, contains_text, not_contains_text,
            contains_terms, starts_with, ends_with, within_the_next,
            within_the_last :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}.
        limit : int, optional
            Número máximo de ítems a devolver por página (por defecto 1).

        Returns
        -------
        list[dict]
            Lista de diccionarios, uno por cada ítem filtrado. Cada dict incluye
            las claves `id`, `name` y `column_values` (con `column.id`, `column.title`
            y `text`).

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        # Montamos la primera consulta con filtro en items_page
        
        if not fields:
            fields = ["id", "name", f"column_values {{ {ALL_COLUMNS_FRAGMENT} }}"]
            fields_block = "\n".join(fields)
            # fields_block = "id name column_values { ... }"
        else:
            fields_block = fields
        
        
        query_first = f"""
        query {{
        boards(ids: [{board_id}]) {{
            items_page(
            limit: {limit},
            query_params: {{
                rules: [{{
                column_id: "{column_id}",
                compare_value: ["{value}"],
                operator: {operator}
                }}]
            }}
            ) {{
            cursor
            items {{
                {fields_block}
            }}
            }}
        }}
        }}
        """

        data = self.execute_query(query_first)
        boards = data.get("boards", [])
        if not boards:
            return []

        page = boards[0]["items_page"]
        items = page.get("items", [])
        cursor = page.get("cursor")

        # Paginación: obtener siguientes páginas desde next_items_page
        while cursor:
            query_next = f"""
            query {{
            next_items_page(
                limit: {limit},
                cursor: "{cursor}"
            ) {{
                cursor
                items {{
                {fields_block}
                }}
            }}
            }}
            """
            nxt = self.execute_query(query_next)
            page = nxt.get("next_items_page", {})
            items.extend(page.get("items", []))
            cursor = page.get("cursor")

        return items
        
        
        
    def get_item(self,
                item_id: int,
                subitems: str | None = None,
                get_group: bool = False,
                columns_ids: list[str] | None = None) -> dict:
        """
        Obtiene un ítem específico de Monday.com por su ID.

        Parameters
        ----------
        item_id : int
            ID del ítem a obtener.
        subitems: str
            String con los datos a obtener de los subitems Ej: subitems {id name}
            es None por defecto
        columns_ids : list[str] | None, optional
            Lista de IDs de columnas a incluir en la respuesta. Si es None, se
            devolverán todas las columnas.
        get_group: bool = False
            Si se envia true devuelve el id y titulo del grupo al que pertenece el item

        Returns
        -------
        dict
            Diccionario con los datos del ítem, incluyendo sus columnas y valores.

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        # 1) argumento para column_values
        if columns_ids:
            # json.dumps -> '["sadfg","sdfs"]'
            cols_list = json.dumps(columns_ids)
            ids_arg = f"(ids:{cols_list})"
        else:
            ids_arg = ""

        # 2) Subitems

        subitems_query = subitems if subitems else ""
        group_query = "group { id title}" if get_group else ""
        
        query = f'''
            query {{
            items(ids:{item_id}) {{
                name
                id
                {subitems_query}
                {group_query}
                column_values{ids_arg} {{
                column{{
                    title
                    id
                }}
                {ALL_COLUMNS_FRAGMENT}
                }}
            }}
            }}
        '''
        
        response = self.execute_query(query)
        items = response.get("items", [])
        
        if not items:
            raise MondayAPIError(f"No se encontró el ítem con ID {item_id}")

        return items[0]
    
    
    
    def board_columns(self, board_id: str) -> list[dict]:
        """
        Obtiene las columnas de un tablero específico de Monday.com.

        Parameters
        ----------
        board_id : int
            ID del tablero cuyas columnas se quieren obtener.

        Returns
        -------
        list[dict]
            Lista de diccionarios, cada uno con los campos `id`, `title`, `type`,
            `settings_str` y `width`.

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        query = f"""
        query {{
            boards(ids: [{board_id}]) {{
                columns {{
                    id
                    title
                    type
                }}
            }}
        }}
        """

        response = self.execute_query(query)
        boards = response.get("boards", [])

        if not boards:
            raise MondayAPIError(f"No se encontró el tablero con ID {board_id}")

        return boards[0]["columns"]
    
    
    def item_columns(self, item_id: str) -> list[dict]:
        """
        Obtiene las columnas de un ítem específico de Monday.com.
        Crea un subitem en un item del tablero, obtiene las columnas y despues lo borra

        Parameters
        ----------
        item_id : int
            ID del ítem cuyas columnas se quieren obtener.

        Returns
        -------
        list[dict]
            Lista de diccionarios, cada uno con los campos `id`, `title`, `type`,
            `settings_str` y `width`.

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                column_values {{
                    column {{
                        id
                        title
                        type
                    }}
                }}
            }}
        }}
        """

        response = self.execute_query(query)
        items = response.get("items", [])

        if not items:
            raise MondayAPIError(f"No se encontró el ítem con ID {item_id}")

        return items[0]["column_values"]
    
    
    


    def subitems_columns(self, board_id:str) -> list[dict]:
        """
        Obtiene las columnas de los subitems de un tablero específico de Monday.com.
        Crea un subitem en un item del tablero, obtiene las columnas y despues lo borra

        Parameters
        ----------
        board : str
            ID del tablero cuyas columnas se quieren obtener.

        Returns
        -------
        list[dict]
            Lista de diccionarios, cada uno con los campos `id`, `title`, `type`,
            `settings_str` y `width`.

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        
        
        # Obtener 1 item del tablero para crear un subitem
        item_id = self.get_all_items(board_id)[0]['id']
                
        #crear un subitem a ese item padre
        subitem = self.create_subitem(item_id,'FLAG')
        
        subitem_id = subitem.get("id")
        
        if not subitem_id:
            raise MondayAPIError(f"No se pudo crear el subitem para verificar las columnas")
        
        subitem_board_id = subitem.get("board", {}).get("id")
        
        #obtener las columnas del subitem_board_id
        columns = self.board_columns(subitem_board_id)
       
        

        #borrar el subitem creado
        delete = self.delete_item(subitem_id)

        if delete is not True:
            raise MondayAPIError(f"No se pudo borrar el subitem")
        
        
        return columns


    def delete_item(self, item_id: str) -> None:
        """
        Elimina un ítem específico de Monday.com por su ID.

        Parameters
        ----------
        item_id : int
            ID del ítem a eliminar.

        Raises
        ------
        MondayAPIError
            Si la consulta GraphQL falla o la API devuelve errores.
        """
        query = f"""
        mutation {{
            delete_item(
                item_id: {item_id}
            ) {{
                id
            }}
        }}
        """

        response = self.execute_query(query)
        if "errors" in response:
            raise MondayAPIError(f"Error al eliminar el ítem con ID {item_id}: {response['errors']}")
        
        return True
    
    
    

    def create_item_update(self,
                            item_id: str,
                            body: str,
                            mention_user:list[dict] = []) -> dict:
            """
            Crea un cambio (update) para un ítem específico en Monday.com.

            Parameters
            ----------
            item_id : str
                ID del ítem al que se le realizará el cambio.
            body : str
                Cuerpo del cambio en formato HTML.
            mention_user : list[dict]
                Lista de diccionarios con los usuarios y tipo a mencionar en el cambio.

            Returns
            -------
            dict
                Diccionario con los datos del cambio creado, incluyendo su ID
                Ejemplo: [{id: 1234567890, type: User}].

            Raises
            ------
            MondayAPIError
                Si la consulta GraphQL falla o la API devuelve errores.
            """
            
            if mention_user:
                clean_mentions = json.dumps(mention_user).replace('"', '')
                mention_user = f"mentions_list:{clean_mentions}"
            else:
                mention_user = ""
            
            
            
            
            query = f"""
            mutation {{
                create_update(
                    item_id: {item_id},
                    body: "{body}",
                    {mention_user}
                ) {{
                    id
                }}
            }}
            """
            
            print(f'query = {query}')

            response = self.execute_query(query)
            if "errors" in response:
                raise MondayAPIError(f"Error al crear el cambio para el ítem con ID {item_id}: {response['errors']}")

            return response["create_update"]
        
        
    def create_column_values(self,
                            columns: list[dict],
                             *,
                            fail_on_duplicate=True):
        """
            Construye un diccionario con los valores de columnas para Monday API.

            Parámetros
            ----------
            columns : list[dict]
                Lista de columnas con el formato:
                [
                    {
                        "id": "column_id",        # ID de la columna en Monday
                        "value": "column_value",  # Valor de la columna
                        "type": "column_type"     # Tipo de la columna
                    },
                    ...
                ]

            fail_on_duplicate : bool, opcional
                Si True (default), lanza un error al encontrar IDs de columna repetidos.
                Si False, el último valor sobreescribe al anterior.

            Tipos soportados
            ----------------
            - checkbox → bool
                {"checked": true/false}

            - board_relation → list[int]
                {"item_ids": [id1, id2, ...]}

            - date → dict con {"date": "YYYY-MM-DD", "time": "HH:MM" (opcional)}

            - dropdown → str o list[str]
                {"labels": ["Opción1", "Opción2", ...]}

            - email → str o dict con {"email": "...", "text": "..."}
                Si se pasa string, se usa como email y como text.

            - link → str o dict con {"url": "...", "text": "..."}
                Si se pasa string, se usa como url y como text.

            - long_text → str

            - name → str
                (aunque normalmente se pasa fuera de column_values en create_item,
                aquí se soporta para updates)

            - numbers → int | float | str numérico
                Siempre se envía como string.

            - people → list[int | dict]
                - Si se pasa int → {"id": int, "kind": "person"}
                - Si se pasa dict → {"id": int, "kind": "person|team"}

            - phone → str o dict con {"phone": "...", "countryShortName": "..."}
                El número se normaliza (sin espacios, guiones ni paréntesis).

            - status → str (label) o int (index)

            - text → str

            - timeline → dict con {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}

            Retorno
            -------
            dict
                Diccionario listo para usar en `column_values`, donde cada clave es
                el `column_id` y el valor corresponde al formato esperado por Monday.
            
            Ejemplo
            -------
            >>> create_column_values([
            ...     {"id": "text_col", "value": "Hola", "type": "text"},
            ...     {"id": "status_col", "value": "Working on it", "type": "status"}
            ... ])
            {
                "text_col": "Hola",
                "status_col": {"label": "Working on it"}
        }
        """
        column_values = {}
        
        for col in columns:
            col_id   = col["id"]
            col_type = col.get("type")
            raw_val  = col.get("value")
            
            if col_id in column_values:
                if fail_on_duplicate:
                    raise ValueError(f"Column id duplicada: {col_id}")
                # Si no fallas, aquí podrías combinar según el tipo.
        
            if col_type == 'checkbox':
                value = {'checked': bool(raw_val)}
            elif col_type == 'board_relation':
                if not isinstance(raw_val, (list, tuple)):
                    raise TypeError(f"{col_id}: board_relation espera lista de IDs")
                value = {'item_ids': list(raw_val)}
            elif col_type == 'date':
                if not isinstance(raw_val, dict):
                    raise TypeError(f"{col_id}: date espera diccionario con al menos 'date'")
                # Validar fecha
                try:
                    datetime.strptime(raw_val['date'], "%Y-%m-%d")
                except (KeyError, ValueError):
                    raise ValueError(f"{col_id}: 'date' debe estar en formato YYYY-MM-DD")
                value = {"date": raw_val['date']}
                # Validar hora si viene
                if 'time' in raw_val:
                    try:
                        datetime.strptime(raw_val['time'], "%H:%M")
                    except ValueError:
                        raise ValueError(f"{col_id}: 'time' debe estar en formato HH:MM (24h)")
                    value["time"] = raw_val['time']
            elif col_type == "dropdown":
                if isinstance(raw_val, str):
                    # Caso: un único valor
                    value = {"labels": [raw_val]}
                elif isinstance(raw_val, (list, tuple)):
                    # Caso: lista de valores
                    if not all(isinstance(v, str) for v in raw_val):
                        raise TypeError(f"{col_id}: dropdown espera lista de strings")
                    value = {"labels": list(raw_val)}
                else:
                    raise TypeError(f"{col_id}: dropdown espera string o lista de strings")
                
            elif col_type == "email":
                if isinstance(raw_val, str):
                    # Si solo pasan un email en string, lo convertimos
                    value = {"email": raw_val, "text": raw_val}
                elif isinstance(raw_val, dict) and "email" in raw_val:
                    if not isinstance(raw_val["email"], str):
                        raise TypeError(f"{col_id}: 'email' debe ser string")
                    value = {
                        "email": raw_val["email"],
                        "text": raw_val.get("text", raw_val["email"])
                    }
                else:
                    raise TypeError(f"{col_id}: email espera string o dict con 'email'")
            
            elif col_type == "link":
                if isinstance(raw_val, str):
                    # Si solo pasan un string, lo tomamos como url y lo usamos también como texto
                    value = {"url": raw_val, "text": raw_val}
                elif isinstance(raw_val, dict) and "url" in raw_val:
                    if not isinstance(raw_val["url"], str):
                        raise TypeError(f"{col_id}: 'url' debe ser string")
                    value = {
                        "url": raw_val["url"],
                        "text": raw_val.get("text", raw_val["url"])
                    }
                else:
                    raise TypeError(f"{col_id}: link espera string o dict con 'url'")
            
            elif col_type == "long_text":
                if not isinstance(raw_val, str):
                    raise TypeError(f"{col_id}: long_text espera un string")
                value = raw_val
                
            elif col_type == "name":
                if not isinstance(raw_val, str):
                    raise TypeError(f"{col_id}: name espera un string")
                # en lugar de meterlo en column_values, lo devolvemos en otro campo
                value = raw_val
                
            elif col_type == "numbers":
                if not isinstance(raw_val, (int, float, str)):
                    raise TypeError(f"{col_id}: numbers espera int, float o string numérico")
                try:
                    # Validamos que realmente se puede convertir a número
                    float(raw_val)
                except ValueError:
                    raise ValueError(f"{col_id}: numbers debe contener un valor numérico válido")
                value = str(raw_val)               
            
            elif col_type == "people":
                if not isinstance(raw_val, (list, tuple)):
                    raise TypeError(f"{col_id}: people espera lista de IDs o lista de dicts con id/kind")

                persons_and_teams = []
                for entry in raw_val:
                    if isinstance(entry, int):
                        # int = persona por defecto
                        persons_and_teams.append({"id": entry, "kind": "person"})
                    elif isinstance(entry, dict):
                        uid = entry.get("id")
                        kind = entry.get("kind", "person")  # por defecto "person" si no se especifica
                        if kind not in ("person", "team"):
                            raise ValueError(f"{col_id}: 'kind' debe ser 'person' o 'team'")
                        persons_and_teams.append({"id": uid, "kind": kind})
                    else:
                        raise TypeError(f"{col_id}: cada valor debe ser int (persona) o dict con id/kind")

                value = {"personsAndTeams": persons_and_teams}
                
            elif col_type == "phone":
                if isinstance(raw_val, str):
                    # Limpiamos espacios, guiones y paréntesis
                    phone_clean = raw_val.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    value = {"phone": phone_clean, "countryShortName": ""}
                elif isinstance(raw_val, dict) and "phone" in raw_val:
                    if not isinstance(raw_val["phone"], str):
                        raise TypeError(f"{col_id}: 'phone' debe ser string")
                    phone_clean = (
                        raw_val["phone"]
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("(", "")
                        .replace(")", "")
                    )
                    value = {
                        "phone": phone_clean,
                        "countryShortName": raw_val.get("countryShortName", "")
                    }
                else:
                    raise TypeError(f"{col_id}: phone espera string o dict con 'phone'")
            
            
            elif col_type == "status":
                if isinstance(raw_val, str):
                    value = {"label": raw_val}
                elif isinstance(raw_val, int):
                    value = {"index": raw_val}
                else:
                    raise TypeError(f"{col_id}: status espera string (label) o int (index)")
            
            elif col_type == "text":
                if not isinstance(raw_val, str):
                    raise TypeError(f"{col_id}: text espera un string")
                value = raw_val
            
            elif col_type == "timeline":
                if not isinstance(raw_val, dict) or not {"from", "to"}.issubset(raw_val):
                    raise TypeError(f"{col_id}: timeline espera dict con 'from' y 'to' en formato YYYY-MM-DD")

                try:
                    datetime.strptime(raw_val["from"], "%Y-%m-%d")
                    datetime.strptime(raw_val["to"], "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{col_id}: 'from' y 'to' deben estar en formato YYYY-MM-DD")

                value = {"from": raw_val["from"], "to": raw_val["to"]}
            
            elif col_type == "country":
                if not isinstance(raw_val, dict) or not {'countryCode', 'countryName'}.issubset(raw_val):
                    raise TypeError(f"{col_id}: country espera un diccionario con las claves 'countryCode' y 'countryName' ")
                
                value = {"countryCode": raw_val['countryCode'], "countryName": raw_val['countryName']}
                

            else: 
                raise KeyError(f'Tipo de columna: "{col_type}", no soportado por create_column_values')
            

            column_values[col_id] = value
                
        
        return column_values
    
    def get_users(
            self,
            limit: int | None = None,
            page: int | None = None,         
            fields: list[str] | str | None = None,
        ) -> list[dict]:
        """
        Recupera una lista paginada de usuarios desde la API de Monday.com.

        Este método envía una query GraphQL `users(limit:, page:)` y devuelve la lista de
        usuarios con los campos solicitados.

        Parámetros
        ----------
        limit : int | None, opcional
            Número máximo de usuarios a devolver por página. Si es None, se utiliza el
            valor por defecto del API (o el que la query permita). Debe ser > 0 cuando
            se indique.
        page : int | None, opcional
            Página a recuperar. Si es None, se utiliza el valor por defecto del API.
            Debe ser >= 1 cuando se indique.
        fields : list[str] | str | None, opcional
            Campos GraphQL a solicitar por usuario:
            - None  -> usa el bloque por defecto (`id` y `name`).
            - list[str] -> cada elemento será una línea/campo y se unirá con saltos de línea.
            - str -> se inyecta tal cual (permite bloques complejos).

        Returns
        -------
        list[dict]
            Lista de usuarios con los campos solicitados.

        Raises
        ------
        ValueError
            Si `limit` es <= 0 o `page` es < 1 (cuando se indiquen), o si `fields` es inválido.
        MondayAPIError
            Si la API devuelve errores o la respuesta es inesperada.
        """

        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("get_users: 'limit' debe ser int o None")
            if limit <= 0:
                raise ValueError("get_users: 'limit' debe ser > 0")

        if page is not None:
            if not isinstance(page, int):
                raise ValueError("get_users: 'page' debe ser int o None")
            if page < 1:
                raise ValueError("get_users: 'page' debe ser >= 1")

        # ---- Fields block ----
        if fields is None:
            fields_block = "\n".join(["id", "name"])
        elif isinstance(fields, list):
            if not all(isinstance(f, str) and f.strip() for f in fields):
                raise ValueError("get_users: todos los elementos de 'fields' deben ser strings no vacíos")
            fields_block = "\n".join(fields)
        elif isinstance(fields, str):
            if not fields.strip():
                raise ValueError("get_users: 'fields' string no puede estar vacío")
            fields_block = fields
        else:
            raise ValueError("get_users: 'fields' debe ser None, list[str] o str")

        # ---- Construcción compacta de args ----
        args = []
        if limit is not None:
            args.append(f"limit: {limit}")
        if page is not None:
            args.append(f"page: {page}")

        args_block = f"({', '.join(args)})" if args else ""

        query = f"""
        query {{
        users{args_block} {{
            {fields_block}
        }}
        }}
        """

        users = self.execute_query(query, return_key="users")
        logger.debug("get_users: recuperados %d users", len(users))
        return users
    
    def send_notification(
        self,
        user_id: int | str,
        target_id: int | str,
        target_type: str,
        text: str
        ) -> str:
        """
        Envía una notificación a un usuario en Monday.com.

        Este método ejecuta la mutación GraphQL `create_notification` y devuelve
        el texto de la notificación creada.

        Parámetros
        ----------
        user_id : int | str
            ID del usuario que recibirá la notificación.
        target_id : int | str
            ID del objeto objetivo de la notificación (por ejemplo, un item o proyecto).
        target_type : str
            Tipo de objeto objetivo. Valores permitidos:
            - "Post"
            - "Project"
        text : str
            Texto de la notificación a enviar. No puede ser una cadena vacía.

        Returns
        -------
        str
            Texto de la notificación creada.

        Raises
        ------
        ValueError
            Si alguno de los parámetros tiene un tipo o valor inválido.
        MondayAPIError
            Si la API de Monday devuelve errores o la mutación falla.
        """

        # ---- Validaciones ----
        if not isinstance(user_id, (int, str)):
            raise ValueError("send_notification: 'user_id' debe ser int o str")

        if not isinstance(target_id, (int, str)):
            raise ValueError("send_notification: 'target_id' debe ser int o str")

        if not isinstance(target_type, str):
            raise ValueError("send_notification: 'target_type' debe ser str")

        if target_type not in {"Post", "Project"}:
            raise ValueError("send_notification: 'target_type' debe ser 'Post' o 'Project'")

        if not isinstance(text, str) or not text.strip():
            raise ValueError("send_notification: 'text' debe ser un string no vacío")

        # ---- Mutación GraphQL ----
        query = f"""
        mutation {{
        create_notification(
            user_id: {user_id}
            target_id: {target_id}
            text: "{text}"
            target_type: {target_type}
        ) {{
            text
        }}
        }}
        """

        r = self.execute_query(query=query, return_key="create_notification")
        notification_text = r['text']
        return notification_text
    
    def get_parent_board(
        self,
        item_id: int | str
        ) -> int | str:
        """
        Obtiene el ID del tablero padre al que pertenece un ítem de Monday.com.

        Este método ejecuta una query GraphQL sobre `items(ids: ...)` y extrae
        el `board.id` asociado al ítem indicado.

        Parámetros
        ----------
        item_id : int | str
            ID del ítem del cual se quiere obtener el tablero padre.

        Returns
        -------
        int | str
            ID del tablero padre al que pertenece el ítem.

        Raises
        ------
        ValueError
            Si `item_id` no es un int o str válido.
        MondayAPIError
            Si la API de Monday devuelve errores o la respuesta es inesperada
            (por ejemplo, si el ítem no existe).
        """

        if not isinstance(item_id, (int, str)):
            raise ValueError("get_parent_board: 'item_id' debe ser int o str")

        if isinstance(item_id, str) and not item_id.strip():
            raise ValueError("get_parent_board: 'item_id' string no puede estar vacío")

        query = f"""
        query {{
        items(ids: {item_id}) {{
            board {{
            id
            }}
        }}
        }}
        """

        result = self.execute_query(query=query, return_key="items")

        parent_board_id = result[0]['board']['id']
        return parent_board_id