"""Base classifier with shared sklearn interface and validation logic."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.validation import check_array, check_is_fitted, check_X_y


class BaseClassifier(ClassifierMixin, BaseEstimator, ABC):
    """
    Abstract base classifier with shared sklearn interface.

    This class provides common functionality for both cloud and on-premise
    classifiers, including input validation, label encoding, and the
    standard sklearn fit/predict interface.

    Parameters
    ----------
    model : str, default="nicl-small"
        Model identifier to use for inference.
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

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        The unique class labels found during fit.
    X_train_ : ndarray of shape (n_samples, n_features)
        Training data stored during fit.
    y_train_ : ndarray of shape (n_samples,)
        Encoded training labels stored during fit.
    label_encoder_ : LabelEncoder or None
        Label encoder used for non-integer labels.
    last_response_ : dict, optional
        The last response received from the server.
    """

    def __init__(
        self,
        *,
        model: str = "nicl-small",
        strategy: Optional[str] = None,
        memory_optimization: bool = True,
        n_groups: Optional[int] = None,
        column_names: Optional[List[str]] = None,
        selected_features: Optional[List[str]] = None,
        timeout_s: int = 900,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
    ):
        self.model = model
        self.strategy = strategy
        self.memory_optimization = memory_optimization
        self.n_groups = n_groups
        self.column_names = column_names
        self.selected_features = selected_features
        self.timeout_s = timeout_s
        self.metadata = metadata
        self.user = user

    def fit(self, X, y) -> "BaseClassifier":
        """
        Fit the classifier by storing training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values. Can be numeric or string labels.

        Returns
        -------
        self : BaseClassifier
            Returns the instance itself.
        """
        X, y = check_X_y(X, y, dtype=None, ensure_2d=True)

        if not np.issubdtype(y.dtype, np.integer):
            self.label_encoder_ = LabelEncoder()
            y_encoded = self.label_encoder_.fit_transform(y)
            self.classes_ = self.label_encoder_.classes_
        else:
            y_encoded = y
            self.classes_ = np.unique(y_encoded)
            self.label_encoder_ = None

        self.X_train_ = check_array(X, dtype=np.float32, order="C")
        self.y_train_ = check_array(
            y_encoded, dtype=np.int64, ensure_2d=False, order="C"
        )

        return self

    def predict(self, X) -> np.ndarray:
        """
        Predict class labels for samples in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples to predict.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels per sample.
        """
        check_is_fitted(self, ("X_train_", "y_train_"))
        X = check_array(X, dtype=np.float32, order="C")

        result = self._remote_predict(X)
        predictions = np.asarray(result["predictions"])

        if self.label_encoder_ is not None:
            predictions = self.label_encoder_.inverse_transform(predictions)

        return predictions

    def predict_proba(self, X) -> np.ndarray:
        """
        Predict class probabilities for samples in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples to predict.

        Returns
        -------
        y_proba : ndarray of shape (n_samples, n_classes)
            Class probabilities for each sample.
        """
        check_is_fitted(self, ("X_train_", "y_train_"))
        X = check_array(X, dtype=np.float32, order="C")

        result = self._remote_predict(X)
        probabilities = result.get("probabilities")

        if probabilities is None:
            raise ValueError("Probabilities not available in response")

        return np.asarray(probabilities)

    @abstractmethod
    def _remote_predict(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Execute remote prediction.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Validated test samples.

        Returns
        -------
        dict
            Response containing at minimum:
            - predictions: List[int]
            - probabilities: List[List[float]] (optional)
        """
        pass

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get metadata from the last server response.

        Returns
        -------
        metadata : dict or None
            Metadata from the last prediction call, or None if not available.
        """
        return getattr(self, "metadata_", None)

    def get_last_response(self) -> Optional[Dict[str, Any]]:
        """
        Get the full last server response.

        Returns
        -------
        response : dict or None
            The complete response from the last prediction call.
        """
        return getattr(self, "last_response_", None)
