"""
Comandos CLI para el marketplace de AILOOS.
Gestión de wallets, listings de datos y transacciones DRACMA.
"""

import click
from typing import List, Dict, Any
import json
import time

try:
    from ailoos.marketplace import marketplace, create_user_wallet, get_user_balance, list_available_datasets, show_market_stats
    from ailoos.marketplace.data_listing import DataCategory
except ImportError:
    # Para desarrollo local
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from ailoos.marketplace import marketplace, create_user_wallet, get_user_balance, list_available_datasets, show_market_stats
    from ailoos.marketplace.data_listing import DataCategory


@click.group()
@click.pass_context
def marketplace_group(ctx):
    """Comandos para gestión del marketplace DRACMA."""
    # Asegurar que tenemos configuración
    if not ctx.obj:
        from ailoos.core.config import get_config
        ctx.obj = get_config()


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--label', default='default', help='Etiqueta para la dirección')
@click.pass_context
def create_wallet(ctx, user_id: str, label: str):
    """Crea una nueva wallet DracmaS para un usuario."""
    try:
        wallet = marketplace.create_wallet(user_id, label)
        balance = wallet.get_balance()

        click.echo(f"✅ Wallet creada exitosamente para usuario: {user_id}")
        click.echo(f"📧 Dirección: {wallet.current_address}")
        click.echo(f"💰 Balance inicial: {balance} DRACMA")

        # Mostrar información adicional
        portfolio = wallet.get_portfolio_summary()
        click.echo(f"🎯 Multiplicador de staking: {portfolio['staking_multiplier']}x")
        click.echo(f"📊 Estado: {portfolio['portfolio_health']}")

    except Exception as e:
        click.echo(f"❌ Error creando wallet: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.pass_context
def wallet_balance(ctx, user_id: str):
    """Muestra el balance de DracmaS de un usuario."""
    try:
        wallet = marketplace.get_wallet(user_id)
        if not wallet:
            click.echo(f"❌ Usuario {user_id} no tiene wallet", err=True)
            return

        portfolio = wallet.get_portfolio_summary()

        click.echo(f"💰 BALANCE DracmaS - Usuario: {user_id}")
        click.echo("=" * 50)
        click.echo(f"📧 Dirección: {portfolio['address']}")
        click.echo(f"💵 Balance disponible: {portfolio['balance_dracma']:.2f} DRACMA")
        click.echo(f"🔒 Staked: {portfolio['staked_dracma']:.2f} DRACMA")
        click.echo(f"📊 Valor total: {portfolio['total_value_dracma']:.2f} DRACMA")
        click.echo(f"🎯 Multiplicador: {portfolio['staking_multiplier']}x")
        click.echo(f"📈 Recompensa diaria estimada: {portfolio['estimated_daily_reward']:.2f} DRACMA")
        click.echo(f"📈 Recompensa mensual estimada: {portfolio['estimated_monthly_reward']:.2f} DRACMA")
        click.echo(f"📋 Transacciones recientes: {portfolio['recent_transactions']}")
        click.echo(f"🏥 Estado: {portfolio['portfolio_health']}")

    except Exception as e:
        click.echo(f"❌ Error obteniendo balance: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--amount', required=True, type=float, help='Cantidad a stakear')
@click.pass_context
def stake_tokens(ctx, user_id: str, amount: float):
    """Stake DracmaS tokens para obtener rewards."""
    try:
        tx_hash = marketplace.stake_tokens(user_id, amount)
        click.echo(f"✅ Tokens staked exitosamente")
        click.echo(f"🔗 Transaction Hash: {tx_hash}")
        click.echo(f"💰 Cantidad staked: {amount} DRACMA")

        # Mostrar nueva información de staking
        wallet = marketplace.get_wallet(user_id)
        if wallet:
            staking_info = wallet.get_staking_info()
            click.echo(f"🎯 Nuevo multiplicador: {staking_info['multiplier']}x")
            click.echo(f"📈 Recompensa diaria estimada: {staking_info['estimated_daily_reward']:.2f} DRACMA")

    except Exception as e:
        click.echo(f"❌ Error stakendo tokens: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--amount', required=True, type=float, help='Cantidad a unstakear')
@click.pass_context
def unstake_tokens(ctx, user_id: str, amount: float):
    """Unstake DracmaS tokens."""
    try:
        tx_hash = marketplace.unstake_tokens(user_id, amount)
        click.echo(f"✅ Tokens unstaked exitosamente")
        click.echo(f"🔗 Transaction Hash: {tx_hash}")
        click.echo(f"💰 Cantidad unstaked: {amount} DRACMA")

    except Exception as e:
        click.echo(f"❌ Error unstakendo tokens: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--to-address', required=True, help='Dirección destinataria')
@click.option('--amount', required=True, type=float, help='Cantidad a transferir')
@click.pass_context
def transfer_tokens(ctx, user_id: str, to_address: str, amount: float):
    """Transfiere DracmaS tokens a otra dirección."""
    try:
        tx_hash = marketplace.transfer_tokens(user_id, to_address, amount)
        click.echo(f"✅ Transferencia exitosa")
        click.echo(f"🔗 Transaction Hash: {tx_hash}")
        click.echo(f"📤 De: {user_id}")
        click.echo(f"📥 A: {to_address}")
        click.echo(f"💰 Cantidad: {amount} DRACMA")

    except Exception as e:
        click.echo(f"❌ Error en transferencia: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--limit', default=10, type=int, help='Número máximo de transacciones')
@click.pass_context
def transaction_history(ctx, user_id: str, limit: int):
    """Muestra el historial de transacciones de un usuario."""
    try:
        transactions = marketplace.get_transaction_history(user_id, limit)

        if not transactions:
            click.echo(f"📭 No hay transacciones para el usuario {user_id}")
            return

        click.echo(f"📋 HISTORIAL DE TRANSACCIONES - Usuario: {user_id}")
        click.echo("=" * 80)

        for tx in transactions:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['timestamp']))
            click.echo(f"🔗 {tx['tx_hash'][:16]}... | {tx['type']} | {tx['amount']:.2f} DracmaS | {timestamp}")
            click.echo(f"   📤 {tx['sender'][:20]}... → 📥 {tx['receiver'][:20]}... | {tx['status']}")
            click.echo("-" * 80)

    except Exception as e:
        click.echo(f"❌ Error obteniendo historial: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--title', required=True, help='Título del dataset')
@click.option('--description', required=True, help='Descripción del dataset')
@click.option('--category', required=True, type=click.Choice([cat.value for cat in DataCategory]),
              help='Categoría del dataset')
@click.option('--data-hash', required=True, help='Hash de integridad de los datos')
@click.option('--ipfs-cid', required=True, help='CID de IPFS donde están los datos')
@click.option('--price', required=True, type=float, help='Precio en DRACMA')
@click.option('--size-mb', required=True, type=float, help='Tamaño en MB')
@click.option('--samples', required=True, type=int, help='Número de muestras')
@click.option('--quality', required=True, type=float, help='Puntaje de calidad (0-1)')
@click.option('--tags', default='', help='Etiquetas separadas por coma')
@click.option('--duration-days', default=30, type=int, help='Días que dura el listing')
@click.pass_context
def create_listing(ctx, user_id: str, title: str, description: str, category: str,
                  data_hash: str, ipfs_cid: str, price: float, size_mb: float,
                  samples: int, quality: float, tags: str, duration_days: int):
    """Crea un nuevo listing de datos para venta."""
    try:
        # Parsear tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        listing_id = marketplace.create_data_listing(
            seller_id=user_id,
            title=title,
            description=description,
            category=category,
            data_hash=data_hash,
            ipfs_cid=ipfs_cid,
            price_dracma=price,
            data_size_mb=size_mb,
            sample_count=samples,
            quality_score=quality,
            tags=tag_list,
            duration_days=duration_days
        )

        click.echo(f"✅ Listing creado exitosamente")
        click.echo(f"🆔 ID: {listing_id}")
        click.echo(f"📄 Título: {title}")
        click.echo(f"💰 Precio: {price} DRACMA")
        click.echo(f"📊 Calidad: {quality}")
        click.echo(f"🏷️ Tags: {', '.join(tag_list) if tag_list else 'Ninguno'}")
        click.echo(f"⏰ Expira en: {duration_days} días")

    except Exception as e:
        click.echo(f"❌ Error creando listing: {e}", err=True)


@marketplace_group.command()
@click.option('--query', default='', help='Término de búsqueda')
@click.option('--category', type=click.Choice([cat.value for cat in DataCategory]),
              help='Filtrar por categoría')
@click.option('--min-price', default=0, type=float, help='Precio mínimo')
@click.option('--max-price', type=float, help='Precio máximo')
@click.option('--min-quality', default=0, type=float, help='Calidad mínima (0-1)')
@click.option('--tags', default='', help='Etiquetas requeridas (separadas por coma)')
@click.option('--limit', default=20, type=int, help='Número máximo de resultados')
@click.pass_context
def search_datasets(ctx, query: str, category: str, min_price: float,
                   max_price: float, min_quality: float, tags: str, limit: int):
    """Busca datasets disponibles en el marketplace."""
    try:
        # Parsear tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        datasets = marketplace.search_datasets(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price if max_price else float('inf'),
            min_quality=min_quality,
            tags=tag_list,
            limit=limit
        )

        if not datasets:
            click.echo("🔍 No se encontraron datasets que coincidan con los criterios")
            return

        click.echo(f"📊 DATASETS ENCONTRADOS ({len(datasets)})")
        click.echo("=" * 100)

        for i, dataset in enumerate(datasets, 1):
            click.echo(f"{i}. 🏷️  {dataset['title']}")
            click.echo(f"   📝 {dataset['description'][:80]}{'...' if len(dataset['description']) > 80 else ''}")
            click.echo(f"   💰 {dataset['price_dracma']} DracmaS | 📊 {dataset['quality_score']:.2f} calidad")
            click.echo(f"   📏 {dataset['data_size_mb']:.1f} MB | 🔢 {dataset['sample_count']} muestras")
            click.echo(f"   🏷️  {dataset['category']} | 🆔 {dataset['listing_id']}")
            click.echo(f"   🕒 Expira: {time.strftime('%Y-%m-%d', time.localtime(dataset['expires_at']))}")
            if dataset['tags']:
                click.echo(f"   🔖 Tags: {', '.join(dataset['tags'])}")
            click.echo("-" * 100)

    except Exception as e:
        click.echo(f"❌ Error buscando datasets: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del comprador')
@click.option('--listing-id', required=True, help='ID del listing a comprar')
@click.pass_context
def purchase_dataset(ctx, user_id: str, listing_id: str):
    """Compra un dataset del marketplace."""
    try:
        tx_hash = marketplace.purchase_data(user_id, listing_id)

        click.echo(f"✅ Compra realizada exitosamente")
        click.echo(f"🔗 Transaction Hash: {tx_hash}")
        click.echo(f"🛒 Comprador: {user_id}")
        click.echo(f"📦 Listing ID: {listing_id}")

        # Mostrar información adicional
        wallet = marketplace.get_wallet(user_id)
        if wallet:
            balance = wallet.get_balance()
            click.echo(f"💰 Balance restante: {balance:.2f} DRACMA")

    except Exception as e:
        click.echo(f"❌ Error en compra: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.pass_context
def user_portfolio(ctx, user_id: str):
    """Muestra el portfolio completo de un usuario."""
    try:
        portfolio = marketplace.get_user_portfolio(user_id)

        if "error" in portfolio:
            click.echo(f"❌ {portfolio['error']}", err=True)
            return

        click.echo(f"📊 PORTFOLIO COMPLETO - Usuario: {user_id}")
        click.echo("=" * 60)
        click.echo(f"📧 Dirección: {portfolio['address']}")
        click.echo(f"💰 Balance: {portfolio['balance_dracma']:.2f} DRACMA")
        click.echo(f"🔒 Staked: {portfolio['staked_dracma']:.2f} DRACMA")
        click.echo(f"📊 Valor total: {portfolio['total_value_dracma']:.2f} DRACMA")
        click.echo(f"🎯 Multiplicador: {portfolio['staking_multiplier']}x")
        click.echo(f"📈 Reward diario: {portfolio['estimated_daily_reward']:.2f} DRACMA")
        click.echo(f"📈 Reward mensual: {portfolio['estimated_monthly_reward']:.2f} DRACMA")
        click.echo(f"🏷️ Listings activos: {portfolio['active_listings']}")
        click.echo(f"🛒 Compras realizadas: {portfolio['total_purchases']}")
        click.echo(f"🏥 Estado: {portfolio['portfolio_health']}")

    except Exception as e:
        click.echo(f"❌ Error obteniendo portfolio: {e}", err=True)


@marketplace_group.command()
@click.option('--user-id', required=True, help='ID del usuario')
@click.option('--limit', default=5, type=int, help='Número de recomendaciones')
@click.pass_context
def get_recommendations(ctx, user_id: str, limit: int):
    """Obtiene recomendaciones de datasets."""
    try:
        recommendations = marketplace.get_recommendations(user_id, limit)

        if not recommendations:
            click.echo("🤔 No hay recomendaciones disponibles")
            return

        click.echo(f"🎯 RECOMENDACIONES PARA {user_id}")
        click.echo("=" * 60)

        for rec in recommendations:
            click.echo(f"📊 {rec['title']}")
            click.echo(f"   💰 {rec['price_dracma']} DracmaS | 📈 {rec['quality_score']:.2f} calidad")
            click.echo(f"   🏷️ {rec['category']}")
            click.echo(f"   💡 {rec['reason']}")
            click.echo("-" * 60)

    except Exception as e:
        click.echo(f"❌ Error obteniendo recomendaciones: {e}", err=True)


@marketplace_group.command()
@click.pass_context
def market_stats(ctx):
    """Muestra estadísticas del marketplace."""
    try:
        stats = marketplace.get_market_stats()

        click.echo("📊 ESTADÍSTICAS DEL MARKETPLACE DRACMA")
        click.echo("=" * 60)
        click.echo(f"🏷️  Listings totales: {stats['total_listings']}")
        click.echo(f"🟢 Listings activos: {stats['active_listings']}")
        click.echo(f"💰 Listings vendidos: {stats['sold_listings']}")
        click.echo(f"💵 Volumen total: {stats['total_volume_dracma']:.2f} DRACMA")
        click.echo(f"📊 Precio promedio: {stats['average_price_dracma']:.2f} DRACMA")
        click.echo(f"👥 Vendedores únicos: {stats['unique_sellers']}")
        click.echo(f"🛒 Compradores únicos: {stats['unique_buyers']}")
        click.echo()

        # Estadísticas por categoría
        if stats['category_stats']:
            click.echo("📈 ESTADÍSTICAS POR CATEGORÍA:")
            click.echo("-" * 40)
            for cat, cat_stats in stats['category_stats'].items():
                click.echo(f"🏷️  {cat}:")
                click.echo(f"   📊 Count: {cat_stats['count']}")
                click.echo(f"   💰 Avg Price: {cat_stats['avg_price']:.2f} DRACMA")
                click.echo(f"   📈 Total Value: {cat_stats['total_value']:.2f} DRACMA")

    except Exception as e:
        click.echo(f"❌ Error obteniendo estadísticas: {e}", err=True)


# Alias para el grupo principal
marketplace_cli = marketplace_group