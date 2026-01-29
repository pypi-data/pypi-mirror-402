"""Low-level API client for Neuralk inference API."""

import hashlib
import io
import platform
import sys
import time
from contextlib import contextmanager
from http import HTTPStatus
from importlib import metadata as importlib_metadata
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from sklearn.utils.validation import check_array

from neuralk.exceptions import NeuralkException
from neuralk.utils._remote_utils import create_tar, extract_tar

# Rich console for spinner output
_console = Console(stderr=True)


@contextmanager
def _inference_spinner(message: str = "Running inference"):
    """Context manager for a professional inference spinner."""
    # Skip spinner if not in interactive terminal
    if not sys.stderr.isatty():
        yield None
        return

    spinner = Spinner("dots", text=Text(f" {message}", style="dim"))
    with Live(spinner, console=_console, refresh_per_second=12, transient=True):
        yield spinner


def _print_status(success: bool, message: str, elapsed_ms: Optional[int] = None):
    """Print a status message with icon."""
    if not sys.stderr.isatty():
        return

    if success:
        icon = Text("✓", style="green bold")
        text = Text(f" {message}", style="dim")
        if elapsed_ms is not None:
            elapsed_str = f"{elapsed_ms / 1000:.2f}s" if elapsed_ms >= 1000 else f"{elapsed_ms}ms"
            text.append(f" · {elapsed_str}", style="cyan")
    else:
        icon = Text("✗", style="red bold")
        text = Text(f" {message}", style="dim red")

    _console.print(icon + text)


def _get_user_agent() -> str:
    """Get the User-Agent string for requests."""
    try:
        pkg_version = importlib_metadata.version("neuralk")
    except Exception:
        pkg_version = "0"
    return (
        f"neuralk/{pkg_version} httpx/{httpx.__version__} "
        f"python/{platform.python_version()}"
    )


class Classifications:
    """Resource for classification inference operations using tar-based protocol."""

    def __init__(self, client: "NeuralkAPI"):
        self._client = client

    def create(
        self,
        *,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        dataset_name: str = "dataset",
        model: str = "nicl-small",
        strategy: Optional[str] = None,
        memory_optimization: bool = True,
        n_groups: Optional[int] = None,
        column_names: Optional[List[str]] = None,
        selected_features: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a classification inference request.

        This method sends training data and test data to the Neuralk API
        and returns predictions and probabilities.

        Parameters
        ----------
        X_train : np.ndarray
            Training feature matrix of shape (n_samples, n_features).
        y_train : np.ndarray
            Training labels of shape (n_samples,).
        X_test : np.ndarray
            Test feature matrix of shape (n_test_samples, n_features).
        dataset_name : str, default="dataset"
            Name identifier for the dataset.
        model : str, default="nicl-small"
            Model identifier to use for inference (e.g., "nicl-small", "nicl-large").
        strategy : str, optional
            Prompting strategy: "feature", "random", "correlation", or "precomputed_groups".
        memory_optimization : bool, default=True
            Enable server-side memory optimization.
        n_groups : int, optional
            Number of groups for the prompting strategy.
        column_names : List[str], optional
            Column names for feature-based strategies.
        selected_features : List[str], optional
            Features to use for grouping.
        metadata : dict, optional
            Optional metadata to include with the request.
        user : str, optional
            Optional user identifier for request tracking.

        Returns
        -------
        dict
            Response containing:
            - predictions: np.ndarray or List[int]
            - probabilities: np.ndarray or List[List[float]]
            - request_id: str (if provided by server)
            - credits_consumed: int (cloud mode only)
            - latency_ms: int (if provided by server)
            - Additional metadata fields from server response

        Examples
        --------
        >>> from neuralk import NeuralkAPI
        >>> import numpy as np
        >>>
        >>> client = NeuralkAPI(api_key="nk_live_xxxx")
        >>> X_train = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]])
        >>> y_train = np.array([0, 0, 1])
        >>> X_test = np.array([[1.5, 2.5]])
        >>>
        >>> result = client.classifications.create(
        ...     X_train=X_train,
        ...     y_train=y_train,
        ...     X_test=X_test,
        ... )
        >>> print(result["predictions"])
        [0]
        """
        # Build prompter config if strategy is set
        prompter_config = None
        if strategy is not None:
            prompter_config = {
                "strategy": strategy,
                "n_groups": n_groups,
                "column_names": column_names,
                "selected_features": selected_features,
            }

        # Build tar archive and headers
        tar_bytes, headers = self._client._build_tar_and_headers(
            dataset_name=dataset_name,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            model_path=model,
            prompter_config=prompter_config,
            memory_optimization=memory_optimization,
            metadata=metadata,
            user=user,
        )

        # Make the request
        return self._client._make_request(tar_bytes, headers)


class NeuralkAPI:
    """
    Low-level API client for Neuralk inference services.

    This client provides direct access to the Neuralk API using a tar-based
    binary protocol for efficient data transfer. For most users, the higher-level
    `Classifier` class is recommended.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication (e.g., "nk_live_xxxx").
        Required for cloud mode. Optional for on-premise deployments.
    host : str, default="https://api.prediction.neuralk-ai.com"
        Base URL of the Neuralk API or on-premise server.
    timeout_s : int, default=900
        Request timeout in seconds.
    api_version : str, optional
        Optional API version string to send as 'Nicl-Version' header.
    default_headers : dict, optional
        Optional default headers to include with every request.

    Examples
    --------
    Cloud mode with API key:

    >>> from neuralk import NeuralkAPI
    >>> import numpy as np
    >>>
    >>> client = NeuralkAPI(api_key="nk_live_xxxx")
    >>> result = client.classifications.create(
    ...     X_train=np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]),
    ...     y_train=np.array([0, 0, 1]),
    ...     X_test=np.array([[1.5, 2.5]]),
    ... )
    >>> print(result["predictions"])
    [0]

    On-premise mode without API key:

    >>> client = NeuralkAPI(host="http://localhost:8000")
    >>> result = client.classifications.create(
    ...     X_train=X_train,
    ...     y_train=y_train,
    ...     X_test=X_test,
    ... )
    """

    DEFAULT_HOST = "https://api.prediction.neuralk-ai.com/api/v1/inference"

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        timeout_s: int = 900,
        api_version: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.api_key = api_key
        self.host = (host or self.DEFAULT_HOST).rstrip("/")
        self.timeout_s = timeout_s
        self.api_version = api_version
        self.default_headers = default_headers
        self._classifications = None

    @property
    def classifications(self) -> Classifications:
        """Access classification inference operations."""
        if self._classifications is None:
            self._classifications = Classifications(self)
        return self._classifications

    def _build_tar_and_headers(
        self,
        *,
        dataset_name: str,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        model_path: str,
        prompter_config: Optional[Dict[str, Any]],
        memory_optimization: bool,
        metadata: Optional[Dict[str, Any]],
        user: Optional[str],
    ) -> tuple:
        """Build tar archive and HTTP headers for the request."""
        X_train = check_array(X_train, dtype=np.float32, order="C")
        X_test = check_array(X_test, dtype=np.float32, order="C")
        y_train = check_array(y_train, dtype=np.int64, ensure_2d=False, order="C")

        archive = create_tar(
            {
                "method": "fit_predict",
                "model_path": model_path,
                "dataset": dataset_name,
                "prompter_config": prompter_config,
                "memory_optimization": memory_optimization,
                "metadata": metadata or {},
                "user": user or "",
            },
            {"X_train": X_train, "X_test": X_test, "y_train": y_train},
        )
        tar_bytes = archive.getvalue()

        headers = {**(self.default_headers or {})}
        headers.setdefault("Content-Type", "application/x-tar+zstd")
        headers.setdefault("User-Agent", _get_user_agent())

        # Add API key for authenticated requests
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self.api_version:
            headers.setdefault("Nicl-Version", self.api_version)

        headers["X-Content-SHA256"] = hashlib.sha256(tar_bytes).hexdigest()

        return tar_bytes, headers

    def _make_request(
        self,
        tar_bytes: bytes,
        headers: Dict[str, str],
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the server.

        Parameters
        ----------
        tar_bytes : bytes
            The tar archive content to send.
        headers : dict
            HTTP headers to include with the request.
        timeout : int, optional
            Request timeout in seconds. Uses instance timeout_s if not specified.

        Returns
        -------
        dict
            Decoded response containing predictions and metadata.

        Raises
        ------
        NeuralkException
            If the request fails or returns an error status.
        """
        timeout = timeout or self.timeout_s
        host = self.host
        attempts = 0
        retry_statuses = {500, 502, 503, 504}
        start = time.perf_counter()

        with _inference_spinner("Running inference"):
            while attempts < 3:
                attempts += 1

                try:
                    with httpx.Client(timeout=timeout) as client:
                        response = client.post(
                            f"{host}", content=tar_bytes, headers=headers
                        )

                        if response.status_code == 200:
                            elapsed_ms = int((time.perf_counter() - start) * 1000)
                            _print_status(True, "Inference complete", elapsed_ms)
                            return self._decode_response(response)
                        elif response.status_code in retry_statuses and attempts < 3:
                            time.sleep(0.5 * attempts)
                            continue
                        else:
                            _print_status(False, f"Request failed ({response.status_code})")
                            self._raise_for_status(response)

                except httpx.TimeoutException as e:
                    _print_status(False, f"Timeout after {timeout}s")
                    raise NeuralkException(
                        f"Timeout after {timeout}s",
                        HTTPStatus.REQUEST_TIMEOUT,
                        str(e),
                    ) from e
                except httpx.HTTPError as e:
                    _print_status(False, "Network error")
                    raise NeuralkException(
                        "Network error while calling Neuralk service",
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        str(e),
                    ) from e

        _print_status(False, "Max retries exceeded")
        raise NeuralkException(
            "Unexpected response from Neuralk service",
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "No successful response after retries.",
        )

    def _decode_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Decode the tar response from the server."""
        response_bytes = response.content
        payload = extract_tar(io.BytesIO(response_bytes), load_cloudpickle=False)

        result: Dict[str, Any] = {}

        # Handle both response formats (cloud uses predictions/probabilities,
        # on-premise uses predict/predict_proba)
        if "predictions" in payload:
            result["predictions"] = payload["predictions"]
        elif "predict" in payload:
            result["predictions"] = payload["predict"]

        if "probabilities" in payload:
            result["probabilities"] = payload["probabilities"]
        elif "predict_proba" in payload:
            result["probabilities"] = payload["predict_proba"]

        # Extract metadata from payload
        metadata = {
            key: value
            for key, value in payload.items()
            if key not in ["predict", "predict_proba", "predictions", "probabilities"]
        }

        # Unpack nested metadata if present
        if "metadata" in metadata and isinstance(metadata["metadata"], dict):
            nested_metadata = metadata.pop("metadata")
            if nested_metadata:
                metadata.update(nested_metadata)

        # Add metadata fields to result at top level for easy access
        for key, value in metadata.items():
            result[key] = value

        # Extract request ID from response headers
        request_id = response.headers.get("x-request-id")
        if request_id:
            result["request_id"] = request_id

        return result

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise an appropriate exception for HTTP error responses."""
        try:
            data = response.json()
            err = data.get("error") if isinstance(data, dict) else None
        except Exception:
            err = None

        message = response.text
        if err:
            rid = err.get("request_id")
            message = f"{err.get('code')}: {err.get('message')}"
            if rid:
                message += f" (request_id={rid})"

        status = response.status_code
        raise NeuralkException(message, HTTPStatus(status), response.text)
