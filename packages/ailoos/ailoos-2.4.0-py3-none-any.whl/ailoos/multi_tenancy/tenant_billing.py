#!/usr/bin/env python3
"""
TenantBilling - Sistema de facturación por tenant para Ailoos FASE 8
==================================================================

Sistema de facturación completo con:
- Cálculo de costos por uso por tenant
- Generación de facturas automáticas
- Integración con pasarelas de pago
- Gestión de créditos y débitos
- Reportes de facturación por tenant
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BillingCycle(Enum):
    """Ciclos de facturación disponibles"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class InvoiceStatus(Enum):
    """Estados de factura"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    """Métodos de pago"""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    STRIPE = "stripe"
    PAYPAL = "paypal"

@dataclass
class BillingItem:
    """Item individual de facturación"""
    item_id: str
    tenant_id: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    category: str  # api_calls, storage, training, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Invoice:
    """Factura de tenant"""
    invoice_id: str
    tenant_id: str
    invoice_number: str
    billing_cycle: BillingCycle
    period_start: datetime
    period_end: datetime
    items: List[BillingItem] = field(default_factory=list)
    subtotal: Decimal = Decimal('0.00')
    tax_rate: Decimal = Decimal('0.21')  # 21% IVA
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[PaymentMethod] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class TenantCredits:
    """Créditos disponibles para un tenant"""
    tenant_id: str
    available_credits: Decimal = Decimal('0.00')
    used_credits: Decimal = Decimal('0.00')
    total_credits: Decimal = Decimal('0.00')
    credit_expiry: Optional[datetime] = None
    auto_recharge: bool = False
    auto_recharge_amount: Decimal = Decimal('0.00')
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PricingRule:
    """Regla de precios para un servicio"""
    rule_id: str
    service_name: str
    unit: str  # per_call, per_gb, per_hour, etc.
    base_price: Decimal
    tiers: List[Dict[str, Any]] = field(default_factory=list)  # pricing tiers
    currency: str = "EUR"
    is_active: bool = True

class TenantBilling:
    """
    Sistema de facturación completo para multi-tenancy
    """

    def __init__(self, tenant_manager):
        self.tenant_manager = tenant_manager

        # Almacenamiento de datos de facturación
        self.invoices: Dict[str, Invoice] = {}
        self.billing_items: Dict[str, BillingItem] = {}
        self.tenant_credits: Dict[str, TenantCredits] = {}
        self.pricing_rules: Dict[str, PricingRule] = {}

        # Configuración de precios por defecto
        self._initialize_pricing_rules()

        # Contadores para números de factura
        self.invoice_counter = 1000

        logger.info("💰 TenantBilling initialized")

    def _initialize_pricing_rules(self):
        """Inicializar reglas de precios por defecto"""
        default_rules = [
            PricingRule(
                rule_id="api_calls",
                service_name="API Calls",
                unit="per_1000_calls",
                base_price=Decimal('0.50'),
                tiers=[
                    {'min': 0, 'max': 100000, 'price': Decimal('0.50')},
                    {'min': 100000, 'max': 500000, 'price': Decimal('0.40')},
                    {'min': 500000, 'max': None, 'price': Decimal('0.30')}
                ]
            ),
            PricingRule(
                rule_id="storage",
                service_name="Storage",
                unit="per_gb_month",
                base_price=Decimal('0.10'),
                tiers=[
                    {'min': 0, 'max': 100, 'price': Decimal('0.10')},
                    {'min': 100, 'max': 1000, 'price': Decimal('0.08')},
                    {'min': 1000, 'max': None, 'price': Decimal('0.05')}
                ]
            ),
            PricingRule(
                rule_id="training",
                service_name="Training Hours",
                unit="per_hour",
                base_price=Decimal('2.00'),
                tiers=[
                    {'min': 0, 'max': 100, 'price': Decimal('2.00')},
                    {'min': 100, 'max': 500, 'price': Decimal('1.50')},
                    {'min': 500, 'max': None, 'price': Decimal('1.00')}
                ]
            ),
            PricingRule(
                rule_id="inference",
                service_name="Inference Requests",
                unit="per_1000_requests",
                base_price=Decimal('0.20'),
                tiers=[
                    {'min': 0, 'max': 1000000, 'price': Decimal('0.20')},
                    {'min': 1000000, 'max': None, 'price': Decimal('0.15')}
                ]
            )
        ]

        for rule in default_rules:
            self.pricing_rules[rule.rule_id] = rule

    async def record_usage(self, tenant_id: str, service: str, quantity: Decimal,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registrar uso de un servicio por tenant
        """
        try:
            # Verificar que el tenant existe
            tenant = await self.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return False

            # Calcular precio
            price = await self._calculate_price(service, quantity)
            total_amount = (quantity * price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Crear billing item
            item = BillingItem(
                item_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                description=f"{service} usage",
                quantity=quantity,
                unit_price=price,
                total_amount=total_amount,
                category=service,
                metadata=metadata or {}
            )

            self.billing_items[item.item_id] = item

            # Actualizar créditos si es necesario
            await self._apply_credits_if_available(tenant_id, total_amount)

            logger.info(f"📊 Usage recorded: {tenant_id} - {service} - {quantity} units - €{total_amount}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record usage for tenant {tenant_id}: {e}")
            return False

    async def _calculate_price(self, service: str, quantity: Decimal) -> Decimal:
        """
        Calcular precio basado en reglas de pricing
        """
        rule = self.pricing_rules.get(service)
        if not rule:
            # Precio por defecto
            return Decimal('1.00')

        # Encontrar tier aplicable
        for tier in rule.tiers:
            if tier['max'] is None or quantity <= tier['max']:
                return tier['price']

        # Fallback al precio base
        return rule.base_price

    async def generate_invoice(self, tenant_id: str, billing_cycle: BillingCycle = BillingCycle.MONTHLY,
                              period_start: Optional[datetime] = None) -> Optional[Invoice]:
        """
        Generar factura para un tenant
        """
        try:
            # Determinar período
            if not period_start:
                now = datetime.now()
                if billing_cycle == BillingCycle.MONTHLY:
                    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                elif billing_cycle == BillingCycle.QUARTERLY:
                    quarter = ((now.month - 1) // 3) + 1
                    period_start = now.replace(month=((quarter - 1) * 3) + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:  # ANNUAL
                    period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            if billing_cycle == BillingCycle.MONTHLY:
                period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif billing_cycle == BillingCycle.QUARTERLY:
                period_end = (period_start + timedelta(days=93)).replace(day=1) - timedelta(days=1)
            else:  # ANNUAL
                period_end = period_start.replace(year=period_start.year + 1) - timedelta(days=1)

            # Obtener items de facturación para el período
            period_items = [
                item for item in self.billing_items.values()
                if item.tenant_id == tenant_id and
                period_start <= item.created_at <= period_end
            ]

            if not period_items:
                logger.info(f"No billing items found for tenant {tenant_id} in period")
                return None

            # Calcular totales
            subtotal = sum(item.total_amount for item in period_items)
            tax_amount = (subtotal * Decimal('0.21')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_amount = subtotal + tax_amount

            # Generar número de factura
            invoice_number = f"INV-{tenant_id[:8].upper()}-{self.invoice_counter:06d}"
            self.invoice_counter += 1

            # Crear factura
            invoice = Invoice(
                invoice_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                invoice_number=invoice_number,
                billing_cycle=billing_cycle,
                period_start=period_start,
                period_end=period_end,
                items=period_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                due_date=period_end + timedelta(days=30)
            )

            self.invoices[invoice.invoice_id] = invoice

            logger.info(f"📄 Invoice generated: {invoice_number} for tenant {tenant_id} - €{total_amount}")
            return invoice

        except Exception as e:
            logger.error(f"❌ Failed to generate invoice for tenant {tenant_id}: {e}")
            return None

    async def process_payment(self, invoice_id: str, payment_method: PaymentMethod,
                             payment_details: Dict[str, Any]) -> bool:
        """
        Procesar pago de factura
        """
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return False

        if invoice.status != InvoiceStatus.SENT:
            return False

        try:
            # En implementación real, integrar con pasarela de pago
            # Por ahora, simular procesamiento exitoso
            success = await self._process_payment_gateway(invoice, payment_method, payment_details)

            if success:
                invoice.status = InvoiceStatus.PAID
                invoice.paid_at = datetime.now()
                invoice.payment_method = payment_method
                invoice.updated_at = datetime.now()

                # Agregar créditos si es pago exitoso
                await self.add_credits(invoice.tenant_id, invoice.total_amount, "Payment credit")

                logger.info(f"💳 Payment processed: {invoice.invoice_number} - €{invoice.total_amount}")
                return True
            else:
                logger.error(f"❌ Payment failed: {invoice.invoice_number}")
                return False

        except Exception as e:
            logger.error(f"❌ Payment processing error for invoice {invoice_id}: {e}")
            return False

    async def _process_payment_gateway(self, invoice: Invoice, payment_method: PaymentMethod,
                                     payment_details: Dict[str, Any]) -> bool:
        """
        Integración con pasarela de pago (simulada)
        """
        # Simular procesamiento de pago
        await asyncio.sleep(0.1)  # Simular delay de red

        # 95% de éxito
        return asyncio.get_event_loop().time() % 100 > 5

    async def add_credits(self, tenant_id: str, amount: Decimal, description: str = "") -> bool:
        """
        Agregar créditos a un tenant
        """
        if tenant_id not in self.tenant_credits:
            self.tenant_credits[tenant_id] = TenantCredits(tenant_id=tenant_id)

        credits = self.tenant_credits[tenant_id]
        credits.available_credits += amount
        credits.total_credits += amount
        credits.updated_at = datetime.now()

        logger.info(f"💰 Credits added: {tenant_id} +€{amount} ({description})")
        return True

    async def _apply_credits_if_available(self, tenant_id: str, amount: Decimal) -> bool:
        """
        Aplicar créditos disponibles al cargo
        """
        credits = self.tenant_credits.get(tenant_id)
        if not credits or credits.available_credits <= 0:
            return False

        # Aplicar créditos hasta cubrir el cargo
        credit_to_apply = min(credits.available_credits, amount)
        credits.available_credits -= credit_to_apply
        credits.used_credits += credit_to_apply
        credits.updated_at = datetime.now()

        logger.info(f"💸 Credits applied: {tenant_id} -€{credit_to_apply}")
        return True

    async def get_tenant_balance(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtener balance de facturación de un tenant
        """
        credits = self.tenant_credits.get(tenant_id, TenantCredits(tenant_id=tenant_id))

        # Calcular deuda pendiente
        pending_invoices = [
            inv for inv in self.invoices.values()
            if inv.tenant_id == tenant_id and inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]
        ]
        pending_amount = sum(inv.total_amount for inv in pending_invoices)

        return {
            'tenant_id': tenant_id,
            'available_credits': credits.available_credits,
            'used_credits': credits.used_credits,
            'total_credits': credits.total_credits,
            'pending_amount': pending_amount,
            'net_balance': credits.available_credits - pending_amount
        }

    async def get_billing_history(self, tenant_id: str, limit: int = 50) -> List[Invoice]:
        """
        Obtener historial de facturación de un tenant
        """
        tenant_invoices = [
            inv for inv in self.invoices.values()
            if inv.tenant_id == tenant_id
        ]

        # Ordenar por fecha descendente
        tenant_invoices.sort(key=lambda inv: inv.created_at, reverse=True)

        return tenant_invoices[:limit]

    async def generate_billing_report(self, tenant_id: str, start_date: datetime,
                                     end_date: datetime) -> Dict[str, Any]:
        """
        Generar reporte de facturación detallado
        """
        # Filtrar items por período
        period_items = [
            item for item in self.billing_items.values()
            if item.tenant_id == tenant_id and
            start_date <= item.created_at <= end_date
        ]

        # Agrupar por categoría
        category_totals = {}
        for item in period_items:
            cat = item.category
            if cat not in category_totals:
                category_totals[cat] = {'quantity': Decimal('0'), 'amount': Decimal('0')}
            category_totals[cat]['quantity'] += item.quantity
            category_totals[cat]['amount'] += item.total_amount

        # Calcular totales
        total_quantity = sum(item.quantity for item in period_items)
        total_amount = sum(item.total_amount for item in period_items)

        return {
            'tenant_id': tenant_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_items': len(period_items),
            'total_quantity': total_quantity,
            'total_amount': total_amount,
            'category_breakdown': category_totals,
            'items': [item.__dict__ for item in period_items[:100]]  # Limitar items detallados
        }

    async def setup_auto_billing(self, tenant_id: str, payment_method: PaymentMethod,
                                payment_details: Dict[str, Any]) -> bool:
        """
        Configurar facturación automática
        """
        # En implementación real, almacenar método de pago tokenizado
        # Por ahora, solo marcar como configurado
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if tenant:
            tenant.config['auto_billing'] = {
                'enabled': True,
                'payment_method': payment_method.value,
                'setup_at': datetime.now().isoformat()
            }
            logger.info(f"🔄 Auto-billing setup for tenant {tenant_id}")
            return True

        return False

    async def check_overdue_invoices(self) -> List[str]:
        """
        Verificar facturas vencidas y marcar como overdue
        """
        now = datetime.now()
        overdue_invoice_ids = []

        for invoice in self.invoices.values():
            if (invoice.status == InvoiceStatus.SENT and
                invoice.due_date and now > invoice.due_date):
                invoice.status = InvoiceStatus.OVERDUE
                invoice.updated_at = now
                overdue_invoice_ids.append(invoice.invoice_id)

                logger.warning(f"⚠️ Invoice overdue: {invoice.invoice_number}")

        return overdue_invoice_ids