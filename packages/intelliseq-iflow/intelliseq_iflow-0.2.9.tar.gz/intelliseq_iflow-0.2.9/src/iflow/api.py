"""API clients for file-service and compute-service."""

from dataclasses import dataclass, field

import httpx

from iflow.auth import get_valid_token
from iflow.config import get_settings


class APIError(Exception):
    """API error with status code."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


# File service models


@dataclass
class FileItem:
    """File or folder item."""

    name: str
    display_name: str
    size: int | None
    last_modified: str | None
    is_folder: bool
    content_type: str | None = None


@dataclass
class ListFilesResult:
    """Result of listing files."""

    bucket_name: str
    path: str
    folders: list[FileItem]
    files: list[FileItem]


# Compute service models


@dataclass
class Pipeline:
    """Pipeline definition."""

    id: str
    name: str
    slug: str
    version: str
    description: str | None
    source_type: str
    source_url: str | None
    default_profile: str
    execution_mode: str
    scope: str
    org_id: str | None
    project_id: str | None
    is_active: bool
    properties: dict = field(default_factory=dict)


@dataclass
class Run:
    """Pipeline run."""

    id: str
    name: str
    project_id: str
    pipeline_id: str
    status: str
    order_id: str | None = None
    container_image: str | None = None
    profile: str | None = None
    params: dict = field(default_factory=dict)
    job_id: str | None = None
    output_path: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_by: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class RunOutput:
    """Semantic output from a pipeline run."""

    name: str  # Semantic name (e.g., "vcf", "report")
    display_name: str  # Human-readable name (e.g., "VCF File")
    type: str  # WDL type (e.g., "File", "String")
    path: str | None  # Actual GCS path
    description: str | None = None


@dataclass
class RunOutputsResponse:
    """Response from run outputs endpoint."""

    outputs: list[RunOutput]
    message: str | None = None  # Informational message (e.g., why outputs may be empty)


# Miner service models


@dataclass
class Order:
    """Clinical order."""

    id: str
    project_id: str
    name: str
    status: str
    priority: str
    accession_number: str | None = None
    external_id: str | None = None
    description: str | None = None
    indication: str | None = None
    test_type: str | None = None
    ordering_provider: str | None = None
    ordering_facility: str | None = None
    received_date: str | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    created_by: str | None = None
    tags: list[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)


@dataclass
class Sample:
    """Sample within an order."""

    id: str
    name: str
    status: str


# Admin service models


@dataclass
class Organization:
    """Organization summary."""

    id: str
    name: str
    slug: str


@dataclass
class Project:
    """Project summary."""

    id: str
    name: str
    slug: str
    org_id: str
    org_name: str
    bucket_name: str | None = None


class FlowAPIClient:
    """Client for file-service API."""

    def __init__(self, token: str | None = None):
        self.settings = get_settings()
        self._token = token

    async def _get_token(self) -> str:
        """Get valid access token."""
        if self._token:
            return self._token

        token = await get_valid_token()
        if not token:
            raise APIError("Not authenticated. Run 'iflow login' first.", status_code=401)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        """Make authenticated API request to file-service."""
        token = await self._get_token()
        url = f"{self.settings.file_url}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )

            if response.status_code == 401:
                raise APIError("Authentication expired. Run 'iflow login' again.", status_code=401)
            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)
            elif response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text or f"HTTP {response.status_code}"
                raise APIError(f"API error: {detail}", status_code=response.status_code)

            return response.json()

    async def list_files(self, project_id: str, path: str = "") -> ListFilesResult:
        """List files in a project at a given path."""
        data = await self._request(
            "GET",
            "/api/v1/files",
            params={"project_id": project_id, "path": path},
        )

        return ListFilesResult(
            bucket_name=data["bucket_name"],
            path=data["path"],
            folders=[FileItem(**f) for f in data["folders"]],
            files=[FileItem(**f) for f in data["files"]],
        )

    async def get_download_url(self, project_id: str, path: str) -> str:
        """Get signed URL for downloading a file."""
        data = await self._request(
            "GET",
            "/api/v1/files/download-url",
            params={"project_id": project_id, "path": path},
        )
        return data["url"]

    async def get_upload_url(
        self, project_id: str, path: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Get signed URL for uploading a file."""
        data = await self._request(
            "POST",
            "/api/v1/files/upload-url",
            params={"project_id": project_id},
            json={"path": path, "content_type": content_type},
        )
        return data["url"]

    async def download_file(self, url: str, output_path: str) -> None:
        """Download file from signed URL."""
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, timeout=300.0) as response:
                if response.status_code != 200:
                    raise APIError(f"Download failed: {response.status_code}")

                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

    async def upload_file(self, url: str, file_path: str, content_type: str) -> None:
        """Upload file to signed URL."""
        with open(file_path, "rb") as f:
            content = f.read()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                content=content,
                headers={"Content-Type": content_type},
                timeout=300.0,
            )

            if response.status_code not in (200, 201):
                raise APIError(f"Upload failed: {response.status_code}")


class ComputeAPIClient:
    """Client for compute-service API."""

    def __init__(self, token: str | None = None):
        self.settings = get_settings()
        self._token = token

    async def _get_token(self) -> str:
        """Get valid access token."""
        if self._token:
            return self._token

        token = await get_valid_token()
        if not token:
            raise APIError("Not authenticated. Run 'iflow login' first.", status_code=401)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """Make authenticated API request to compute-service."""
        token = await self._get_token()
        url = f"{self.settings.compute_url}{path}"

        request_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=request_headers,
                timeout=30.0,
            )

            if response.status_code == 401:
                raise APIError(
                    "Authentication expired. Run 'iflow login' again.", status_code=401
                )
            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)
            elif response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text or f"HTTP {response.status_code}"
                raise APIError(f"API error: {detail}", status_code=response.status_code)

            # Handle 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

    # Pipeline methods

    async def list_pipelines(self) -> list[Pipeline]:
        """List all active pipelines."""
        data = await self._request("GET", "/api/v1/pipelines")
        return [self._parse_pipeline(p) for p in data]

    async def get_pipeline(self, slug: str, version: str | None = None) -> Pipeline:
        """Get pipeline by slug, optionally with specific version.

        If version is None, returns the latest version.
        """
        params = {"version": version} if version else None
        data = await self._request(
            "GET", f"/api/v1/pipelines/slug/{slug}", params=params
        )
        return self._parse_pipeline(data)

    async def list_pipeline_versions(self, slug: str) -> list[Pipeline]:
        """List all versions of a pipeline."""
        data = await self._request("GET", f"/api/v1/pipelines/slug/{slug}/versions")
        return [self._parse_pipeline(p) for p in data]

    async def create_pipeline(
        self,
        name: str,
        slug: str,
        version: str,
        source_type: str,
        source_url: str,
        execution_mode: str = "direct_wdl",
        default_profile: str = "local",
        default_container_image: str = "broadinstitute/cromwell:86",
        scope: str = "global",
        org_id: str | None = None,
        project_id: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        properties: dict | None = None,
        force: bool = False,
    ) -> Pipeline:
        """Create a new pipeline.

        If force=True, overwrites existing pipeline with same slug+version.
        """
        data = await self._request(
            "POST",
            "/api/v1/pipelines",
            json={
                "name": name,
                "slug": slug,
                "version": version,
                "source_type": source_type,
                "source_url": source_url,
                "execution_mode": execution_mode,
                "default_profile": default_profile,
                "default_container_image": default_container_image,
                "scope": scope,
                "org_id": org_id,
                "project_id": project_id,
                "description": description,
                "tags": tags or [],
                "properties": properties or {},
                "force": force,
            },
        )
        return self._parse_pipeline(data)

    def _parse_pipeline(self, data: dict) -> Pipeline:
        """Parse pipeline data from API response."""
        return Pipeline(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            version=data["version"],
            description=data.get("description"),
            source_type=data["source_type"],
            source_url=data.get("source_url"),
            default_profile=data["default_profile"],
            execution_mode=data["execution_mode"],
            scope=data.get("scope", "global"),
            org_id=data.get("org_id"),
            project_id=data.get("project_id"),
            is_active=data["is_active"],
            properties=data.get("properties", {}),
        )

    # Run methods

    async def list_runs(self, project_id: str, limit: int = 50) -> list[Run]:
        """List runs for a project."""
        data = await self._request(
            "GET",
            "/api/v1/runs",
            params={"limit": limit},
            headers={"X-Project-ID": project_id},
        )
        return [self._parse_run(r, project_id=project_id) for r in data]

    async def submit_run(
        self,
        project_id: str,
        pipeline_id: str,
        order_id: str | None = None,
        params: dict | None = None,
        tags: list[str] | None = None,
        profile: str | None = None,
        callback_url: str | None = None,
    ) -> Run:
        """Submit a new pipeline run."""
        request_body = {
            "pipeline_id": pipeline_id,
            "params": params or {},
            "tags": tags or [],
        }
        if order_id:
            request_body["order_id"] = order_id
        if profile:
            request_body["profile"] = profile
        if callback_url:
            request_body["callback_url"] = callback_url

        data = await self._request(
            "POST",
            "/api/v1/runs",
            json=request_body,
            headers={"X-Project-ID": project_id},
        )
        return self._parse_run(data)

    async def get_run(self, run_id: str) -> Run:
        """Get run details by ID."""
        data = await self._request("GET", f"/api/v1/runs/{run_id}")
        return self._parse_run(data)

    async def cancel_run(self, run_id: str) -> None:
        """Cancel a running or queued run."""
        await self._request("DELETE", f"/api/v1/runs/{run_id}")

    async def list_runs_by_order(self, order_id: str) -> list[Run]:
        """List runs associated with an order."""
        data = await self._request("GET", f"/api/v1/runs/by-order/{order_id}")
        return [self._parse_run(r) for r in data]

    async def get_run_outputs(self, run_id: str) -> RunOutputsResponse:
        """Get semantic outputs for a run.

        Parses metadata.json and maps to semantic names from meta.json.
        Only available for WDL runs that have completed.
        """
        data = await self._request("GET", f"/api/v1/runs/{run_id}/outputs")
        outputs = [
            RunOutput(
                name=o["name"],
                display_name=o["display_name"],
                type=o["type"],
                path=o.get("path"),
                description=o.get("description"),
            )
            for o in data.get("outputs", [])
        ]
        return RunOutputsResponse(
            outputs=outputs,
            message=data.get("message"),
        )

    def _parse_run(self, data: dict, project_id: str | None = None) -> Run:
        """Parse run data from API response.

        Handles both full RunDetailView and simplified RunListView responses.
        """
        return Run(
            id=data["id"],
            name=data["name"],
            project_id=data.get("project_id") or project_id or "",
            pipeline_id=data["pipeline_id"],
            status=data["status"],
            order_id=data.get("order_id"),
            container_image=data.get("container_image"),
            profile=data.get("profile"),
            params=data.get("params", {}),
            job_id=data.get("job_id"),
            output_path=data.get("output_path"),
            error_message=data.get("error_message"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            created_by=data.get("created_by"),
            tags=data.get("tags", []),
        )


class MinerAPIClient:
    """Client for miner-service API (orders, samples, subjects)."""

    def __init__(self, token: str | None = None):
        self.settings = get_settings()
        self._token = token

    async def _get_token(self) -> str:
        """Get valid access token."""
        if self._token:
            return self._token

        token = await get_valid_token()
        if not token:
            raise APIError("Not authenticated. Run 'iflow login' first.", status_code=401)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> dict | list:
        """Make authenticated API request to miner-service."""
        token = await self._get_token()
        url = f"{self.settings.miner_url}{path}"

        request_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=request_headers,
                timeout=30.0,
            )

            if response.status_code == 401:
                raise APIError(
                    "Authentication expired. Run 'iflow login' again.", status_code=401
                )
            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)
            elif response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text or f"HTTP {response.status_code}"
                raise APIError(f"API error: {detail}", status_code=response.status_code)

            # Handle 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

    # Order methods

    async def list_orders(
        self,
        project_id: str,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 100,
    ) -> list[Order]:
        """List orders for a project."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        data = await self._request(
            "GET",
            "/api/v1/orders",
            params=params,
            headers={"X-Project-ID": project_id},
        )
        return [self._parse_order(o) for o in data]

    async def create_order(
        self,
        project_id: str,
        name: str,
        accession_number: str | None = None,
        external_id: str | None = None,
        description: str | None = None,
        priority: str = "routine",
        indication: str | None = None,
        test_type: str | None = None,
        ordering_provider: str | None = None,
        ordering_facility: str | None = None,
        tags: list[str] | None = None,
        properties: dict | None = None,
    ) -> Order:
        """Create a new order."""
        request_body = {
            "name": name,
            "priority": priority,
        }
        if accession_number:
            request_body["accession_number"] = accession_number
        if external_id:
            request_body["external_id"] = external_id
        if description:
            request_body["description"] = description
        if indication:
            request_body["indication"] = indication
        if test_type:
            request_body["test_type"] = test_type
        if ordering_provider:
            request_body["ordering_provider"] = ordering_provider
        if ordering_facility:
            request_body["ordering_facility"] = ordering_facility
        if tags:
            request_body["tags"] = tags
        if properties:
            request_body["properties"] = properties

        data = await self._request(
            "POST",
            "/api/v1/orders",
            json=request_body,
            headers={"X-Project-ID": project_id},
        )
        return self._parse_order(data)

    async def get_order(self, project_id: str, order_id: str) -> Order:
        """Get order by ID."""
        data = await self._request(
            "GET",
            f"/api/v1/orders/{order_id}",
            headers={"X-Project-ID": project_id},
        )
        return self._parse_order(data)

    async def get_order_by_name(self, project_id: str, name: str) -> Order | None:
        """Get order by name.

        Returns the first order matching the name (case-insensitive search).
        Returns None if no order found.
        """
        # Use search endpoint with name filter
        data = await self._request(
            "GET",
            "/api/v1/orders",
            params={"search": name, "limit": 1},
            headers={"X-Project-ID": project_id},
        )
        if data:
            return self._parse_order(data[0])
        return None

    async def transition_order(
        self, project_id: str, order_id: str, status: str
    ) -> Order:
        """Transition order to a new status."""
        data = await self._request(
            "POST",
            f"/api/v1/orders/{order_id}/transition",
            json={"status": status},
            headers={"X-Project-ID": project_id},
        )
        return self._parse_order(data)

    async def delete_order(self, project_id: str, order_id: str) -> None:
        """Delete an order."""
        await self._request(
            "DELETE",
            f"/api/v1/orders/{order_id}",
            headers={"X-Project-ID": project_id},
        )

    async def get_order_samples(
        self, project_id: str, order_id: str
    ) -> list[Sample]:
        """Get samples for an order."""
        data = await self._request(
            "GET",
            f"/api/v1/orders/{order_id}/samples",
            headers={"X-Project-ID": project_id},
        )
        return [Sample(id=s["id"], name=s["name"], status=s["status"]) for s in data]

    async def add_sample_to_order(
        self, project_id: str, order_id: str, sample_id: str
    ) -> None:
        """Add a sample to an order."""
        await self._request(
            "POST",
            f"/api/v1/orders/{order_id}/samples/{sample_id}",
            headers={"X-Project-ID": project_id},
        )

    async def remove_sample_from_order(
        self, project_id: str, order_id: str, sample_id: str
    ) -> None:
        """Remove a sample from an order."""
        await self._request(
            "DELETE",
            f"/api/v1/orders/{order_id}/samples/{sample_id}",
            headers={"X-Project-ID": project_id},
        )

    def _parse_order(self, data: dict) -> Order:
        """Parse order data from API response."""
        return Order(
            id=data["id"],
            project_id=data["project_id"],
            name=data["name"],
            status=data["status"],
            priority=data["priority"],
            accession_number=data.get("accession_number"),
            external_id=data.get("external_id"),
            description=data.get("description"),
            indication=data.get("indication"),
            test_type=data.get("test_type"),
            ordering_provider=data.get("ordering_provider"),
            ordering_facility=data.get("ordering_facility"),
            received_date=data.get("received_date"),
            due_date=data.get("due_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            created_by=data.get("created_by"),
            tags=data.get("tags", []),
            properties=data.get("properties", {}),
        )


class AdminAPIClient:
    """Client for admin-service API (orgs, projects)."""

    def __init__(self, token: str | None = None):
        self.settings = get_settings()
        self._token = token

    async def _get_token(self) -> str:
        """Get valid access token."""
        if self._token:
            return self._token

        token = await get_valid_token()
        if not token:
            raise APIError("Not authenticated. Run 'iflow login' first.", status_code=401)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
    ) -> dict | list:
        """Make authenticated API request to admin-service."""
        token = await self._get_token()
        url = f"{self.settings.admin_url}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )

            if response.status_code == 401:
                raise APIError(
                    "Authentication expired. Run 'iflow login' again.", status_code=401
                )
            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)
            elif response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text or f"HTTP {response.status_code}"
                raise APIError(f"API error: {detail}", status_code=response.status_code)

            try:
                return response.json()
            except Exception:
                text = response.text[:200] if response.text else "empty"
                raise APIError(
                    f"Invalid response from server: {text}",
                    status_code=response.status_code,
                )

    async def list_organizations(self) -> list[Organization]:
        """List all organizations."""
        data = await self._request("GET", "/api/v1/orgs")
        return [
            Organization(id=o["id"], name=o["name"], slug=o["slug"])
            for o in data
        ]

    async def list_projects(self, org_id: str | None = None) -> list[Project]:
        """List projects, optionally filtered by organization."""
        params = {"org_id": org_id} if org_id else None
        data = await self._request("GET", "/api/v1/projects", params=params)
        return [
            Project(
                id=p["id"],
                name=p["name"],
                slug=p["slug"],
                org_id=p["org_id"],
                org_name=p["org_name"],
                bucket_name=p.get("bucket_name"),
            )
            for p in data
        ]

    async def get_project(self, project_id: str) -> Project:
        """Get project by ID."""
        data = await self._request("GET", f"/api/v1/projects/{project_id}")
        return Project(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            org_id=data["org_id"],
            org_name=data["org_name"],
            bucket_name=data.get("bucket_name"),
        )
