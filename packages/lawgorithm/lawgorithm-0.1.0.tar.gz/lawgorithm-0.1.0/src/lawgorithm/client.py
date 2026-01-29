"""Lawgorithm API client."""

from typing import Any, Literal

import httpx

from lawgorithm.exceptions import (
    AuthenticationError,
    ComplianceError,
    LawgorithmError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from lawgorithm.models import (
    Attestation,
    ComplianceCheckResult,
    ComplianceState,
    ControlResult,
    DossierCompleteness,
    DossierExport,
    Incident,
    IncidentStats,
    Policy,
    System,
)


class LawgorithmClient:
    """Client for the Lawgorithm API.

    Usage:
        client = LawgorithmClient(
            api_url="https://api.lawgorithm.io",
            api_token="your-api-token"
        )

        # Check compliance for a system
        result = client.check_compliance(system_id="uuid")

        # Export compliance dossier
        dossier = client.export_dossier(system_id="uuid")
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000/api",
        api_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Lawgorithm client.

        Args:
            api_url: Base URL for the Lawgorithm API.
            api_token: JWT token for authentication.
            timeout: Request timeout in seconds.
        """
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 201:
            return response.json()
        elif response.status_code == 204:
            return None
        elif response.status_code == 401:
            raise AuthenticationError("Invalid or missing API token", status_code=401)
        elif response.status_code == 403:
            raise AuthenticationError("Access forbidden", status_code=403)
        elif response.status_code == 404:
            raise NotFoundError("Resource not found", status_code=404)
        elif response.status_code == 422:
            data = response.json()
            raise ValidationError(
                "Validation error",
                errors=data.get("detail", []),
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 500:
            raise ServerError(f"Server error: {response.text}", status_code=response.status_code)
        else:
            raise LawgorithmError(
                f"Unexpected error: {response.text}",
                status_code=response.status_code,
            )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        response = self._client.get(
            f"{self.api_url}{path}",
            headers=self._headers(),
            params=params,
        )
        return self._handle_response(response)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        response = self._client.post(
            f"{self.api_url}{path}",
            headers=self._headers(),
            json=json,
        )
        return self._handle_response(response)

    def _patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a PATCH request."""
        response = self._client.patch(
            f"{self.api_url}{path}",
            headers=self._headers(),
            json=json,
        )
        return self._handle_response(response)

    def _delete(self, path: str) -> Any:
        """Make a DELETE request."""
        response = self._client.delete(
            f"{self.api_url}{path}",
            headers=self._headers(),
        )
        return self._handle_response(response)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "LawgorithmClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -------------------------------------------------------------------------
    # Systems
    # -------------------------------------------------------------------------

    def list_systems(self, skip: int = 0, limit: int = 100) -> list[System]:
        """List all AI systems.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of AI systems.
        """
        data = self._get("/systems", params={"skip": skip, "limit": limit})
        return [System(**s) for s in data]

    def get_system(self, system_id: str) -> System:
        """Get an AI system by ID.

        Args:
            system_id: The system UUID.

        Returns:
            The AI system.
        """
        data = self._get(f"/systems/{system_id}")
        return System(**data)

    def create_system(
        self,
        name: str,
        description: str | None = None,
        purpose: str | None = None,
        domain: str | None = None,
    ) -> System:
        """Create a new AI system.

        Args:
            name: System name.
            description: System description.
            purpose: Intended purpose.
            domain: Application domain.

        Returns:
            The created system.
        """
        data = self._post(
            "/systems",
            json={
                "name": name,
                "description": description,
                "purpose": purpose,
                "domain": domain,
            },
        )
        return System(**data)

    def classify_system(self, system_id: str) -> System:
        """Classify a system's risk level using AI.

        Args:
            system_id: The system UUID.

        Returns:
            The updated system with risk classification.
        """
        data = self._post(f"/systems/{system_id}/classify")
        return System(**data)

    # -------------------------------------------------------------------------
    # Policies
    # -------------------------------------------------------------------------

    def list_policies(self, enabled_only: bool = True) -> list[Policy]:
        """List all policies.

        Args:
            enabled_only: Only return enabled policies.

        Returns:
            List of policies.
        """
        data = self._get("/policies", params={"enabled_only": enabled_only})
        return [Policy(**p) for p in data]

    def execute_policies(self, system_id: str) -> list[ControlResult]:
        """Execute all policies on a system.

        Args:
            system_id: The system UUID.

        Returns:
            List of control results.
        """
        data = self._post(f"/policies/execute/{system_id}")
        return [ControlResult(**c) for c in data.get("results", [])]

    def sync_policies(self) -> dict[str, Any]:
        """Sync all policies from their source URLs.

        Returns:
            Sync result with success/failure counts.
        """
        return self._post("/policies/sync/all")

    # -------------------------------------------------------------------------
    # CI/CD Compliance Check
    # -------------------------------------------------------------------------

    def check_compliance(
        self,
        repo: str | None = None,
        commit: str | None = None,
        branch: str | None = None,
        system_id: str | None = None,
        strict: bool = False,
        require_compliance_state: bool = False,
    ) -> ComplianceCheckResult:
        """Run a CI/CD compliance check.

        Args:
            repo: Repository path (e.g., "owner/repo").
            commit: Commit SHA.
            branch: Branch name.
            system_id: Specific system to check (optional).
            strict: If True, raises ComplianceError on failures.
            require_compliance_state: Require valid compliance state.

        Returns:
            Compliance check result.

        Raises:
            ComplianceError: If strict=True and compliance issues found.
        """
        payload = {
            "repo": repo,
            "commit": commit,
            "branch": branch,
            "system_id": system_id,
            "strict": strict,
            "require_compliance_state": require_compliance_state,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        data = self._post("/ci/check", json=payload)
        result = ComplianceCheckResult(**data)

        if strict and result.blocked:
            raise ComplianceError(
                f"Compliance check failed: {result.failed} issues found",
                issues=[issue.model_dump() for issue in result.issues],
            )

        return result

    # -------------------------------------------------------------------------
    # Incidents (Post-Market Surveillance)
    # -------------------------------------------------------------------------

    def list_incidents(
        self,
        system_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[Incident]:
        """List incidents with optional filters.

        Args:
            system_id: Filter by system.
            status: Filter by status.
            severity: Filter by severity.

        Returns:
            List of incidents.
        """
        params = {}
        if system_id:
            params["system_id"] = system_id
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity

        data = self._get("/incidents", params=params)
        return [Incident(**i) for i in data.get("items", data)]

    def create_incident(
        self,
        system_id: str,
        title: str,
        severity: str,
        description: str | None = None,
        category: str | None = None,
    ) -> Incident:
        """Create a new incident.

        Args:
            system_id: The affected system UUID.
            title: Incident title.
            severity: Severity level (low, medium, high, critical).
            description: Detailed description.
            category: Incident category.

        Returns:
            The created incident.
        """
        data = self._post(
            "/incidents",
            json={
                "system_id": system_id,
                "title": title,
                "severity": severity,
                "description": description,
                "category": category,
            },
        )
        return Incident(**data)

    def get_incident_stats(self, system_id: str) -> IncidentStats:
        """Get incident statistics for a system.

        Args:
            system_id: The system UUID.

        Returns:
            Incident statistics.
        """
        data = self._get(f"/incidents/systems/{system_id}/stats")
        return IncidentStats(**data)

    def notify_authority(self, incident_id: str) -> Incident:
        """Mark an incident as notified to authority.

        Args:
            incident_id: The incident UUID.

        Returns:
            The updated incident.
        """
        data = self._post(f"/incidents/{incident_id}/notify-authority")
        return Incident(**data)

    # -------------------------------------------------------------------------
    # Compliance States
    # -------------------------------------------------------------------------

    def get_compliance_history(
        self,
        system_id: str,
        limit: int = 50,
    ) -> list[ComplianceState]:
        """Get compliance state history for a system.

        Args:
            system_id: The system UUID.
            limit: Maximum number of states to return.

        Returns:
            List of compliance states (newest first).
        """
        data = self._get(
            f"/compliance-states/systems/{system_id}/history",
            params={"limit": limit},
        )
        return [ComplianceState(**s) for s in data]

    def verify_compliance_chain(self, system_id: str) -> dict[str, Any]:
        """Verify the integrity of a system's compliance state chain.

        Args:
            system_id: The system UUID.

        Returns:
            Verification result with valid/invalid status.
        """
        return self._post(f"/compliance-states/systems/{system_id}/verify")

    # -------------------------------------------------------------------------
    # Attestations
    # -------------------------------------------------------------------------

    def create_attestation(
        self,
        system_id: str,
        attestation_type: str,
        statement: str,
        private_key: str,
        attester_org: str,
        attester_role: str,
    ) -> Attestation:
        """Create an Ed25519 signed attestation.

        Args:
            system_id: The system UUID.
            attestation_type: Type (e.g., "CONFORMITY_DECLARATION").
            statement: Attestation statement.
            private_key: Ed25519 private key (base64).
            attester_org: Attester organization name.
            attester_role: Attester role (e.g., "DPO", "CTO").

        Returns:
            The created attestation.
        """
        data = self._post(
            f"/attestations/systems/{system_id}",
            json={
                "attestation_type": attestation_type,
                "statement": statement,
                "private_key": private_key,
                "attester_org": attester_org,
                "attester_role": attester_role,
            },
        )
        return Attestation(**data)

    def verify_attestation(self, attestation_id: str) -> dict[str, Any]:
        """Verify an attestation's signature.

        Args:
            attestation_id: The attestation UUID.

        Returns:
            Verification result.
        """
        return self._post(f"/attestations/{attestation_id}/verify")

    # -------------------------------------------------------------------------
    # Dossier
    # -------------------------------------------------------------------------

    def check_dossier_completeness(self, system_id: str) -> DossierCompleteness:
        """Check the completeness of a system's compliance dossier.

        Args:
            system_id: The system UUID.

        Returns:
            Completeness check result.
        """
        data = self._get(f"/dossier/systems/{system_id}/completeness")
        return DossierCompleteness(**data)

    def export_dossier(
        self,
        system_id: str,
        format: Literal["json", "markdown"] = "markdown",
    ) -> DossierExport:
        """Export a complete compliance dossier.

        Args:
            system_id: The system UUID.
            format: Export format ("json" or "markdown").

        Returns:
            The exported dossier.
        """
        data = self._post(
            f"/dossier/systems/{system_id}/export",
            json={"format": format},
        )
        return DossierExport(**data)

    # -------------------------------------------------------------------------
    # MLOps Integration
    # -------------------------------------------------------------------------

    def import_mlflow_run(
        self,
        system_id: str,
        tracking_uri: str,
        run_id: str,
    ) -> dict[str, Any]:
        """Import an MLflow run as compliance evidence.

        Args:
            system_id: The system UUID to attach evidence to.
            tracking_uri: MLflow tracking server URI.
            run_id: The MLflow run ID.

        Returns:
            Import result with evidence ID.
        """
        return self._post(
            "/mlops/import-run",
            json={
                "system_id": system_id,
                "provider": "mlflow",
                "tracking_uri": tracking_uri,
                "run_id": run_id,
            },
        )

    def import_wandb_run(
        self,
        system_id: str,
        entity: str,
        project: str,
        run_id: str,
        api_key: str,
    ) -> dict[str, Any]:
        """Import a Weights & Biases run as compliance evidence.

        Args:
            system_id: The system UUID to attach evidence to.
            entity: W&B entity (username or team).
            project: W&B project name.
            run_id: The W&B run ID.
            api_key: W&B API key.

        Returns:
            Import result with evidence ID.
        """
        return self._post(
            "/mlops/import-run",
            json={
                "system_id": system_id,
                "provider": "wandb",
                "entity": entity,
                "project": project,
                "run_id": run_id,
                "api_key": api_key,
            },
        )
