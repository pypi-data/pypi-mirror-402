#!/bin/bash
# AILOOS SDK Publication Script
# Version 2.3.0

set -e

echo "🚀 Preparando lanzamiento de AILOOS SDK v2.3.0..."

# 1. Limpieza
echo "🧹 Limpiando builds anteriores..."
rm -rf dist/ build/ *.egg-info

# 2. Construcción
echo "📦 Construyendo sdist y wheel..."
python3 setup.py sdist bdist_wheel

# 3. Verificación
echo "🔍 Verificando integridad del paquete..."
if [ -f "dist/ailoos-2.3.0.tar.gz" ]; then
    echo "✅ Archivo fuente generado: dist/ailoos-2.3.0.tar.gz"
    # Verificar si incluye el directorio security
    tar -tzf dist/ailoos-2.3.0.tar.gz | grep "ailoos/security/" > /dev/null && echo "✅ Directorio 'security' incluido." || echo "❌ ERROR: 'security' no se incluyó."
else
    echo "❌ ERROR: No se generó el archivo dist/ailoos-2.3.0.tar.gz"
    exit 1
fi

echo ""
echo "🎉 ¡Todo listo! Para subir a PyPI ejecuta:"
echo "   twine upload dist/*"
echo ""
echo "Nota: Necesitarás tener instalado 'twine' y 'wheel'."
