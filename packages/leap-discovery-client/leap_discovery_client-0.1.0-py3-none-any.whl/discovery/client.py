"""Discovery Engine Python SDK Client."""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

try:
    import pandas as pd
except ImportError:
    pd = None

from discovery.types import (
    AnalysisResult,
    Column,
    CorrelationEntry,
    DataInsights,
    FeatureImportance,
    FeatureImportanceScore,
    FileInfo,
    Pattern,
    PatternGroup,
    RunStatus,
    Summary,
)


class Client:
    """Client for the Discovery Engine API."""

    # Production API URL (can be overridden via DISCOVERY_API_URL env var for testing)
    # This points to the Modal-deployed FastAPI API which uses the same database and pipeline as the dashboard
    _DEFAULT_BASE_URL = "https://jessica-52466-production--discovery-api.modal.run"

    def __init__(self, api_key: str):
        """
        Initialize the Discovery API client.

        Args:
            api_key: Your API key
        """
        self.api_key = api_key
        # Use DISCOVERY_API_URL env var if set (for testing/custom deployments),
        # otherwise use the production default
        self.base_url = os.getenv("DISCOVERY_API_URL", self._DEFAULT_BASE_URL).rstrip("/")
        self._organization_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._org_fetched = False

    async def _ensure_organization_id(self) -> str:
        """
        Ensure we have an organization ID, fetching from API if needed.

        The organization ID is required for API requests to identify which
        organization the user belongs to (multi-tenancy support).

        Returns:
            Organization ID string

        Raises:
            ValueError: If no organization is found or API request fails
        """
        if self._organization_id:
            return self._organization_id

        if not self._org_fetched:
            # Fetch user's organizations and use the first one
            try:
                orgs = await self.get_organizations()
                if orgs:
                    self._organization_id = orgs[0]["id"]
            except ValueError as e:
                # Re-raise with more context
                raise ValueError(
                    f"Failed to fetch organization: {e}. "
                    "Please ensure your API key is valid and you belong to an organization."
                ) from e
            self._org_fetched = True

        if not self._organization_id:
            raise ValueError(
                "No organization found for your account. "
                "Please contact support if this issue persists."
            )

        return self._organization_id

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=60.0,
            )
        return self._client

    async def _get_client_with_org(self) -> httpx.AsyncClient:
        """Get HTTP client with organization header set."""
        client = await self._get_client()
        org_id = await self._ensure_organization_id()
        # Update headers with org ID
        client.headers["X-Organization-ID"] = org_id
        return client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get the organizations you belong to.

        Returns:
            List of organizations with id, name, and slug

        Raises:
            ValueError: If the API request fails
        """
        client = await self._get_client()
        try:
            response = await client.get("/v1/me/organizations")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"Failed to fetch organizations: HTTP {e.response.status_code}. "
                f"{e.response.text or 'No error details available'}"
            ) from e
        except httpx.RequestError as e:
            raise ValueError(f"Failed to connect to API: {e}") from e

    async def upload_file(
        self, file: Union[str, Path, "pd.DataFrame"], filename: Optional[str] = None
    ) -> FileInfo:
        """
        Upload a file to the API.

        Args:
            file: File path, Path object, or pandas DataFrame
            filename: Optional filename (for DataFrame uploads)

        Returns:
            FileInfo with file_path, file_hash, file_size, mime_type
        """
        client = await self._get_client_with_org()

        if pd is not None and isinstance(file, pd.DataFrame):
            # Convert DataFrame to CSV in memory
            import io

            buffer = io.BytesIO()
            file.to_csv(buffer, index=False)
            buffer.seek(0)
            file_content = buffer.getvalue()
            filename = filename or "dataset.csv"
            mime_type = "text/csv"
        else:
            # Read file from disk
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            file_content = file_path.read_bytes()
            filename = filename or file_path.name
            mime_type = (
                "text/csv" if file_path.suffix == ".csv" else "application/vnd.apache.parquet"
            )

        # Upload file
        files = {"file": (filename, file_content, mime_type)}
        response = await client.post("/v1/upload", files=files)
        response.raise_for_status()

        data = response.json()
        return FileInfo(
            file_path=data["file_path"],
            file_hash=data["file_hash"],
            file_size=data["file_size"],
            mime_type=data["mime_type"],
        )

    async def create_dataset(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        total_rows: int = 0,
        dataset_size_mb: Optional[float] = None,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a dataset record.

        Args:
            title: Dataset title
            description: Dataset description
            total_rows: Number of rows in the dataset
            dataset_size_mb: Dataset size in MB
            author: Optional author attribution
            source_url: Optional source URL

        Returns:
            Dataset record with ID
        """
        client = await self._get_client_with_org()

        response = await client.post(
            "/v1/run-datasets",
            json={
                "title": title,
                "description": description,
                "total_rows": total_rows,
                "dataset_size_mb": dataset_size_mb,
                "author": author,
                "source_url": source_url,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_file_record(self, dataset_id: str, file_info: FileInfo) -> Dict[str, Any]:
        """
        Create a file record for a dataset.

        Args:
            dataset_id: Dataset ID
            file_info: FileInfo from upload_file()

        Returns:
            File record with ID
        """
        client = await self._get_client_with_org()

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/files",
            json={
                "mime_type": file_info.mime_type,
                "file_path": file_info.file_path,
                "file_hash": file_info.file_hash,
                "file_size": file_info.file_size,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_columns(
        self, dataset_id: str, columns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create column records for a dataset.

        Args:
            dataset_id: Dataset ID
            columns: List of column definitions with full metadata

        Returns:
            List of column records with IDs
        """
        client = await self._get_client_with_org()

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/columns",
            json=columns,
        )
        response.raise_for_status()
        return response.json()

    async def create_run(
        self,
        dataset_id: str,
        target_column_id: str,
        task: str = "regression",
        mode: str = "fast",
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        target_column_override: Optional[str] = None,
        auto_train_num_trials: int = 1,
        auto_train_max_epochs: int = 10,
        auto_report_use_llm_evals: bool = True,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a run and enqueue it for processing.

        Args:
            dataset_id: Dataset ID
            target_column_id: Target column ID
            task: Task type (regression, binary_classification, multiclass_classification)
            mode: Analysis mode ("fast" or "deep")
            visibility: Dataset visibility ("public" or "private")
            timeseries_groups: Optional list of timeseries column groups
            target_column_override: Optional override for target column name
            auto_train_num_trials: Number of training trials
            auto_train_max_epochs: Maximum training epochs
            auto_report_use_llm_evals: Use LLM evaluations
            author: Optional dataset author
            source_url: Optional source URL

        Returns:
            Run record with ID and job information
        """
        client = await self._get_client_with_org()

        payload = {
            "run_target_column_id": target_column_id,
            "task": task,
            "mode": mode,
            "visibility": visibility,
            "auto_train_num_trials": auto_train_num_trials,
            "auto_train_max_epochs": auto_train_max_epochs,
            "auto_report_use_llm_evals": auto_report_use_llm_evals,
        }

        if timeseries_groups:
            payload["timeseries_groups"] = timeseries_groups
        if target_column_override:
            payload["target_column_override"] = target_column_override
        if author:
            payload["author"] = author
        if source_url:
            payload["source_url"] = source_url

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/runs",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_results(self, run_id: str) -> AnalysisResult:
        """
        Get complete analysis results for a run.

        This returns all data that the Discovery dashboard displays:
        - LLM-generated summary with key insights
        - All discovered patterns with conditions, citations, and explanations
        - Column/feature information with statistics and importance scores
        - Correlation matrix
        - Global feature importance

        Args:
            run_id: The run ID

        Returns:
            AnalysisResult with complete analysis data
        """
        client = await self._get_client_with_org()

        response = await client.get(f"/v1/runs/{run_id}/results")
        response.raise_for_status()

        data = response.json()
        return self._parse_analysis_result(data)

    async def get_run_status(self, run_id: str) -> RunStatus:
        """
        Get the status of a run.

        Args:
            run_id: Run ID

        Returns:
            RunStatus with current status information
        """
        client = await self._get_client_with_org()

        response = await client.get(f"/v1/runs/{run_id}/results")
        response.raise_for_status()

        data = response.json()
        return RunStatus(
            run_id=data["run_id"],
            status=data["status"],
            job_id=data.get("job_id"),
            job_status=data.get("job_status"),
            error_message=data.get("error_message"),
        )

    async def wait_for_completion(
        self,
        run_id: str,
        poll_interval: float = 5.0,
        timeout: Optional[float] = None,
    ) -> AnalysisResult:
        """
        Wait for a run to complete and return the results.

        Args:
            run_id: Run ID
            poll_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (None = no timeout)

        Returns:
            AnalysisResult with complete analysis data

        Raises:
            TimeoutError: If the run doesn't complete within the timeout
            RuntimeError: If the run fails
        """
        start_time = time.time()

        while True:
            result = await self.get_results(run_id)

            if result.status == "completed":
                return result
            elif result.status == "failed":
                raise RuntimeError(
                    f"Run {run_id} failed: {result.error_message or 'Unknown error'}"
                )

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")

            await asyncio.sleep(poll_interval)

    async def analyze_async(
        self,
        file: Union[str, Path, "pd.DataFrame"],
        target_column: str,
        mode: str = "fast",
        title: Optional[str] = None,
        description: Optional[str] = None,
        column_descriptions: Optional[Dict[str, str]] = None,
        task: Optional[str] = None,
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        target_column_override: Optional[str] = None,
        auto_train_num_trials: int = 1,
        auto_train_max_epochs: int = 10,
        auto_report_use_llm_evals: bool = True,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
        wait: bool = False,
        wait_timeout: Optional[float] = None,
        **kwargs,
    ) -> AnalysisResult:
        """
        Analyze a dataset (async).

        This is a convenience method that handles the entire workflow:
        1. Upload file
        2. Create dataset
        3. Create file record
        4. Create columns (inferred from file if DataFrame)
        5. Create run
        6. Optionally wait for completion and return full results

        Args:
            file: File path, Path object, or pandas DataFrame
            target_column: Name of the target column
            mode: Analysis mode ("fast" or "deep", default: "fast")
            title: Optional dataset title
            description: Optional dataset description
            column_descriptions: Optional dict mapping column names to descriptions
            task: Task type (regression, binary, multiclass) - auto-detected if None
            visibility: Dataset visibility ("public" or "private", default: "public")
            timeseries_groups: Optional list of timeseries column groups
            target_column_override: Optional override for target column name
            auto_train_num_trials: Number of training trials (default: 1)
            auto_train_max_epochs: Maximum training epochs (default: 10)
            auto_report_use_llm_evals: Use LLM evaluations (default: True)
            author: Optional dataset author
            source_url: Optional source URL
            wait: If True, wait for analysis to complete and return full results
            wait_timeout: Maximum seconds to wait for completion (only if wait=True)
            **kwargs: Additional arguments (for future use)

        Returns:
            AnalysisResult with run_id and (if wait=True) complete results
        """
        # 1. Upload file
        file_info = await self.upload_file(file)

        # 2. Create dataset
        # If file is DataFrame, get row count
        if pd is not None and isinstance(file, pd.DataFrame):
            total_rows = len(file)
            # Infer columns from DataFrame with basic stats
            columns = []
            for col in file.columns:
                col_data = file[col]
                is_numeric = pd.api.types.is_numeric_dtype(col_data)
                is_categorical = col_data.dtype == "object" or (
                    is_numeric and col_data.nunique() <= 20
                )

                # Map pandas dtype to API data_type
                if pd.api.types.is_integer_dtype(col_data):
                    data_type = "int"
                elif pd.api.types.is_float_dtype(col_data):
                    data_type = "float"
                elif pd.api.types.is_bool_dtype(col_data):
                    data_type = "boolean"
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    data_type = "datetime"
                else:
                    data_type = "string"

                col_dict = {
                    "name": col,
                    "display_name": col,
                    "type": "categorical" if is_categorical else "continuous",
                    "data_type": data_type,
                    "description": column_descriptions.get(col) if column_descriptions else None,
                    "enabled": True,
                    "null_percentage": float(col_data.isna().sum() / len(col_data))
                    if len(col_data) > 0
                    else 0.0,
                }

                # Add numeric stats if applicable
                if is_numeric:
                    col_dict.update(
                        {
                            "mean": float(col_data.mean()) if not col_data.empty else None,
                            "median": float(col_data.median()) if not col_data.empty else None,
                            "std": float(col_data.std()) if not col_data.empty else None,
                            "min": float(col_data.min()) if not col_data.empty else None,
                            "max": float(col_data.max()) if not col_data.empty else None,
                            "approx_unique": int(col_data.nunique()),
                        }
                    )
                else:
                    col_dict.update(
                        {
                            "mean": None,
                            "median": None,
                            "std": None,
                            "min": None,
                            "max": None,
                            "mode": str(col_data.mode().iloc[0])
                            if not col_data.mode().empty
                            else None,
                            "approx_unique": int(col_data.nunique()),
                        }
                    )

                col_dict.update(
                    {
                        "iqr_min": None,
                        "iqr_max": None,
                        "values_count": None,
                    }
                )

                columns.append(col_dict)
        else:
            total_rows = 0
            columns = []  # Would need to infer from file or require user to provide

        dataset = await self.create_dataset(
            title=title or (Path(file).stem if isinstance(file, (str, Path)) else "Dataset"),
            description=description,
            total_rows=total_rows,
            author=author,
            source_url=source_url,
        )

        # 3. Create file record
        await self.create_file_record(dataset["id"], file_info)

        # 4. Create columns
        if not columns:
            raise ValueError(
                "Columns must be provided. Either pass a pandas DataFrame or use "
                "the step-by-step methods (upload_file, create_dataset, create_columns, etc.) "
                "to provide full column metadata."
            )

        column_records = await self.create_columns(dataset["id"], columns)

        # Find target column
        target_col = next((c for c in column_records if c["name"] == target_column), None)
        if not target_col:
            raise ValueError(f"Target column '{target_column}' not found in dataset")

        # 5. Create run
        run = await self.create_run(
            dataset["id"],
            target_col["id"],
            task=task or "regression",  # Default to regression, could auto-detect
            mode=mode,
            visibility=visibility,
            timeseries_groups=timeseries_groups,
            target_column_override=target_column_override,
            auto_train_num_trials=auto_train_num_trials,
            auto_train_max_epochs=auto_train_max_epochs,
            auto_report_use_llm_evals=auto_report_use_llm_evals,
            author=author,
            source_url=source_url,
        )

        run_id = str(run["id"])

        if wait:
            # Wait for completion and return full results
            return await self.wait_for_completion(run_id, timeout=wait_timeout)

        # Return minimal result with pending status
        return AnalysisResult(
            run_id=run_id,
            status="pending",
            job_id=run.get("job_id"),
            job_status=run.get("job_status"),
        )

    def analyze(
        self,
        file: Union[str, Path, "pd.DataFrame"],
        target_column: str,
        mode: str = "fast",
        description: Optional[str] = None,
        column_descriptions: Optional[Dict[str, str]] = None,
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        wait: bool = False,
        wait_timeout: Optional[float] = None,
        **kwargs,
    ) -> AnalysisResult:
        """
        Analyze a dataset (synchronous wrapper).

        This is a synchronous wrapper around analyze_async().

        Args:
            file: File path, Path object, or pandas DataFrame
            target_column: Name of the target column
            mode: Analysis mode ("fast" or "deep", default: "fast")
            description: Optional dataset description
            column_descriptions: Optional dict mapping column names to descriptions
            visibility: Dataset visibility ("public" or "private", default: "public")
            timeseries_groups: Optional list of timeseries column groups
            wait: If True, wait for analysis to complete and return full results
            wait_timeout: Maximum seconds to wait for completion (only if wait=True)
            **kwargs: Additional arguments passed to analyze_async()

        Returns:
            AnalysisResult with run_id and (if wait=True) complete results
        """
        return asyncio.run(
            self.analyze_async(
                file,
                target_column,
                mode,
                description=description,
                column_descriptions=column_descriptions,
                visibility=visibility,
                timeseries_groups=timeseries_groups,
                wait=wait,
                wait_timeout=wait_timeout,
                **kwargs,
            )
        )

    def _parse_analysis_result(self, data: Dict[str, Any]) -> AnalysisResult:
        """Parse API response into AnalysisResult dataclass."""
        # Parse summary
        summary = None
        if data.get("summary"):
            summary = self._parse_summary(data["summary"])

        # Parse patterns
        patterns = []
        for p in data.get("patterns", []):
            patterns.append(
                Pattern(
                    id=p["id"],
                    task=p.get("task", "regression"),
                    target_column=p.get("target_column", ""),
                    direction=p.get("direction", "max"),
                    p_value=p.get("p_value", 0),
                    conditions=p.get("conditions", []),
                    lift_value=p.get("lift_value", 0),
                    support_count=p.get("support_count", 0),
                    support_percentage=p.get("support_percentage", 0),
                    pattern_type=p.get("pattern_type", "validated"),
                    novelty_type=p.get("novelty_type", "confirmatory"),
                    target_score=p.get("target_score", 0),
                    target_class=p.get("target_class"),
                    target_mean=p.get("target_mean"),
                    target_std=p.get("target_std"),
                    description=p.get("description", ""),
                    novelty_explanation=p.get("novelty_explanation", ""),
                    citations=p.get("citations", []),
                )
            )

        # Parse columns
        columns = []
        for c in data.get("columns", []):
            columns.append(
                Column(
                    id=c["id"],
                    name=c["name"],
                    display_name=c.get("display_name", c["name"]),
                    type=c.get("type", "continuous"),
                    data_type=c.get("data_type", "float"),
                    enabled=c.get("enabled", True),
                    description=c.get("description"),
                    mean=c.get("mean"),
                    median=c.get("median"),
                    std=c.get("std"),
                    min=c.get("min"),
                    max=c.get("max"),
                    iqr_min=c.get("iqr_min"),
                    iqr_max=c.get("iqr_max"),
                    mode=c.get("mode"),
                    approx_unique=c.get("approx_unique"),
                    null_percentage=c.get("null_percentage"),
                    feature_importance_score=c.get("feature_importance_score"),
                )
            )

        # Parse correlation matrix
        correlation_matrix = []
        for entry in data.get("correlation_matrix", []):
            correlation_matrix.append(
                CorrelationEntry(
                    feature_x=entry["feature_x"],
                    feature_y=entry["feature_y"],
                    value=entry["value"],
                )
            )

        # Parse feature importance
        feature_importance = None
        if data.get("feature_importance"):
            fi = data["feature_importance"]
            scores = [
                FeatureImportanceScore(feature=s["feature"], score=s["score"])
                for s in fi.get("scores", [])
            ]
            feature_importance = FeatureImportance(
                kind=fi.get("kind", "unknown"),
                baseline=fi.get("baseline", 0),
                scores=scores,
            )

        return AnalysisResult(
            run_id=data["run_id"],
            report_id=data.get("report_id"),
            status=data.get("status", "unknown"),
            dataset_title=data.get("dataset_title"),
            dataset_description=data.get("dataset_description"),
            total_rows=data.get("total_rows"),
            target_column=data.get("target_column"),
            task=data.get("task"),
            summary=summary,
            patterns=patterns,
            columns=columns,
            correlation_matrix=correlation_matrix,
            feature_importance=feature_importance,
            job_id=data.get("job_id"),
            job_status=data.get("job_status"),
            error_message=data.get("error_message"),
        )

    def _parse_summary(self, data: Dict[str, Any]) -> Summary:
        """Parse summary data into Summary dataclass."""
        # Parse data insights
        data_insights = None
        if data.get("data_insights"):
            di = data["data_insights"]
            data_insights = DataInsights(
                important_features=di.get("important_features", []),
                important_features_explanation=di.get("important_features_explanation", ""),
                strong_correlations=di.get("strong_correlations", []),
                strong_correlations_explanation=di.get("strong_correlations_explanation", ""),
                notable_relationships=di.get("notable_relationships", []),
            )

        return Summary(
            overview=data.get("overview", ""),
            key_insights=data.get("key_insights", []),
            novel_patterns=PatternGroup(
                pattern_ids=data.get("novel_patterns", {}).get("pattern_ids", []),
                explanation=data.get("novel_patterns", {}).get("explanation", ""),
            ),
            surprising_findings=PatternGroup(
                pattern_ids=data.get("surprising_findings", {}).get("pattern_ids", []),
                explanation=data.get("surprising_findings", {}).get("explanation", ""),
            ),
            statistically_significant=PatternGroup(
                pattern_ids=data.get("statistically_significant", {}).get("pattern_ids", []),
                explanation=data.get("statistically_significant", {}).get("explanation", ""),
            ),
            data_insights=data_insights,
            selected_pattern_id=data.get("selected_pattern_id"),
        )
