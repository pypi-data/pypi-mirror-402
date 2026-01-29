from __future__ import annotations

from .models import (
    ExternalProviderUpsertRequest,
    ExternalProviderUpsertResponse,
    ExternalProviderStripeOnboardingRequest,
    ExternalProviderStripeOnboardingResponse,
    ExternalProviderStripeStatusResponse,
)


class ProvidersClient:
    def __init__(self, transport):
        self._transport = transport

    def upsert_provider(
        self, payload: ExternalProviderUpsertRequest
    ) -> ExternalProviderUpsertResponse:
        return self._transport._post(
            "/external/v1/providers",
            payload.model_dump(exclude_none=True, by_alias=True),
            ExternalProviderUpsertResponse,
        )

    def get_provider(self, provider_id):
        return self._transport._get(
            f"/external/v1/providers/{provider_id}",
            ExternalProviderUpsertResponse,
        )

    def list_providers(
        self,
        *,
        external_reference: str | None = None,
        name: str | None = None,
        email: str | None = None,
    ) -> list[ExternalProviderUpsertResponse]:
        params = {
            "external_reference": external_reference,
            "name": name,
            "email": email,
        }
        return self._transport._get(
            "/external/v1/providers",
            ExternalProviderUpsertResponse,
            params={k: v for k, v in params.items() if v is not None},
            many=True,
        )

    def get_provider_stripe_status(self, provider_id):
        return self._transport._get(
            f"/external/v1/providers/{provider_id}/stripe-status",
            ExternalProviderStripeStatusResponse,
        )

    def ensure_provider_stripe_onboarding(
        self, provider_id, payload: ExternalProviderStripeOnboardingRequest
    ):
        return self._transport._post(
            f"/external/v1/providers/{provider_id}/stripe-onboarding",
            payload.model_dump(exclude_none=True),
            ExternalProviderStripeOnboardingResponse,
        )
