"""
RAG Configuration

This module provides configuration management for RAG systems,
including default settings and validation.
"""

from typing import Dict, Any, Optional, List
import os
import json
import logging

logger = logging.getLogger(__name__)


class RAGConfig:
    """
    Configuration manager for RAG systems.

    This class provides centralized configuration management with
    validation, defaults, and environment variable support.
    """

    # Default configuration
    DEFAULT_CONFIG = {
        'retriever': {
            'class': 'FAISSStore',
            'config': {
                'dimension': 768,
                'index_type': 'IndexFlatIP',
                'metric': 'cosine'
            }
        },
        'generator': {
            'class': 'EmpoorioLMGenerator',
            'config': {
                'model_name': 'empoorio-lm-v1',
                'max_tokens': 512,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 50,
                'repetition_penalty': 1.1,
                'stream': False
            }
        },
        'evaluator': {
            'class': 'BasicEvaluator',
            'config': {
                'metrics': ['relevance', 'faithfulness', 'informativeness']
            }
        },
        'vector_store': {
            'type': 'faiss',
            'config': {
                'persist_directory': './vector_store'
            }
        },
        'embedding': {
            'model': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimension': 384,
            'batch_size': 32
        },
        'text_splitter': {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'separators': ['\n\n', '\n', '. ', ' ', '']
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'cors_origins': ['*']
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'performance': {
            'max_concurrent_requests': 10,
            'request_timeout': 30.0,
            'cache_enabled': True
        },
        'cache': {
            'enabled': True,
            'model_name': 'all-MiniLM-L6-v2',
            'similarity_threshold': 0.8,
            'max_size': 1000,
            'eviction_policy': 'LRU',
            'cache_file': './cache/rag_cache.pkl',
            'ttl_seconds': 3600
        },
        # EmpoorioLM unified configuration
        'empoorio_lm': {
            'api_config': {
                'model_path': './models/empoorio_lm/v1.0.0',
                'device': 'auto',
                'max_batch_size': 4,
                'max_sequence_length': 512,
                'cache_dir': None,
                'trust_remote_code': False
            },
            'generation_config': {
                'max_new_tokens': 512,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 50,
                'do_sample': True,
                'repetition_penalty': 1.1,
                'pad_token_id': None,
                'eos_token_id': None,
                'bos_token_id': None
            },
            'prompt_config': {
                'template': (
                    "Eres un asistente de IA especializado en proporcionar respuestas precisas y fundamentadas. "
                    "Utiliza únicamente la información proporcionada en el contexto para responder la pregunta del usuario.\n\n"
                    "CONTEXTO DISPONIBLE:\n{context}\n\n"
                    "PREGUNTA DEL USUARIO: {query}\n\n"
                    "INSTRUCCIONES:\n"
                    "- Responde de manera directa y concisa\n"
                    "- Si la información no está en el contexto, indica que no puedes responder basado en la información disponible\n"
                    "- Mantén un tono profesional y helpful\n"
                    "- Si hay múltiples perspectivas, preséntalas claramente\n\n"
                    "RESPUESTA:"
                ),
                'max_context_length': 4000,
                'include_metadata': True
            },
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'burst_limit': 10
            },
            'caching': {
                'enabled': True,
                'max_size': 1000,
                'ttl_seconds': 3600,
                'similarity_threshold': 0.85
            },
            'conversation': {
                'enabled': True,
                'max_turns': 10,
                'context_window': 5
            },
            'fallback': {
                'enabled': True,
                'generators': [
                    {'class': 'MockGenerator', 'config': {}}
                ]
            },
            'metrics': {
                'enabled': True,
                'track_quality': True,
                'track_performance': True
            },
            'ab_testing': {
                'enabled': False,
                'default_variant': 'default',
                'variants': {
                    'creative': {'temperature': 0.9, 'top_p': 0.95},
                    'conservative': {'temperature': 0.3, 'top_p': 0.7},
                    'balanced': {'temperature': 0.7, 'top_p': 0.9}
                }
            },
            'models': {
                'available': ['empoorio-lm-v1', 'empoorio-lm-v2'],
                'current': 'empoorio-lm-v1'
            },
            'safety': {
                'content_filter': True,
                'max_response_length': 2000,
                'banned_phrases': []
            },
            # Maturity 3: Data Governance Configuration
            'preprocessing_config': {
                'enable_audit_log': True,
                'fail_on_pii_detection': False,
                'max_query_length': 10000,
                'steps': [
                    {
                        'name': 'pii_filtering',
                        'config': {
                            'patterns': [],  # Will use default patterns
                            'enable_audit_log': True
                        }
                    },
                    {
                        'name': 'text_normalization',
                        'config': {
                            'lowercase': True,
                            'remove_extra_spaces': True,
                            'normalize_unicode': False
                        }
                    },
                    {
                        'name': 'compliance_validation',
                        'config': {}
                    }
                ]
            },
            'access_control_config': {
                'policies': [
                    {
                        'name': 'default_deny',
                        'access_level': 'restricted',
                        'allowed_roles': ['admin'],
                        'decision': 'deny'
                    },
                    {
                        'name': 'public_access',
                        'access_level': 'public',
                        'decision': 'allow'
                    }
                ],
                'default_access_level': 'internal',
                'enable_audit_log': True
            }
        }
    }

    def __init__(self, config_file: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize RAG configuration.

        Args:
            config_file (Optional[str]): Path to configuration file
            overrides (Optional[Dict[str, Any]]): Configuration overrides
        """
        self.config = self.DEFAULT_CONFIG.copy()

        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)

        # Apply environment variable overrides
        self._load_from_env()

        # Apply runtime overrides
        if overrides:
            self._merge_config(self.config, overrides)

        # Validate configuration
        self._validate_config()

        logger.info("RAG configuration initialized")

    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(self.config, file_config)
            logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_file}: {str(e)}")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # RAG environment variables
        rag_env_mappings = {
            'RAG_API_HOST': ('api', 'host'),
            'RAG_API_PORT': ('api', 'port'),
            'RAG_EMBEDDING_MODEL': ('embedding', 'model'),
            'RAG_LOG_LEVEL': ('logging', 'level'),
            'RAG_MAX_CONCURRENT': ('performance', 'max_concurrent_requests'),
            'RAG_CACHE_ENABLED': ('performance', 'cache_enabled'),
            'RAG_VECTOR_STORE_PATH': ('vector_store', 'config', 'persist_directory'),
            'RAG_CHUNK_SIZE': ('text_splitter', 'chunk_size'),
            'RAG_CHUNK_OVERLAP': ('text_splitter', 'chunk_overlap')
        }

        # EmpoorioLM environment variables
        empoorio_env_mappings = {
            'EMPOORIO_MODEL_PATH': ('empoorio_lm', 'api_config', 'model_path'),
            'EMPOORIO_DEVICE': ('empoorio_lm', 'api_config', 'device'),
            'EMPOORIO_MAX_BATCH_SIZE': ('empoorio_lm', 'api_config', 'max_batch_size'),
            'EMPOORIO_MAX_SEQUENCE_LENGTH': ('empoorio_lm', 'api_config', 'max_sequence_length'),
            'EMPOORIO_TEMPERATURE': ('empoorio_lm', 'generation_config', 'temperature'),
            'EMPOORIO_MAX_TOKENS': ('empoorio_lm', 'generation_config', 'max_new_tokens'),
            'EMPOORIO_TOP_P': ('empoorio_lm', 'generation_config', 'top_p'),
            'EMPOORIO_TOP_K': ('empoorio_lm', 'generation_config', 'top_k'),
            'EMPOORIO_REPETITION_PENALTY': ('empoorio_lm', 'generation_config', 'repetition_penalty'),
            'EMPOORIO_RATE_LIMIT_RPM': ('empoorio_lm', 'rate_limiting', 'requests_per_minute'),
            'EMPOORIO_RATE_LIMIT_RPH': ('empoorio_lm', 'rate_limiting', 'requests_per_hour'),
            'EMPOORIO_CACHE_SIZE': ('empoorio_lm', 'caching', 'max_size'),
            'EMPOORIO_CACHE_TTL': ('empoorio_lm', 'caching', 'ttl_seconds'),
            'EMPOORIO_CONVERSATION_MAX_TURNS': ('empoorio_lm', 'conversation', 'max_turns'),
            'EMPOORIO_METRICS_ENABLED': ('empoorio_lm', 'metrics', 'enabled'),
            'EMPOORIO_AB_TESTING_ENABLED': ('empoorio_lm', 'ab_testing', 'enabled'),
            'EMPOORIO_CURRENT_MODEL': ('empoorio_lm', 'models', 'current'),
            'EMPOORIO_FALLBACK_ENABLED': ('empoorio_lm', 'fallback', 'enabled'),
            # Cache configuration
            'RAG_CACHE_ENABLED': ('cache', 'enabled'),
            'RAG_CACHE_MODEL': ('cache', 'model_name'),
            'RAG_CACHE_SIMILARITY_THRESHOLD': ('cache', 'similarity_threshold'),
            'RAG_CACHE_MAX_SIZE': ('cache', 'max_size'),
            'RAG_CACHE_EVICTION_POLICY': ('cache', 'eviction_policy'),
            'RAG_CACHE_FILE': ('cache', 'cache_file'),
            'RAG_CACHE_TTL': ('cache', 'ttl_seconds')
        }

        # Load RAG environment variables
        for env_var, config_path in rag_env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if isinstance(config_path, tuple) and len(config_path) > 1:
                    if config_path[-1] in ['port', 'max_concurrent_requests', 'chunk_size', 'chunk_overlap']:
                        value = int(value)
                    elif config_path[-1] in ['cache_enabled']:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                self._set_nested_config(self.config, config_path, value)
                logger.debug(f"Set RAG {config_path} from environment: {value}")

        # Load EmpoorioLM environment variables
        for env_var, config_path in empoorio_env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if isinstance(config_path, tuple) and len(config_path) > 1:
                    if config_path[-1] in ['max_batch_size', 'max_sequence_length', 'max_new_tokens',
                                          'top_k', 'requests_per_minute', 'requests_per_hour',
                                          'max_size', 'ttl_seconds', 'max_turns']:
                        value = int(value)
                    elif config_path[-1] in ['temperature', 'top_p', 'repetition_penalty', 'similarity_threshold']:
                        value = float(value)
                    elif config_path[-1] in ['enabled']:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                self._set_nested_config(self.config, config_path, value)
                logger.debug(f"Set EmpoorioLM {config_path} from environment: {value}")

        # Load Cache environment variables
        cache_env_mappings = {
            'RAG_CACHE_ENABLED': ('cache', 'enabled'),
            'RAG_CACHE_MODEL': ('cache', 'model_name'),
            'RAG_CACHE_SIMILARITY_THRESHOLD': ('cache', 'similarity_threshold'),
            'RAG_CACHE_MAX_SIZE': ('cache', 'max_size'),
            'RAG_CACHE_EVICTION_POLICY': ('cache', 'eviction_policy'),
            'RAG_CACHE_FILE': ('cache', 'cache_file'),
            'RAG_CACHE_TTL': ('cache', 'ttl_seconds')
        }

        for env_var, config_path in cache_env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if isinstance(config_path, tuple) and len(config_path) > 1:
                    if config_path[-1] in ['max_size', 'ttl_seconds']:
                        value = int(value)
                    elif config_path[-1] in ['similarity_threshold']:
                        value = float(value)
                    elif config_path[-1] in ['enabled']:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                self._set_nested_config(self.config, config_path, value)
                logger.debug(f"Set Cache {config_path} from environment: {value}")

        # Load Maturity 3 environment variables
        maturity3_env_mappings = {
            'RAG_PREPROCESSING_AUDIT_LOG': ('preprocessing_config', 'enable_audit_log'),
            'RAG_PREPROCESSING_FAIL_ON_PII': ('preprocessing_config', 'fail_on_pii_detection'),
            'RAG_PREPROCESSING_MAX_QUERY_LENGTH': ('preprocessing_config', 'max_query_length'),
            'RAG_ACCESS_CONTROL_AUDIT_LOG': ('access_control_config', 'enable_audit_log'),
            'RAG_ACCESS_CONTROL_DEFAULT_LEVEL': ('access_control_config', 'default_access_level')
        }

        for env_var, config_path in maturity3_env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if isinstance(config_path, tuple) and len(config_path) > 1:
                    if config_path[-1] in ['max_query_length']:
                        value = int(value)
                    elif config_path[-1] in ['enable_audit_log', 'fail_on_pii_detection']:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                self._set_nested_config(self.config, config_path, value)
                logger.debug(f"Set Maturity 3 {config_path} from environment: {value}")

    def _merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]):
        """Recursively merge override configuration into base configuration."""
        for key, value in override_config.items():
            if isinstance(value, dict) and key in base_config and isinstance(base_config[key], dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    def _set_nested_config(self, config: Dict[str, Any], path: tuple, value: Any):
        """Set a value in nested configuration using path tuple."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _validate_config(self):
        """Validate the configuration for required fields and types."""
        # Basic validation
        required_sections = ['retriever', 'generator', 'evaluator']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Required configuration section missing: {section}")

        # Validate API port
        api_port = self.config.get('api', {}).get('port', 8000)
        if not isinstance(api_port, int) or not (1024 <= api_port <= 65535):
            raise ValueError("API port must be an integer between 1024 and 65535")

        # Validate embedding dimension
        emb_dim = self.config.get('embedding', {}).get('dimension', 384)
        if not isinstance(emb_dim, int) or emb_dim <= 0:
            raise ValueError("Embedding dimension must be a positive integer")

        logger.debug("Configuration validation passed")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key (str): Configuration key (dot-separated for nested access)
            default (Any): Default value if key not found

        Returns:
            Any: Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value.

        Args:
            key (str): Configuration key (dot-separated for nested access)
            value (Any): Value to set
        """
        keys = key.split('.')
        current = self.config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        logger.debug(f"Configuration updated: {key} = {value}")

    def save_to_file(self, config_file: str):
        """
        Save current configuration to file.

        Args:
            config_file (str): Path to save configuration
        """
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {str(e)}")
            raise

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section (str): Section name

        Returns:
            Dict[str, Any]: Section configuration
        """
        return self.config.get(section, {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.config.copy()

    def get_empoorio_config(self) -> Dict[str, Any]:
        """
        Get EmpoorioLM-specific configuration.

        Returns:
            Dict[str, Any]: EmpoorioLM configuration section
        """
        return self.config.get('empoorio_lm', {})

    def get_unified_rag_config(self, rag_type: str = 'NaiveRAG') -> Dict[str, Any]:
        """
        Get unified RAG configuration that combines RAG and EmpoorioLM settings.

        Args:
            rag_type (str): Type of RAG system

        Returns:
            Dict[str, Any]: Unified configuration for RAG system
        """
        empoorio_config = self.get_empoorio_config()

        # Base RAG configuration
        rag_config = {
            'retriever_class': self.get('retriever.class', 'VectorRetriever'),
            'generator_class': self.get('generator.class', 'EmpoorioLMGenerator'),
            'evaluator_class': self.get('evaluator.class', 'BasicRAGEvaluator'),
            'retriever_config': self.get_section('retriever').get('config', {}),
            'evaluator_config': self.get_section('evaluator').get('config', {}),
            'vector_store_config': self.get_section('vector_store'),
            'embedding_config': self.get_section('embedding'),
            'text_splitter_config': self.get_section('text_splitter'),
            # Maturity 3: Data Governance
            'preprocessing_config': self.get_section('preprocessing_config'),
            'access_control_config': self.get_section('access_control_config')
        }

        # EmpoorioLM generator configuration
        generator_config = {
            'empoorio_api_config': empoorio_config.get('api_config', {}),
            'generation_config': empoorio_config.get('generation_config', {}),
            'prompt_template': empoorio_config.get('prompt_config', {}).get('template', ''),
            'rate_limiting': empoorio_config.get('rate_limiting', {}),
            'caching': empoorio_config.get('caching', {}),
            'conversation': empoorio_config.get('conversation', {}),
            'fallback': empoorio_config.get('fallback', {}),
            'metrics': empoorio_config.get('metrics', {}),
            'ab_testing': empoorio_config.get('ab_testing', {}),
            'models': empoorio_config.get('models', {}),
            'current_model': empoorio_config.get('models', {}).get('current', 'empoorio-lm-v1')
        }

        rag_config['generator_config'] = generator_config

        return rag_config

    def validate_empoorio_config(self) -> List[str]:
        """
        Validate EmpoorioLM configuration.

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        empoorio_config = self.get_empoorio_config()

        # Validate API config
        api_config = empoorio_config.get('api_config', {})
        if not api_config.get('model_path'):
            errors.append("EmpoorioLM model_path is required")

        max_seq_len = api_config.get('max_sequence_length', 512)
        if not (128 <= max_seq_len <= 4096):
            errors.append("max_sequence_length must be between 128 and 4096")

        # Validate generation config
        gen_config = empoorio_config.get('generation_config', {})
        temperature = gen_config.get('temperature', 0.7)
        if not (0.0 <= temperature <= 2.0):
            errors.append("temperature must be between 0.0 and 2.0")

        top_p = gen_config.get('top_p', 0.9)
        if not (0.0 <= top_p <= 1.0):
            errors.append("top_p must be between 0.0 and 1.0")

        max_tokens = gen_config.get('max_new_tokens', 512)
        if not (1 <= max_tokens <= 4096):
            errors.append("max_new_tokens must be between 1 and 4096")

        # Validate rate limiting
        rate_config = empoorio_config.get('rate_limiting', {})
        rpm = rate_config.get('requests_per_minute', 60)
        if rpm < 1:
            errors.append("requests_per_minute must be at least 1")

        # Validate caching
        cache_config = empoorio_config.get('caching', {})
        cache_size = cache_config.get('max_size', 1000)
        if cache_size < 0:
            errors.append("cache max_size must be non-negative")

        ttl = cache_config.get('ttl_seconds', 3600)
        if ttl < 0:
            errors.append("cache ttl_seconds must be non-negative")

        return errors

    def create_empoorio_generator_config(self) -> Dict[str, Any]:
        """
        Create configuration specifically for EmpoorioLMGenerator.

        Returns:
            Dict[str, Any]: Generator configuration
        """
        empoorio_config = self.get_empoorio_config()

        return {
            'empoorio_api_config': empoorio_config.get('api_config', {}),
            'generation_config': empoorio_config.get('generation_config', {}),
            'prompt_template': empoorio_config.get('prompt_config', {}).get('template', ''),
            'rate_limiting': empoorio_config.get('rate_limiting', {}),
            'caching': empoorio_config.get('caching', {}),
            'conversation': empoorio_config.get('conversation', {}),
            'fallback': empoorio_config.get('fallback', {}),
            'metrics': empoorio_config.get('metrics', {}),
            'ab_testing': empoorio_config.get('ab_testing', {}),
            'models': empoorio_config.get('models', {}),
            'current_model': empoorio_config.get('models', {}).get('current', 'empoorio-lm-v1')
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"RAGConfig(sections={list(self.config.keys())})"