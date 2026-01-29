"""Pydantic v2 models for the Finanfut Billing SDK."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ExternalAddress(BaseModel):
    line1: str
    city: str
    country: str
    postal_code: str | None = None
    line2: str | None = None

    @field_validator("line1", "city", "country")
    def _required_fields(cls, value: str) -> str:  # noqa: D401
        """Validate mandatory address fields."""
        if not value:
            raise ValueError("This field is required")
        return value


class ExternalContact(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None


class ExternalClientUpsertRequest(BaseModel):
    external_reference: str
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    vat_number: str | None = None
    tax_regime: str | None = None
    metadata: dict | None = None
    address: ExternalAddress | None = None
    contact: ExternalContact | None = None

    @field_validator("name")
    def _name_required(cls, value: str) -> str:
        if not value:
            raise ValueError("name is required")
        return value


class ExternalClientUpsertResponse(BaseModel):
    client_id: UUID
    contact_id: UUID
    billing_contact_id: UUID | None = None
    external_reference: str
    status: Literal["created", "updated"]
    company_id: UUID
    metadata: dict | None = Field(default=None, alias="metadata_json")


class ExternalProviderUpsertRequest(BaseModel):
    external_reference: str
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    vat_number: str | None = None
    tax_regime: str | None = None
    requires_payouts: bool | None = None
    metadata: dict | None = None
    address: ExternalAddress | None = None
    contact: ExternalContact | None = None

    @field_validator("name")
    def _name_required(cls, value: str) -> str:
        if not value:
            raise ValueError("name is required")
        return value


class ExternalProviderUpsertResponse(BaseModel):
    provider_id: UUID
    contact_id: UUID
    billing_contact_id: UUID | None = None
    external_reference: str
    status: Literal["created", "updated"]
    company_id: UUID
    metadata_json: dict | None = None


class ExternalProviderStripeTimelineItem(BaseModel):
    state: str
    occurred_at: datetime | None = None


class ExternalProviderStripeStatusResponse(BaseModel):
    account_status: str
    capabilities: dict
    external_account_id: str | None = None
    ready_for_payout: bool
    current_state: str
    timeline: list[ExternalProviderStripeTimelineItem]


class ExternalProviderStripeOnboardingRequest(BaseModel):
    return_url: str | None = None
    refresh_url: str | None = None
    mode: str = "live"
    business_unit_id: UUID | None = None


class ExternalProviderStripeOnboardingResponse(BaseModel):
    account_id: str | None = None
    account_status: str
    current_state: str
    ready_for_payout: bool
    account_link_url: str | None = None


class ExternalServiceUpsertRequest(BaseModel):
    external_reference: str
    type: Literal["service", "product"]
    name: str
    description: str | None = None
    price: Decimal = Field(ge=0)
    vat_rate_id: UUID | None = None
    vat_rate_code: str | None = None
    metadata: dict | None = None
    business_unit_id: UUID | None = None


class ExternalServiceUpsertResponse(BaseModel):
    item_id: UUID
    type: Literal["service", "product"]
    status: Literal["created", "updated"]


class ExternalInvoiceLine(BaseModel):
    service_external_reference: str | None = None
    product_external_reference: str | None = None
    description: str | None = None
    qty: Decimal = Field(gt=0)
    price: Decimal = Field(ge=0)
    vat_rate_id: UUID | None = None
    vat_rate_code: str | None = None


class ExternalInvoiceCreateRequest(BaseModel):
    client_id: UUID | None = None
    client_external_reference: str | None = None
    lines: list[ExternalInvoiceLine]
    status: Literal["paid", "pending"] = "pending"
    issued_at: datetime | None = None
    currency: str | None = None
    metadata: dict | None = None
    business_unit_id: UUID | None = None

    @field_validator("lines")
    def _lines_required(cls, value: list[ExternalInvoiceLine]) -> list[ExternalInvoiceLine]:
        if not value:
            raise ValueError("At least one invoice line is required")
        return value


class ExternalInvoiceCreateResponse(BaseModel):
    invoice_id: UUID
    series: str | None = None
    number: int | None = None
    status: str
    total: Decimal
    business_unit_id: UUID | None = None


class ExternalInvoiceLineDetail(BaseModel):
    service_id: UUID | None = None
    product_id: UUID | None = None
    description: str
    qty: Decimal
    price: Decimal
    tax_rate_id: UUID | None = None
    tax_amount: Decimal | None = None
    total: Decimal | None = None


class ExternalInvoiceEvent(BaseModel):
    event_type: str
    payload: dict
    created_at: datetime
    created_by: UUID | None = None


class ExternalInvoiceDetailResponse(BaseModel):
    invoice_id: UUID
    series: str | None = None
    number: int | None = None
    status: str
    date_issued: date
    currency: str
    total: Decimal
    pending_amount: Decimal
    client_id: UUID
    contact_id: UUID | None = None
    payment_ids: list[UUID]
    lines: list[ExternalInvoiceLineDetail]
    events: list[ExternalInvoiceEvent] | None = None
    pdf_url: str | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")
    business_unit_id: UUID | None = None


class ExternalPaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str | None = None
    date: Optional[date] = None
    metadata: dict | None = None


class ExternalPaymentCreateResponse(BaseModel):
    payment_id: UUID | None = None
    payment_ids: list[UUID]
    status: str


class ExternalCheckoutCreateRequest(BaseModel):
    client_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str | None = None
    provider_payload: dict | None = None
    business_unit_id: UUID | None = None


class ExternalCheckoutCreateResponse(BaseModel):
    session_id: UUID
    provider_session_id: str | None = None
    status: str


class ExternalCheckoutSessionCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str | None = None
    success_url: str
    cancel_url: str
    business_unit_id: UUID | None = None
    customer_id: UUID | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    description: str | None = None
    provider_payload: dict | None = None
    charge_mode: Literal["direct", "destination", "platform"] | None = None


class CommissionRevenueCreateRequest(BaseModel):
    provider_id: UUID | None = None
    business_unit_id: UUID | None = None
    provider_payment_id: str | None = None
    provider_object_id: str | None = None
    external_reference: str | None = None
    idempotency_key: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str
    occurred_at: datetime | None = None
    metadata: dict | None = None


class CommissionRevenueResponse(BaseModel):
    id: UUID
    company_id: UUID
    business_unit_id: UUID | None = None
    provider_id: UUID | None = None
    payment_transaction_id: UUID | None = None
    provider_payment_id: str | None = None
    provider_object_id: str | None = None
    external_reference: str | None = None
    idempotency_key: str | None = None
    amount: Decimal
    currency: str
    status: str
    reconciled: bool
    reconciled_at: datetime | None = None
    occurred_at: datetime | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class CommissionRevenueSummary(BaseModel):
    pending_total: Decimal = Decimal("0")
    reconciled_total: Decimal = Decimal("0")
    pending_count: int = 0
    reconciled_count: int = 0


class CommissionRevenueListResponse(BaseModel):
    items: list[CommissionRevenueResponse]
    summary: CommissionRevenueSummary


class CommissionRevenueReverseRequest(BaseModel):
    provider_id: UUID
    provider_payment_id: str | None = None
    provider_object_id: str | None = None
    refund_metadata: dict | None = None


class ExternalCheckoutSessionResponse(BaseModel):
    session_url: str | None = None
    session_id: str | None = None
    payment_session_id: UUID


class ExternalPaymentSessionResponse(BaseModel):
    id: UUID
    status: str
    provider_session_id: str | None = None
    provider_payment_intent_id: str | None = None
    provider_object_id: str | None = None
    expires_at: datetime | None = None
    business_unit_id: UUID | None = None
    customer_id: UUID | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    created_by: UUID | None = None
    description: str | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")


class ExternalConnectOnboardRequest(BaseModel):
    provider_id: UUID | None = None
    return_url: str | None = None
    refresh_url: str | None = None
    provider_payload: dict | None = None
    business_unit_id: UUID | None = None


class ExternalConnectOnboardResponse(BaseModel):
    provider: str
    status: Literal["initiated", "unsupported"]
    url: str | None = None


class ExternalInvoiceEmailRequest(BaseModel):
    brand: str | None = None
    to: EmailStr | None = None
    subject: str | None = None
    body: str | None = None


class ExternalInvoiceEmailResponse(BaseModel):
    sent: bool
    pdf_url: str | None = None


class ExternalTaxRateResponse(BaseModel):
    id: UUID
    code: str
    name: str
    rate: Decimal
    category: str
    is_active: bool


class ExternalTaxRateListResponse(BaseModel):
    items: list[ExternalTaxRateResponse]


class ServiceError(BaseModel):
    error: str
    message: str
    request_id: str | None = None


class RequestValidationError(BaseModel):
    detail: list[dict]


class InternalServerError(BaseModel):
    message: str | None = None
    request_id: str | None = None


class SettlementFinalizeOptions(BaseModel):
    invoice_to: Literal["partner_client", "partner_provider", "none"] | None = None
    invoice_kind: Literal["customer", "supplier"] | None = None
    create_invoice: bool = True
    partner_client_id: UUID | None = None
    partner_provider_id: UUID | None = None
    supplier_tax_rate_id: UUID | None = None
    supplier_tax_reason: str | None = None
    supplier_tax_reason_detail: str | None = None
    supplier_document_id: UUID | None = None
    auto_payout: bool | None = None
    payout_mode: Literal["bank_transfer", "provider_connect"] | None = None
    provider_name: str | None = None


class SettlementLineCreate(BaseModel):
    line_type: Literal["income", "expense", "commission", "platform_fee", "adjustment"]
    description: str
    amount: Decimal
    account_id: UUID | None = None
    tax_rate_id: UUID | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")


class SettlementLine(SettlementLineCreate):
    id: UUID
    created_at: datetime


class SettlementPayout(BaseModel):
    id: UUID
    payout_amount: Decimal
    payout_method: str
    partner_payment_method_id: UUID | None = None
    partner_payment_method: PartnerPaymentMethod | None = None
    payout_date: date | None = None
    reference: str | None = None
    status: Literal["pending", "processing", "completed", "failed"] | None = None
    payout_mode: str | None = None
    provider_name: str | None = None
    destination_account_id: UUID | None = None
    provider_payload: dict | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class SettlementCompensation(BaseModel):
    id: UUID
    invoice_id: UUID
    compensation_amount: Decimal
    created_at: datetime


class SettlementPayoutCreate(BaseModel):
    payout_amount: Decimal
    payout_method: str | None = None
    partner_payment_method_id: UUID | None = None
    payout_date: date | None = None
    reference: str | None = None
    status: Literal["pending", "processing", "completed", "failed"] | None = None
    payout_mode: str | None = None
    provider_name: str | None = None
    destination_account_id: UUID | None = None
    provider_payload: dict | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")


class SettlementCreate(BaseModel):
    partner_client_id: UUID | None = None
    partner_provider_id: UUID | None = None
    external_source_id: UUID | None = None
    business_unit_id: UUID | None = None
    reference_code: str | None = None
    settlement_period_start: date | None = None
    settlement_period_end: date | None = None
    currency: str = "EUR"
    payout_mode: str = "bank_transfer"
    metadata: dict | None = Field(default=None, alias="metadata_json")
    lines: list[SettlementLineCreate]

    @field_validator("lines")
    def _require_lines(cls, value: list[SettlementLineCreate]) -> list[SettlementLineCreate]:  # noqa: D401
        """Ensure at least one settlement line is provided."""
        if not value:
            raise ValueError("At least one settlement line is required")
        return value

    @model_validator(mode="after")
    def _validate_partner(self) -> "SettlementCreate":
        if bool(self.partner_client_id) == bool(self.partner_provider_id):
            raise ValueError("Provide exactly one partner (client or provider)")
        return self


class PartnerPaymentMethodSummary(BaseModel):
    id: UUID
    method_type: str
    descriptor: str | None = None

class Settlement(BaseModel):
    id: UUID
    status: Literal["draft", "finalized", "invoiced", "settled", "payout_failed"]
    partner_client_id: UUID | None = None
    partner_provider_id: UUID | None = None
    external_source_id: UUID | None = None
    business_unit_id: UUID | None = None
    reference_code: str | None = None
    settlement_period_start: date | None = None
    settlement_period_end: date | None = None
    currency: str
    payout_mode: str
    total_positive_amount: Decimal
    total_negative_amount: Decimal
    net_payable_amount: Decimal
    total_compensated: Decimal = Decimal("0")
    invoice_id: UUID | None = None
    metadata: dict | None = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    lines: list[SettlementLine]
    payouts: list[SettlementPayout]
    compensations: list[SettlementCompensation]
    commission_invoice_id: UUID | None = None
    settlement_mode: str | None = None
    partner_payment_method_summary: PartnerPaymentMethodSummary | None = None


class PartnerPaymentMethodCreate(BaseModel):
    client_id: UUID | None = None
    provider_id: UUID | None = None
    method_type: str
    metadata: dict = Field(default_factory=dict, alias="metadata_json")
    is_default: bool | None = None


class PartnerPaymentMethod(BaseModel):
    id: UUID
    company_id: UUID
    client_id: UUID | None = None
    provider_id: UUID | None = None
    method_type: str
    metadata: dict = Field(default_factory=dict, alias="metadata_json")
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class SubscriptionPricingSnapshot(BaseModel):
    name: str | None = None
    description: str | None = None
    amount: Decimal
    currency: str = "EUR"
    interval: str | None = None
    interval_count: int = 1
    trial_period_days: int | None = None
    trial_end: datetime | None = None
    tax_behavior: str | None = None
    usage_type: str | None = None
    metadata: dict | None = None


class SubscriptionStartRequest(BaseModel):
    request_id: str
    business_unit_id: UUID | None = None
    subject_type: str
    subject_id: str
    payer_profile_id: str | None = None
    billing_client_id: UUID | None = None
    bu_plan_ref: str
    pricing_snapshot: SubscriptionPricingSnapshot
    success_url: str
    cancel_url: str
    metadata: dict | None = None


class SubscriptionStartResponse(BaseModel):
    request_id: str
    ledger_id: UUID
    status: str
    checkout_url: str | None = None
    stripe_checkout_session_id: str | None = None


class SubscriptionLedgerRead(BaseModel):
    id: UUID
    company_id: UUID
    business_unit_id: UUID | None = None
    subject_type: str
    subject_id: str
    bu_plan_ref: str
    status: str
    stripe_customer_id: str | None = None
    stripe_product_id: str | None = None
    stripe_price_id: str | None = None
    stripe_subscription_id: str | None = None
    current_period_start: date | None = None
    current_period_end: date | None = None
    cancel_at_period_end: bool
    trial_end: datetime | None = None
    last_stripe_event_id: str | None = None
    last_event_at: datetime | None = None
    latest_invoice_id: str | None = None
    latest_invoice_status: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime
