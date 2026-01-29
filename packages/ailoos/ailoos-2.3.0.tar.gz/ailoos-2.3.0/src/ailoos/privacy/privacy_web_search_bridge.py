"""
Privacy Web Search Bridge - Búsquedas web anónimas sin rastreo

Este módulo proporciona funcionalidades para búsquedas web completamente anónimas,
integrando múltiples motores de búsqueda enfocados en privacidad como DuckDuckGo,
Startpage, Qwant y SearXNG.

Características principales:
- Sin cookies ni tracking pixels
- User-Agent rotativo para evitar fingerprinting
- Soporte opcional para proxies anónimos (Tor/i2p)
- Integración inteligente con sistemas de chat/RAG
- Cache inteligente con TTL
- Gestión de resultados estructurada y filtrada
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, urljoin

import aiohttp
import requests
from duckduckgo_search import DDGS

# Configurar logging
logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logger.warning("BeautifulSoup not available, Startpage parsing limited")

@dataclass
class SearchResult:
    """Resultado estructurado de búsqueda"""
    title: str
    url: str
    snippet: str
    score: float
    date: Optional[str] = None
    engine: str = ""

@dataclass
class SearchOptions:
    """Opciones de búsqueda"""
    engine: str = "duckduckgo"  # duckduckgo, startpage, qwant, searxng
    max_results: int = 5
    language: str = "es"
    region: str = "es-es"
    safe_search: bool = True
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    timeout: int = 10

class PrivacyWebSearchBridge:
    """
    Bridge para búsquedas web anónimas con máxima privacidad
    """

    # User-Agents rotativos para evitar fingerprinting
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar el bridge de búsqueda web privada

        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.cache: Dict[str, Dict] = {}
        self.search_history: List[Dict] = []
        self.session = None
        self._session_initialized = False

        # Cargar historial si existe
        self._load_history()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Cargar configuración desde archivo o usar defaults"""
        default_config = {
            "web_search_enabled": True,
            "preferred_engine": "duckduckgo",
            "max_results": 5,
            "cache_ttl_hours": 1,
            "use_proxy": False,
            "proxy_url": None,
            "searxng_instances": ["https://searx.org"],
            "history_file": "web_search_history.json"
        }

        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Error loading config: {e}")

        return default_config

    def _load_history(self):
        """Cargar historial desde archivo"""
        history_file = self.config.get('history_file', 'web_search_history.json')
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                self.search_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.search_history = []

    def _save_history(self):
        """Guardar historial a archivo"""
        history_file = self.config.get('history_file', 'web_search_history.json')
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def save_config(self, config_path: Optional[str] = None):
        """Guardar configuración actual a archivo"""
        save_path = config_path or self.config_path or 'web_search_config.json'
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def update_config(self, updates: Dict[str, Any]):
        """Actualizar configuración con nuevos valores"""
        self.config.update(updates)
        self.save_config()
        logger.info("Configuration updated")

    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return self.config.copy()

    async def _ensure_session(self):
        """Asegurar que la sesión HTTP esté inicializada"""
        if self.session and not self.session.closed:
            return

        connector_kwargs = {
            'limit': 10,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
            'keepalive_timeout': 60
        }

        # Añadir proxy si está configurado
        if self.config.get('use_proxy') and self.config.get('proxy_url'):
            connector_kwargs['limit'] = 5  # Reducir conexiones con proxy
            # Nota: aiohttp proxy se configura en la request, no en connector

        connector = aiohttp.TCPConnector(**connector_kwargs)

        timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 10))

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_random_headers()
        )

        self._session_initialized = True

    def _get_random_headers(self) -> Dict[str, str]:
        """Generar headers aleatorios para máxima privacidad"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def search_web(self, query: str, options: Optional[SearchOptions] = None) -> List[SearchResult]:
        """
        Realizar búsqueda web anónima

        Args:
            query: Consulta de búsqueda
            options: Opciones de búsqueda

        Returns:
            Lista de resultados estructurados
        """
        if not self.is_web_search_enabled():
            logger.info("Web search disabled")
            return []

        if options is None:
            options = SearchOptions()

        # Asegurar que la sesión esté inicializada
        await self._ensure_session()

        # Verificar cache primero
        cache_key = self._get_cache_key(query, options)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for: {query}")
            return cached_result

        # Realizar búsqueda según motor
        results = []
        try:
            if options.engine == "duckduckgo":
                results = await self._search_duckduckgo(query, options)
            elif options.engine == "startpage":
                results = await self._search_startpage(query, options)
            elif options.engine == "qwant":
                results = await self._search_qwant(query, options)
            elif options.engine == "searxng":
                results = await self._search_searxng(query, options)
            else:
                logger.error(f"Unsupported search engine: {options.engine}")
                return []

            # Filtrar y rankear resultados
            filtered_results = self._filter_and_rank_results(results, options)

            # Cachear resultados
            self._cache_results(cache_key, filtered_results)

            # Agregar a historial
            self._add_to_history(query, options, len(filtered_results))

            return filtered_results

        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []

    async def _search_duckduckgo(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Buscar usando DuckDuckGo API"""
        results = []

        try:
            # Usar duckduckgo-search library (sin API key requerida)
            with DDGS() as ddgs:
                search_results = list(ddgs.text(
                    query,
                    region=options.region,
                    safesearch='strict' if options.safe_search else 'moderate',
                    max_results=options.max_results * 2  # Obtener más para filtrar
                ))

            for result in search_results:
                results.append(SearchResult(
                    title=result.get('title', ''),
                    url=result.get('href', ''),
                    snippet=result.get('body', ''),
                    score=0.8,  # Score base, se ajustará después
                    engine="duckduckgo"
                ))

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")

        return results

    async def _search_startpage(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Buscar usando Startpage (proxy de Google sin logs)"""
        # Implementación básica - Startpage no tiene API pública fácil
        # Usar scraping con headers de privacidad
        results = []

        try:
            search_url = f"https://www.startpage.com/sp/search?q={query}&language={options.language}&cat=web"

            headers = self._get_random_headers()
            headers.update({
                "Referer": "https://www.startpage.com/",
                "Origin": "https://www.startpage.com"
            })

            proxy = self.config.get('proxy_url') if self.config.get('use_proxy') else None

            async with self.session.get(search_url, headers=headers, proxy=proxy) as response:
                if response.status == 200:
                    html = await response.text()
                    results = self._parse_startpage_html(html)

        except Exception as e:
            logger.error(f"Startpage search error: {e}")

        return results

    async def _search_qwant(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Buscar usando Qwant"""
        results = []

        try:
            search_url = f"https://api.qwant.com/v3/search/web?q={query}&locale={options.language}&safesearch=1"

            proxy = self.config.get('proxy_url') if self.config.get('use_proxy') else None

            async with self.session.get(search_url, headers=self._get_random_headers(), proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data.get('data', {}).get('result', {}).get('items', {}).get('mainline', []):
                        if 'items' in item:
                            for result_item in item['items']:
                                results.append(SearchResult(
                                    title=result_item.get('title', ''),
                                    url=result_item.get('url', ''),
                                    snippet=result_item.get('desc', ''),
                                    score=0.7,
                                    engine="qwant"
                                ))

        except Exception as e:
            logger.error(f"Qwant search error: {e}")

        return results

    async def _search_searxng(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Buscar usando SearXNG (meta-buscador auto-alojado)"""
        results = []

        proxy = self.config.get('proxy_url') if self.config.get('use_proxy') else None

        # Intentar múltiples instancias de SearXNG
        for instance_url in self.config.get('searxng_instances', []):
            try:
                search_url = f"{instance_url}/search?q={query}&format=json&categories=general"

                async with self.session.get(search_url, headers=self._get_random_headers(), proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        for result in data.get('results', []):
                            results.append(SearchResult(
                                title=result.get('title', ''),
                                url=result.get('url', ''),
                                snippet=result.get('content', ''),
                                score=0.6,
                                date=result.get('publishedDate'),
                                engine="searxng"
                            ))

                        if results:  # Si encontramos resultados, parar
                            break

            except Exception as e:
                logger.error(f"SearXNG search error for {instance_url}: {e}")
                continue

        return results

    def _parse_startpage_html(self, html: str) -> List[SearchResult]:
        """Parsear HTML de Startpage usando BeautifulSoup"""
        results = []

        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available for Startpage parsing")
            return results

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Startpage usa clases específicas para resultados
            result_divs = soup.find_all('div', class_='result')

            for div in result_divs[:10]:  # Limitar a 10 resultados
                title_elem = div.find('h3') or div.find('a', class_='result-title')
                url_elem = div.find('a', class_='result-title')
                snippet_elem = div.find('p', class_='result-snippet') or div.find('span', class_='result-description')

                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    url = url_elem.get('href', '')

                    # Startpage a veces usa URLs relativas o de redirección
                    if url.startswith('/'):
                        url = f"https://www.startpage.com{url}"
                    elif not url.startswith('http'):
                        continue  # Skip invalid URLs

                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        score=0.75,  # Score base para Startpage
                        engine="startpage"
                    ))

        except Exception as e:
            logger.error(f"Error parsing Startpage HTML: {e}")

        return results

    def _filter_and_rank_results(self, results: List[SearchResult], options: SearchOptions) -> List[SearchResult]:
        """Filtrar y rankear resultados"""
        # Filtrar resultados vacíos o spam
        filtered = [r for r in results if r.title and r.url and len(r.snippet) > 10]

        # Rankear por relevancia (simplificado)
        for result in filtered:
            # Ajustar score basado en autoridad del dominio, frescura, etc.
            domain = urlparse(result.url).netloc
            if 'wikipedia.org' in domain:
                result.score += 0.2
            elif 'gov' in domain or 'edu' in domain:
                result.score += 0.1

        # Ordenar por score descendente
        filtered.sort(key=lambda x: x.score, reverse=True)

        # Limitar resultados
        return filtered[:options.max_results]

    def _get_cache_key(self, query: str, options: SearchOptions) -> str:
        """Generar clave de cache"""
        key_data = f"{query}_{options.engine}_{options.max_results}_{options.language}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[List[SearchResult]]:
        """Obtener resultado cacheado si válido"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.config['cache_ttl_hours'] * 3600:
                return cached['results']
            else:
                del self.cache[cache_key]
        return None

    def _cache_results(self, cache_key: str, results: List[SearchResult]):
        """Cachear resultados"""
        self.cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }

    def _add_to_history(self, query: str, options: SearchOptions, result_count: int):
        """Agregar búsqueda al historial"""
        self.search_history.append({
            'query': query,
            'engine': options.engine,
            'timestamp': time.time(),
            'result_count': result_count
        })

        # Limitar historial a 1000 entradas
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]

        # Guardar historial cada 10 búsquedas
        if len(self.search_history) % 10 == 0:
            self._save_history()

    def get_search_results(self, query: str) -> List[SearchResult]:
        """
        Obtener resultados formateados para IA (wrapper síncrono)

        Args:
            query: Consulta de búsqueda

        Returns:
            Resultados formateados
        """
        # Ejecutar búsqueda asíncrona en bucle de eventos
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si ya hay un loop corriendo, usar asyncio.create_task
                task = asyncio.create_task(self.search_web(query))
                # Nota: En implementación real, manejar mejor el async
                return []  # Placeholder
            else:
                return loop.run_until_complete(self.search_web(query))
        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []

    def is_web_search_enabled(self) -> bool:
        """Verificar si la búsqueda web está habilitada"""
        return self.config.get('web_search_enabled', True)

    def clear_search_history(self):
        """Limpiar historial de búsquedas local"""
        self.search_history.clear()
        self._save_history()
        logger.info("Search history cleared")

    def get_search_history(self) -> List[Dict]:
        """Obtener historial de búsquedas"""
        return self.search_history.copy()

    def set_preferred_engine(self, engine: str):
        """Establecer motor de búsqueda preferido"""
        valid_engines = ['duckduckgo', 'startpage', 'qwant', 'searxng']
        if engine in valid_engines:
            self.config['preferred_engine'] = engine
            logger.info(f"Preferred engine set to: {engine}")
        else:
            logger.error(f"Invalid engine: {engine}")

    def detect_web_search_need(self, query: str) -> bool:
        """
        Detectar automáticamente si una consulta necesita búsqueda web

        Args:
            query: Consulta del usuario

        Returns:
            True si se recomienda búsqueda web
        """
        if not self.is_web_search_enabled():
            return False

        # Palabras clave que indican necesidad de información actual
        current_info_keywords = [
            'precio', 'cotización', 'valor', 'actual', 'hoy', 'ahora',
            'último', 'reciente', 'nuevo', 'noticia', 'evento',
            'resultado', 'puntuación', 'marcador', 'tiempo', 'clima',
            'pronóstico', 'predicción', 'estadística', 'dato'
        ]

        query_lower = query.lower()

        # Verificar si contiene palabras clave de información actual
        for keyword in current_info_keywords:
            if keyword in query_lower:
                return True

        # Verificar patrones como "qué es X", "quién es Y" para entidades
        entity_patterns = [
            'qué es', 'quien es', 'qué fue', 'quién fue',
            'dónde está', 'cuándo fue', 'cómo funciona'
        ]

        for pattern in entity_patterns:
            if pattern in query_lower:
                return True

        # Verificar preguntas con números o datos cuantitativos
        if any(char.isdigit() for char in query) and ('?' in query or 'cuánto' in query_lower):
            return True

        return False

    def enrich_context_with_search(self, query: str, context: str = "") -> str:
        """
        Enriquecer contexto con resultados de búsqueda web

        Args:
            query: Consulta original
            context: Contexto existente

        Returns:
            Contexto enriquecido con información web
        """
        if not self.detect_web_search_need(query):
            return context

        try:
            # Obtener resultados de búsqueda
            search_results = self.get_search_results(query)

            if not search_results:
                return context

            # Formatear resultados para inclusión en prompt
            web_context = "\n\nInformación actual de la web:\n"

            for i, result in enumerate(search_results[:3], 1):  # Top 3 resultados
                web_context += f"{i}. {result.title}\n"
                web_context += f"   URL: {result.url}\n"
                web_context += f"   {result.snippet}\n\n"

            # Combinar con contexto existente
            if context:
                return f"{context}\n{web_context}"
            else:
                return web_context

        except Exception as e:
            logger.error(f"Error enriching context with search: {e}")
            return context

    def get_fallback_knowledge(self, query: str) -> str:
        """
        Proporcionar conocimiento base cuando falla la búsqueda web

        Args:
            query: Consulta que falló

        Returns:
            Conocimiento base como fallback
        """
        # Implementación simplificada - en producción tendría base de conocimiento
        fallbacks = {
            'precio bitcoin': 'El precio del Bitcoin fluctúa constantemente. Recomiendo verificar fuentes confiables como CoinMarketCap o CoinGecko.',
            'tiempo madrid': 'Para información del tiempo actual, consulta servicios meteorológicos como AEMET o El Tiempo.',
            'noticias': 'Para noticias actualizadas, visita medios confiables como BBC, Reuters o El País.'
        }

        query_lower = query.lower()
        for key, value in fallbacks.items():
            if key in query_lower:
                return value

        return "No pude acceder a información web actual. Mi conocimiento está limitado a datos hasta mi último entrenamiento."

    async def close(self):
        """Cerrar sesión HTTP y guardar datos"""
        # Guardar historial y configuración antes de cerrar
        self._save_history()
        self.save_config()

        if self.session:
            await self.session.close()
            self.session = None

    def __del__(self):
        """Destructor para asegurar cierre de sesión"""
        if hasattr(self, 'session') and self.session:
            # Nota: En async context, esto podría no funcionar bien
            pass