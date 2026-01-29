"""Sklearn-compatible classifier using the Neuralk API."""

import os
import warnings
from typing import Any, Dict, List, Optional

import numpy as np

from ._api import NeuralkAPI
from ._base_classifier import BaseClassifier

NEURALK_API_KEY_ENV = "NEURALK_API_KEY"


class NICLClassifier(BaseClassifier):
    """
    Sklearn-compatible classifier using the Neuralk API.

    This classifier connects to either the Neuralk cloud API or an on-premise
    NICL server and provides a scikit-learn compatible interface for classification
    tasks. Both modes use tar-based binary protocol for efficient data transfer.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication (e.g., "nk_live_xxxx").
        Required for cloud mode. If not provided, reads from the ``NEURALK_API_KEY``
        environment variable. Optional for on-premise mode.
    host : str, optional
        Base URL of the server. If not provided, uses the Neuralk cloud endpoint.
        When provided, enables on-premise mode which doesn't require an API key.
    dataset_name : str, default="dataset"
        Name identifier for the dataset used in API requests.
    model : str, default="nicl-small"
        Model identifier to use for inference (e.g., "nicl-small", "nicl-large").
    strategy : str, optional
        Prompting strategy for group-wise processing:
        - "feature": Groups based on specified features
        - "random": Random assignment to groups
        - "correlation": Groups based on target-correlated features
        - "precomputed_groups": Uses pre-existing group IDs
    memory_optimization : bool, default=True
        Enable server-side memory optimization.
    n_groups : int, optional
        Number of groups for the prompting strategy.
    column_names : List[str], optional
        Column names corresponding to features in X.
    selected_features : List[str], optional
        Features to use for grouping strategies.
    timeout_s : int, default=900
        Request timeout in seconds.
    metadata : dict, optional
        Optional metadata to include with requests.
    user : str, optional
        Optional user identifier for request tracking.
    api_version : str, optional
        Optional API version string to send as 'Nicl-Version' header.
    default_headers : dict, optional
        Optional default headers to include with every request.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        The unique class labels found during fit.
    X_train_ : ndarray of shape (n_samples, n_features)
        Training data stored during fit.
    y_train_ : ndarray of shape (n_samples,)
        Encoded training labels stored during fit.
    last_response_ : dict
        The last response from the API, containing:
        - request_id: str
        - model: str
        - predictions: List[int]
        - probabilities: List[List[float]]
        - credits_consumed: int (cloud mode only)
        - latency_ms: int

    Examples
    --------
    Cloud mode (default):

    >>> from neuralk import NICLClassifier
    >>> import numpy as np
    >>>
    >>> # API key from environment variable NEURALK_API_KEY
    >>> clf = NICLClassifier()
    >>>
    >>> # Or explicit API key
    >>> clf = NICLClassifier(api_key="nk_live_xxxx")
    >>>
    >>> X_train = np.random.randn(100, 10).astype(np.float32)
    >>> y_train = np.random.randint(0, 2, 100)
    >>>
    >>> clf.fit(X_train, y_train)
    >>>
    >>> X_test = np.random.randn(10, 10).astype(np.float32)
    >>> predictions = clf.predict(X_test)
    >>> probabilities = clf.predict_proba(X_test)
    >>>
    >>> # Check credits consumed (cloud mode)
    >>> print(clf.credits_consumed)

    On-premise mode:

    >>> clf = NICLClassifier(host="http://localhost:8000")
    >>>
    >>> clf.fit(X_train, y_train)
    >>> predictions = clf.predict(X_test)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        host: Optional[str] = None,
        dataset_name: str = "dataset",
        model: str = "nicl-small",
        strategy: Optional[str] = None,
        memory_optimization: bool = True,
        n_groups: Optional[int] = None,
        column_names: Optional[List[str]] = None,
        selected_features: Optional[List[str]] = None,
        timeout_s: int = 900,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        api_version: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            model=model,
            strategy=strategy,
            memory_optimization=memory_optimization,
            n_groups=n_groups,
            column_names=column_names,
            selected_features=selected_features,
            timeout_s=timeout_s,
            metadata=metadata,
            user=user,
        )

        # Determine mode based on host parameter
        self._is_cloud = host is None
        self.host = host

        # API key handling: required for cloud, optional for on-premise
        if self._is_cloud:
            self.api_key = api_key or os.environ.get(NEURALK_API_KEY_ENV)
            if not self.api_key:
                raise ValueError(
                    f"API key is required for cloud mode. Pass api_key parameter or "
                    f"set {NEURALK_API_KEY_ENV} environment variable."
                )
        else:
            self.api_key = api_key  # Optional for on-premise

        self.dataset_name = dataset_name
        self.api_version = api_version
        self.default_headers = default_headers

    @property
    def _client(self) -> NeuralkAPI:
        """Lazily initialize the API client."""
        if not hasattr(self, "_client_"):
            self._client_ = NeuralkAPI(
                api_key=self.api_key,
                host=self.host,
                timeout_s=self.timeout_s,
                api_version=self.api_version,
                default_headers=self.default_headers,
            )
        return self._client_

    def _remote_predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Execute remote prediction via the Neuralk API."""
        response = self._client.classifications.create(
            X_train=self.X_train_,
            y_train=self.y_train_,
            X_test=X,
            dataset_name=self.dataset_name,
            model=self.model,
            strategy=self.strategy,
            memory_optimization=self.memory_optimization,
            n_groups=self.n_groups,
            column_names=self.column_names,
            selected_features=self.selected_features,
            metadata=self.metadata,
            user=self.user,
        )

        self.last_response_ = response
        self.metadata_ = {
            k: v
            for k, v in response.items()
            if k not in ("predictions", "probabilities")
        }

        return response

    # Convenience properties for response data

    @property
    def credits_consumed(self) -> Optional[int]:
        """Get credits consumed in the last prediction, if available."""
        if hasattr(self, "last_response_"):
            return self.last_response_.get("credits_consumed")
        return None

    @property
    def request_id(self) -> Optional[str]:
        """Get request ID from the last prediction, if available."""
        if hasattr(self, "last_response_"):
            return self.last_response_.get("request_id")
        return None

    @property
    def latency_ms(self) -> Optional[int]:
        """Get latency in milliseconds from the last prediction, if available."""
        if hasattr(self, "last_response_"):
            return self.last_response_.get("latency_ms")
        return None

    # Utility methods

    def print_metadata(self) -> None:
        """Print the metadata from the last server response."""
        metadata = self.get_metadata()
        if metadata is None:
            print("No metadata available. Call predict() or predict_proba() first.")
            return

        if not metadata:
            print("No metadata returned by server.")
            return

        print("Server Metadata:")
        print("-" * 40)
        for key, value in metadata.items():
            formatted = self._format_metadata_value(value)
            print(f"{key}: {formatted}")
        print("-" * 40)

    def _format_metadata_value(self, value: Any) -> str:
        """Format a metadata value for display."""
        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return str(value.item())
            elif value.size <= 10:
                return str(value.tolist())
            else:
                return (
                    f"array of shape {value.shape}, dtype {value.dtype}\n"
                    f"  min: {value.min():.4f}, max: {value.max():.4f}, "
                    f"mean: {value.mean():.4f}"
                )
        return str(value)


class Classifier(NICLClassifier):
    """
    Deprecated: Use :class:`NICLClassifier` instead.

    This class is provided for backward compatibility only.
    It will be removed in a future version.

    Examples
    --------
    Instead of:

    >>> clf = Classifier(api_key="nk_live_xxxx")

    Use:

    >>> clf = NICLClassifier(api_key="nk_live_xxxx")
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Classifier is deprecated and will be removed in a future version. "
            "Use NICLClassifier instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class OnPremiseClassifier(NICLClassifier):
    """
    Deprecated: Use :class:`NICLClassifier` with ``host`` parameter instead.

    This class is provided for backward compatibility only.
    It will be removed in a future version.

    Examples
    --------
    Instead of:

    >>> clf = OnPremiseClassifier(host="http://localhost:8000")

    Use:

    >>> clf = NICLClassifier(host="http://localhost:8000")
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "OnPremiseClassifier is deprecated and will be removed in a future version. "
            "Use NICLClassifier(host='...') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
