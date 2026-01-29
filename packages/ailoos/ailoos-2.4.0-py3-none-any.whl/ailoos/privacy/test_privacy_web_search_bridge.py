"""
Tests para Privacy Web Search Bridge

Tests unitarios y de integración para validar funcionalidad de búsquedas web anónimas.
"""

import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from .privacy_web_search_bridge import PrivacyWebSearchBridge, SearchOptions, SearchResult


class TestPrivacyWebSearchBridge(unittest.TestCase):
    """Tests unitarios para PrivacyWebSearchBridge"""

    def setUp(self):
        """Configurar tests"""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write(json.dumps({
            "web_search_enabled": True,
            "preferred_engine": "duckduckgo",
            "max_results": 3,
            "cache_ttl_hours": 1,
            "use_proxy": False,
            "history_file": "test_history.json"
        }))
        self.temp_config.close()

    def tearDown(self):
        """Limpiar después de tests"""
        os.unlink(self.temp_config.name)
        if os.path.exists("test_history.json"):
            os.unlink("test_history.json")

    def _create_bridge(self):
        """Crear bridge para tests que no requieren sesión"""
        bridge = PrivacyWebSearchBridge.__new__(PrivacyWebSearchBridge)
        bridge.config_path = self.temp_config.name
        bridge.config = bridge._load_config(self.temp_config.name)
        bridge.cache = {}
        bridge.search_history = []
        bridge.session = None
        bridge._session_initialized = False
        bridge._load_history()
        return bridge

    def test_initialization(self):
        """Test inicialización del bridge"""
        bridge = self._create_bridge()
        self.assertTrue(bridge.is_web_search_enabled())
        self.assertEqual(bridge.config['preferred_engine'], 'duckduckgo')
        self.assertIsInstance(bridge.search_history, list)

    def test_detect_web_search_need(self):
        """Test detección automática de necesidad de búsqueda web"""
        # Consultas que deberían requerir búsqueda
        self.assertTrue(self.bridge.detect_web_search_need("¿Cuál es el precio del Bitcoin hoy?"))
        self.assertTrue(self.bridge.detect_web_search_need("¿Quién ganó las elecciones 2024?"))
        self.assertTrue(self.bridge.detect_web_search_need("¿Cuántos habitantes tiene Madrid?"))

        # Consultas que no deberían requerir búsqueda
        self.assertFalse(self.bridge.detect_web_search_need("¿Cuál es la capital de Francia?"))
        self.assertFalse(self.bridge.detect_web_search_need("Explica la teoría de la relatividad"))

    def test_get_cache_key(self):
        """Test generación de claves de cache"""
        options = SearchOptions(engine="duckduckgo", max_results=5)
        key1 = self.bridge._get_cache_key("test query", options)
        key2 = self.bridge._get_cache_key("test query", options)
        key3 = self.bridge._get_cache_key("different query", options)

        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

    @patch('src.ailoos.privacy.privacy_web_search_bridge.DDGS')
    def test_duckduckgo_search(self, mock_ddgs):
        """Test búsqueda con DuckDuckGo"""
        # Mock del contexto manager
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.__exit__.return_value = None
        mock_instance.text.return_value = [
            {'title': 'Test Title', 'href': 'https://example.com', 'body': 'Test snippet'}
        ]
        mock_ddgs.return_value = mock_instance

        async def run_test():
            options = SearchOptions(engine="duckduckgo")
            results = await self.bridge._search_duckduckgo("test query", options)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, 'Test Title')
            self.assertEqual(results[0].engine, 'duckduckgo')

        asyncio.run(run_test())

    def test_filter_and_rank_results(self):
        """Test filtrado y ranking de resultados"""
        results = [
            SearchResult("Spam Title", "http://spam.com", "spam content", 0.5),
            SearchResult("Good Title", "https://wikipedia.org/test", "good content", 0.8),
            SearchResult("Empty Title", "", "", 0.3),
        ]

        options = SearchOptions(max_results=2)
        filtered = self.bridge._filter_and_rank_results(results, options)

        # Debería filtrar el resultado vacío y spam
        self.assertEqual(len(filtered), 2)
        # Wikipedia debería tener score más alto
        self.assertTrue(filtered[0].score >= filtered[1].score)

    def test_config_management(self):
        """Test gestión de configuración"""
        # Actualizar configuración
        self.bridge.update_config({"preferred_engine": "startpage", "max_results": 10})

        self.assertEqual(self.bridge.config['preferred_engine'], 'startpage')
        self.assertEqual(self.bridge.config['max_results'], 10)

        # Verificar que se guardó
        with open(self.temp_config.name, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config['preferred_engine'], 'startpage')

    def test_history_management(self):
        """Test gestión de historial"""
        # Agregar entradas al historial
        options = SearchOptions()
        self.bridge._add_to_history("test query 1", options, 5)
        self.bridge._add_to_history("test query 2", options, 3)

        self.assertEqual(len(self.bridge.search_history), 2)
        self.assertEqual(self.bridge.search_history[0]['query'], 'test query 1')
        self.assertEqual(self.bridge.search_history[1]['result_count'], 3)

        # Limpiar historial
        self.bridge.clear_search_history()
        self.assertEqual(len(self.bridge.search_history), 0)

    def test_fallback_knowledge(self):
        """Test conocimiento de fallback"""
        fallback = self.bridge.get_fallback_knowledge("precio bitcoin")
        self.assertIn("CoinMarketCap", fallback)

        fallback = self.bridge.get_fallback_knowledge("consulta desconocida")
        self.assertIn("conocimiento está limitado", fallback)

    def test_enrich_context(self):
        """Test enriquecimiento de contexto"""
        # Mock search results
        with patch.object(self.bridge, 'get_search_results', return_value=[
            SearchResult("Bitcoin Price", "https://coinmarketcap.com", "Current price: $50,000", 0.9)
        ]):
            enriched = self.bridge.enrich_context_with_search("¿Precio Bitcoin hoy?", "Contexto existente")

            self.assertIn("Información actual de la web", enriched)
            self.assertIn("Contexto existente", enriched)
            self.assertIn("Bitcoin Price", enriched)

    def test_privacy_headers(self):
        """Test headers de privacidad"""
        headers = self.bridge._get_random_headers()

        self.assertIn("User-Agent", headers)
        self.assertEqual(headers["DNT"], "1")  # Do Not Track
        self.assertIn("Accept-Language", headers)

        # Verificar que User-Agent cambia
        headers2 = self.bridge._get_random_headers()
        self.assertNotEqual(headers["User-Agent"], headers2["User-Agent"])


class TestSearchOptions(unittest.TestCase):
    """Tests para SearchOptions"""

    def test_default_options(self):
        """Test opciones por defecto"""
        options = SearchOptions()

        self.assertEqual(options.engine, "duckduckgo")
        self.assertEqual(options.max_results, 5)
        self.assertEqual(options.language, "es")
        self.assertTrue(options.safe_search)


class TestSearchResult(unittest.TestCase):
    """Tests para SearchResult"""

    def test_search_result_creation(self):
        """Test creación de SearchResult"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            score=0.85,
            date="2024-01-01",
            engine="duckduckgo"
        )

        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.score, 0.85)
        self.assertEqual(result.engine, "duckduckgo")


class TestIntegration(unittest.TestCase):
    """Tests de integración"""

    def setUp(self):
        self.bridge = PrivacyWebSearchBridge()

    @patch('src.ailoos.privacy.privacy_web_search_bridge.DDGS')
    def test_full_search_workflow(self, mock_ddgs):
        """Test flujo completo de búsqueda"""
        # Mock DuckDuckGo
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.__exit__.return_value = None
        mock_instance.text.return_value = [
            {'title': 'Bitcoin Price Today', 'href': 'https://coinmarketcap.com', 'body': 'Current price is $45,000'}
        ]
        mock_ddgs.return_value = mock_instance

        async def run_test():
            # Primera búsqueda
            results1 = await self.bridge.search_web("precio bitcoin hoy")
            self.assertEqual(len(results1), 1)

            # Verificar cache
            results2 = await self.bridge.search_web("precio bitcoin hoy")
            self.assertEqual(results1, results2)

            # Verificar historial
            history = self.bridge.get_search_history()
            self.assertEqual(len(history), 2)  # Dos búsquedas

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()