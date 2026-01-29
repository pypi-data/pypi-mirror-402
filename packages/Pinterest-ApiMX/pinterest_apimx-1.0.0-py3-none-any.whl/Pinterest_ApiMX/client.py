import requests
import json
import time
import os
import io
from urllib.parse import urlparse
from tqdm.auto import tqdm
from PIL import Image, ImageFilter

class PinterestPro:
    def __init__(self, cookie_file="cookies.json"):
        self.session = requests.Session()
        self.headers = self._load_credentials(cookie_file)
        
    def _load_credentials(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ Falta el archivo: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookies_list = json.load(f)
            
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
            csrf_token = next((c['value'] for c in cookies_list if c['name'] == 'csrftoken'), "")
            
            return {
                "authority": "mx.pinterest.com",
                "accept": "application/json, text/javascript, */*, q=0.01",
                "accept-language": "es-419,es;q=0.9",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
                "x-csrftoken": csrf_token,
                "cookie": cookie_string,
                "x-pinterest-appstate": "background",
            }
        except Exception as e:
            raise Exception(f"Error procesando cookies: {e}")

    # --- UTILIDADES INTERNAS ---
    def _parsear_url(self, url_input):
        if "http" in url_input: path = urlparse(url_input).path
        else: path = url_input if url_input.startswith("/") else "/" + url_input
        parts = [p for p in path.split('/') if p]
        if len(parts) < 2: return None
        return {"full_path": path, "username": parts[0], "slug": parts[1]}

    def _extraer_datos_pin(self, item):
        """Francotirador universal de imágenes"""
        data = item.get('pin') or item
        pin_id = data.get('id') or data.get('node_id')
        
        # Filtros básicos
        if not pin_id: return None
        if data.get('type') == 'home_feed_tabs': return None

        # Descripción limpia para metadatos (opcional)
        desc = "".join(x for x in (data.get('description') or data.get('grid_title') or "pin") if x.isalnum() or x in (' ', '-', '_'))[:50]
        url_img = None

        # 1. Pin Normal
        if 'images' in data:
            img = data.get('images', {})
            url_img = img.get('orig', {}).get('url') or img.get('large', {}).get('url') or img.get('736x', {}).get('url')
        
        # 2. Story Pin (Idea Pin)
        elif 'story_pin_data' in data and data['story_pin_data']:
            try:
                pages = data['story_pin_data'].get('pages_preview', [])
                if pages:
                    blocks = pages[0].get('blocks', [])
                    if blocks:
                        img = blocks[0].get('image', {}).get('images', {})
                        url_img = img.get('originals', {}).get('url') or img.get('1200x', {}).get('url') or img.get('736x', {}).get('url')
            except: pass

        if url_img:
            return {"id": pin_id, "description": desc, "image_url": url_img}
        return None

    # ==========================================
    # 1. BÚSQUEDA (Search)
    # ==========================================
    def search(self, query, limit=50, verbose=True):
        url = "https://mx.pinterest.com/resource/BaseSearchResource/get/"
        results = []
        unique_ids = set()
        bookmark = None

        with tqdm(total=limit, disable=not verbose, unit="pin", desc=f"🔎 Buscando '{query}'") as pbar:
            while len(results) < limit:
                options = {"query": query, "scope": "pins", "page_size": 25, "rs": "typed", "auto_correction_disabled": False}
                if bookmark: options["bookmarks"] = [bookmark]
                
                payload = {
                    "source_url": f"/search/pins/?q={query}",
                    "data": json.dumps({"options": options, "context": {}}),
                    "x_pinterest_rid": "8558201528283275"
                }

                try:
                    resp = self.session.post(url, headers=self.headers, data=payload)
                    if resp.status_code != 200: break
                    
                    data = resp.json()
                    raw_items = data.get('resource_response', {}).get('data', {}).get('results', [])
                    
                    if not raw_items: break

                    for item in raw_items:
                        if len(results) >= limit: break
                        pin_obj = self._extraer_datos_pin(item)
                        if pin_obj and pin_obj['id'] not in unique_ids:
                            unique_ids.add(pin_obj['id'])
                            results.append(pin_obj)
                            pbar.update(1)

                    bookmark = data.get('resource_response', {}).get('bookmark')
                    if not bookmark or bookmark == '-end-': break
                    time.sleep(0.5)
                except: break
        return results

    # ==========================================
    # 2. HOME FEED
    # ==========================================
    def get_home_feed(self, limit=50, verbose=True):
        url = "https://mx.pinterest.com/resource/UserHomefeedResource/get/"
        results = []
        unique_ids = set()
        bookmark = None

        with tqdm(total=limit, disable=not verbose, unit="pin", desc="🏠 Home Feed") as pbar:
            while len(results) < limit:
                options = {"is_prefetch": False, "page_size": 25, "field_set_key": "grid_item", "redux_normalize_feed": True}
                if bookmark: options["bookmarks"] = [bookmark]

                payload = {
                    "source_url": "/",
                    "data": json.dumps({"options": options, "context": {}}),
                    "x_pinterest_rid": "8558201528283275"
                }

                try:
                    resp = self.session.post(url, headers=self.headers, data=payload)
                    if resp.status_code != 200: break

                    data = resp.json()
                    raw_items = data.get('resource_response', {}).get('data', [])
                    if not raw_items: break

                    for item in raw_items:
                        if len(results) >= limit: break
                        pin_obj = self._extraer_datos_pin(item)
                        if pin_obj and pin_obj['id'] not in unique_ids:
                            unique_ids.add(pin_obj['id'])
                            results.append(pin_obj)
                            pbar.update(1)

                    bookmark = data.get('resource_response', {}).get('bookmark')
                    if not bookmark or bookmark == '-end-': break
                    time.sleep(0.5)
                except: break
        return results

    # ==========================================
    # 3. TABLERO (Con ID de Inventario + Headers Falsos)
    # ==========================================
    def _obtener_id_tablero(self, username, slug_buscado):
        url = "https://mx.pinterest.com/resource/BoardsResource/get/"
        options = {"username": username, "page_size": 250, "sort": "last_pinned_to", "privacy_filter": "all", "field_set_key": "detailed"}
        payload = {"source_url": f"/{username}/", "data": json.dumps({"options": options, "context": {}}), "x_pinterest_rid": "8558201528283275"}
        
        headers_post = self.headers.copy()
        headers_post["content-type"] = "application/x-www-form-urlencoded"
        
        try:
            resp = self.session.post(url, headers=headers_post, data=payload)
            tableros = resp.json().get('resource_response', {}).get('data', [])
            for t in tableros:
                if slug_buscado in t.get('url', ''): return t['id']
        except: pass
        return None

    def get_board(self, url_tablero, limit=50, verbose=True):
        info = self._parsear_url(url_tablero)
        if not info: print("❌ URL inválida"); return []

        if verbose: print(f"🕵️‍♂️ Buscando ID de tablero: {info['slug']}...")
        board_id = self._obtener_id_tablero(info['username'], info['slug'])
        if not board_id: print("⛔ No encontrado en tu lista."); return []

        # Headers clave
        self.headers["referer"] = f"https://mx.pinterest.com{info['full_path']}"
        self.headers["x-pinterest-source-url"] = info['full_path']
        self.headers["x-pinterest-pws-handler"] = f"www/[{info['username']}]/[{info['slug']}].js"

        url_api = "https://mx.pinterest.com/resource/BoardFeedResource/get/"
        results = []
        unique_ids = set()
        bookmark = None

        with tqdm(total=limit, disable=not verbose, unit="pin", desc=f"📌 Tablero: {info['slug']}") as pbar:
            while len(results) < limit:
                options = {
                    "board_id": board_id, "board_url": info['full_path'], "currentFilter": -1, 
                    "field_set_key": "partner_react_grid_pin", "filter_section_pins": True, 
                    "sort": "default", "layout": "default", "page_size": 25, "redux_normalize_feed": True
                }
                if bookmark: options["bookmarks"] = [bookmark]

                params = {"source_url": info['full_path'], "data": json.dumps({"options": options, "context": {}}), "_": int(time.time() * 1000)}

                try:
                    resp = self.session.get(url_api, headers=self.headers, params=params)
                    if resp.status_code != 200: break

                    data_json = resp.json()
                    raw_data = data_json.get('resource_response', {}).get('data', [])
                    items = raw_data if isinstance(raw_data, list) else raw_data.get('results', [])
                    if not items: break

                    for item in items:
                        if len(results) >= limit: break
                        pin_obj = self._extraer_datos_pin(item)
                        if pin_obj and pin_obj['id'] not in unique_ids:
                            unique_ids.add(pin_obj['id'])
                            results.append(pin_obj)
                            pbar.update(1)

                    bookmark = data_json.get('resource_response', {}).get('bookmark')
                    if not bookmark or bookmark == '-end-': break
                    time.sleep(0.5)
                except: break
        
        return results

    # ==========================================
    # 4. PROCESAMIENTO DE IMAGEN
    # ==========================================
    def _crear_imagen_cuadrada_difuminada(self, original_img, target_resolution=None):
        """Crea fondo borroso 1:1. Si hay target_resolution (int), redimensiona al final."""
        max_side = max(original_img.size)
        square_size = (max_side, max_side)
        
        background = original_img.resize(square_size, Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=30))
        
        foreground = original_img.copy()
        foreground.thumbnail(square_size, Image.LANCZOS)
        
        bg_w, bg_h = background.size
        fg_w, fg_h = foreground.size
        pos_x = (bg_w - fg_w) // 2
        pos_y = (bg_h - fg_h) // 2
        
        background.paste(foreground, (pos_x, pos_y), foreground if foreground.mode == 'RGBA' else None)
        
        # Redimensionado final si el usuario pidió un tamaño específico (ej. 768)
        if target_resolution and isinstance(target_resolution, int):
            background = background.resize((target_resolution, target_resolution), Image.LANCZOS)
            
        return background

    # ==========================================
    # 5. DESCARGA (JPG TURBO + FIXES)
    # ==========================================
    def download(self, results_list, output_folder="descargas", mode="original", resolution=None, verbose=True):
        """
        Descarga imágenes.
        mode="original": Tal cual viene.
        mode="1:1": Cuadrada con fondo borroso.
        resolution: (Solo para 1:1) Entero con el tamaño deseado, ej: 768.
        """
        if not results_list: return
        if not os.path.exists(output_folder): os.makedirs(output_folder)

        desc = f"⬇️ Bajando (JPG Turbo)"
        if mode == "1:1" and resolution: desc += f" [{resolution}px]"
        
        # Aquí la barra SÍ será exacta porque usarmos len(results_list)
        with tqdm(total=len(results_list), disable=not verbose, unit="img", desc=desc, colour="green") as pbar:
            for pin in results_list:
                try:
                    img_url = pin['image_url']
                    filename = f"{img_url.split('/')[-1].split('.')[0]}.jpg"
                    final_path = os.path.join(output_folder, filename)

                    if os.path.exists(final_path):
                        pbar.update(1); continue

                    response = requests.get(img_url, stream=True, timeout=15)
                    response.raise_for_status()
                    img = Image.open(io.BytesIO(response.content))

                    # --- FIX TRANSPARENCIA (Aplanar RGBA sobre Blanco) ---
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                        fondo = Image.new('RGB', img.size, (255, 255, 255))
                        fondo.paste(img, mask=img.split()[3])
                        img = fondo
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    # -----------------------------------------------------

                    final_img = img
                    if mode == "1:1":
                        # Aplicamos efecto y redimensionado opcional
                        final_img = self._crear_imagen_cuadrada_difuminada(img, target_resolution=resolution)

                    final_img.save(final_path, "JPEG", quality=90, optimize=True)
                    pbar.update(1)

                except Exception as e:
                    if verbose: pbar.write(f"⚠️ Error descarga: {e}")