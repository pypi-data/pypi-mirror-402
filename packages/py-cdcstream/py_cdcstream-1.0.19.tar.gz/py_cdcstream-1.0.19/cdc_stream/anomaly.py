"""
Anomaly Detection Engine for CDCStream

Supports 5 algorithms:
1. Z-Score: Statistical deviation from mean
2. Isolation Forest: Multi-dimensional tree-based isolation
3. Mahalanobis Distance: Correlation-aware distance metric
4. ECOD: Empirical Cumulative Distribution (parameter-free)
5. HBOS: Histogram-Based Outlier Score (fastest)
"""
from __future__ import annotations

import math
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    is_anomaly: bool
    score: float
    threshold: float
    anomaly_fields: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class BaseAnomalyDetector:
    """Base class for anomaly detectors."""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Update rolling statistics with new value."""
        raise NotImplementedError
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Evaluate if the given values are anomalous."""
        raise NotImplementedError


class ZScoreDetector(BaseAnomalyDetector):
    """
    Z-Score based anomaly detection.
    
    Z = (x - μ) / σ
    
    If |Z| > threshold (default 3.0), it's an anomaly.
    Fast: O(1) for evaluation, O(1) for update.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__(parameters)
        self.threshold = self.parameters.get("threshold", 3.0)
        self.window_size = self.parameters.get("window_size", 1000)
        self.min_samples = self.parameters.get("min_samples", 30)
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Update rolling mean and std using Welford's algorithm."""
        if field_name not in stats:
            stats[field_name] = {
                "count": 0,
                "mean": 0.0,
                "M2": 0.0,  # Sum of squares of differences from mean
                "min": value,
                "max": value,
            }
        
        s = stats[field_name]
        s["count"] += 1
        n = s["count"]
        
        # Welford's online algorithm for mean and variance
        delta = value - s["mean"]
        s["mean"] += delta / n
        delta2 = value - s["mean"]
        s["M2"] += delta * delta2
        
        # Update min/max
        s["min"] = min(s["min"], value)
        s["max"] = max(s["max"], value)
        
        # Calculate std
        if n >= 2:
            s["std"] = math.sqrt(s["M2"] / (n - 1))
        else:
            s["std"] = 0.0
        
        return stats
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Check if any value is more than threshold std deviations from mean."""
        anomaly_fields = []
        max_score = 0.0
        details = {}
        
        field_stats = model_state.get("field_stats", {})
        
        for field_name, value in values.items():
            if field_name not in field_stats:
                continue
            
            stats = field_stats[field_name]
            count = stats.get("count", 0)
            mean = stats.get("mean", 0)
            std = stats.get("std", 0)
            
            # Need enough samples for meaningful statistics
            if count < self.min_samples:
                continue
            
            # Avoid division by zero
            if std == 0:
                z_score = 0 if value == mean else float('inf')
            else:
                z_score = abs(value - mean) / std
            
            details[field_name] = {
                "value": value,
                "mean": round(mean, 4),
                "std": round(std, 4),
                "z_score": round(z_score, 4),
                "threshold": self.threshold,
            }
            
            if z_score > max_score:
                max_score = z_score
            
            if z_score > self.threshold:
                anomaly_fields.append(field_name)
        
        return AnomalyResult(
            is_anomaly=len(anomaly_fields) > 0,
            score=round(max_score, 4),
            threshold=self.threshold,
            anomaly_fields=anomaly_fields,
            details=details,
        )


class HBOSDetector(BaseAnomalyDetector):
    """
    Histogram-Based Outlier Score.
    
    Very fast: O(1) evaluation after histogram is built.
    Good for high-volume streaming data (logs, etc.)
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__(parameters)
        self.n_bins = self.parameters.get("n_bins", 10)
        self.alpha = self.parameters.get("alpha", 0.1)  # Contamination rate
        self.min_samples = self.parameters.get("min_samples", 100)
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Update histogram for the field."""
        if field_name not in stats:
            stats[field_name] = {
                "values": [],  # Store values until we have enough for histogram
                "histogram": None,
                "bin_edges": None,
                "count": 0,
            }
        
        s = stats[field_name]
        s["count"] += 1
        
        # Keep collecting values until we have enough
        if len(s["values"]) < self.min_samples:
            s["values"].append(value)
            
            # Build histogram once we have enough samples
            if len(s["values"]) >= self.min_samples:
                self._build_histogram(s)
        else:
            # Update histogram incrementally
            if s["histogram"] is not None:
                self._update_histogram(s, value)
        
        return stats
    
    def _build_histogram(self, stats: Dict):
        """Build initial histogram from collected values."""
        values = stats["values"]
        min_val = min(values)
        max_val = max(values)
        
        # Handle edge case where all values are the same
        if min_val == max_val:
            max_val = min_val + 1
        
        bin_width = (max_val - min_val) / self.n_bins
        bin_edges = [min_val + i * bin_width for i in range(self.n_bins + 1)]
        histogram = [0] * self.n_bins
        
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), self.n_bins - 1)
            histogram[bin_idx] += 1
        
        stats["histogram"] = histogram
        stats["bin_edges"] = bin_edges
        stats["min"] = min_val
        stats["max"] = max_val
    
    def _update_histogram(self, stats: Dict, value: float):
        """Update histogram with new value."""
        min_val = stats["min"]
        max_val = stats["max"]
        
        # Expand range if needed
        if value < min_val or value > max_val:
            stats["min"] = min(min_val, value)
            stats["max"] = max(max_val, value)
            # Rebuild histogram with new range
            stats["values"].append(value)
            if len(stats["values"]) > self.min_samples * 2:
                stats["values"] = stats["values"][-self.min_samples:]
            self._build_histogram(stats)
        else:
            bin_width = (max_val - min_val) / self.n_bins
            bin_idx = min(int((value - min_val) / bin_width), self.n_bins - 1)
            stats["histogram"][bin_idx] += 1
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Calculate HBOS score for given values."""
        anomaly_fields = []
        total_score = 0.0
        details = {}
        
        field_stats = model_state.get("field_stats", {})
        
        for field_name, value in values.items():
            if field_name not in field_stats:
                continue
            
            stats = field_stats[field_name]
            histogram = stats.get("histogram")
            
            if histogram is None or stats.get("count", 0) < self.min_samples:
                continue
            
            min_val = stats["min"]
            max_val = stats["max"]
            
            # Handle out of range
            if value < min_val or value > max_val:
                score = 10.0  # High anomaly score for out-of-range
            else:
                bin_width = (max_val - min_val) / self.n_bins
                bin_idx = min(int((value - min_val) / bin_width), self.n_bins - 1)
                bin_count = histogram[bin_idx]
                total_count = sum(histogram)
                
                # HBOS score: log(1 / density)
                density = (bin_count / total_count) if total_count > 0 else 0
                score = -math.log(max(density, 1e-10))
            
            details[field_name] = {
                "value": value,
                "score": round(score, 4),
            }
            total_score += score
        
        # Threshold based on contamination rate
        threshold = -math.log(self.alpha)
        avg_score = total_score / max(len(values), 1)
        
        if avg_score > threshold:
            anomaly_fields = list(values.keys())
        
        return AnomalyResult(
            is_anomaly=len(anomaly_fields) > 0,
            score=round(avg_score, 4),
            threshold=round(threshold, 4),
            anomaly_fields=anomaly_fields,
            details=details,
        )


class ECODDetector(BaseAnomalyDetector):
    """
    Empirical Cumulative Distribution Function Outlier Detection.
    
    Parameter-free! Automatically learns normal distribution.
    Great for "Auto-Pilot" mode where users just say "watch this table".
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__(parameters)
        self.contamination = self.parameters.get("contamination", 0.1)
        self.max_samples = self.parameters.get("max_samples", 1000)
        self.min_samples = self.parameters.get("min_samples", 50)
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Keep a sample of recent values for CDF estimation."""
        if field_name not in stats:
            stats[field_name] = {
                "values": [],
                "count": 0,
            }
        
        s = stats[field_name]
        s["count"] += 1
        s["values"].append(value)
        
        # Keep only recent samples
        if len(s["values"]) > self.max_samples:
            s["values"] = s["values"][-self.max_samples:]
        
        return stats
    
    def _ecdf(self, sample: List[float], value: float) -> float:
        """Calculate empirical CDF at given value."""
        n = len(sample)
        if n == 0:
            return 0.5
        count_less = sum(1 for x in sample if x < value)
        count_equal = sum(1 for x in sample if x == value)
        return (count_less + 0.5 * count_equal) / n
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Calculate ECOD score using both tails of the distribution."""
        anomaly_fields = []
        max_score = 0.0
        details = {}
        
        field_stats = model_state.get("field_stats", {})
        
        for field_name, value in values.items():
            if field_name not in field_stats:
                continue
            
            stats = field_stats[field_name]
            sample = stats.get("values", [])
            
            if len(sample) < self.min_samples:
                continue
            
            # Calculate ECDF from both tails
            cdf_left = self._ecdf(sample, value)
            cdf_right = 1 - cdf_left
            
            # ECOD score: -log of probability in the smaller tail
            tail_prob = min(cdf_left, cdf_right)
            score = -math.log(max(tail_prob, 1e-10))
            
            details[field_name] = {
                "value": value,
                "cdf_left": round(cdf_left, 4),
                "cdf_right": round(cdf_right, 4),
                "score": round(score, 4),
            }
            
            if score > max_score:
                max_score = score
        
        # Threshold based on contamination
        threshold = -math.log(self.contamination / 2)  # Two-tailed
        
        for field_name, detail in details.items():
            if detail["score"] > threshold:
                anomaly_fields.append(field_name)
        
        return AnomalyResult(
            is_anomaly=len(anomaly_fields) > 0,
            score=round(max_score, 4),
            threshold=round(threshold, 4),
            anomaly_fields=anomaly_fields,
            details=details,
        )


class IsolationForestDetector(BaseAnomalyDetector):
    """
    Simplified Isolation Forest for streaming data.
    
    Uses approximate method suitable for online learning.
    Multi-dimensional: catches anomalies in feature combinations.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__(parameters)
        self.contamination = self.parameters.get("contamination", 0.1)
        self.n_estimators = self.parameters.get("n_estimators", 50)
        self.max_samples = self.parameters.get("max_samples", 256)
        self.min_samples = self.parameters.get("min_samples", 100)
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Keep samples for isolation forest."""
        if "samples" not in stats:
            stats["samples"] = []
            stats["feature_names"] = []
        
        if field_name not in stats["feature_names"]:
            stats["feature_names"].append(field_name)
        
        return stats
    
    def _add_sample(self, values: Dict[str, float], model_state: Dict) -> Dict:
        """Add a complete sample (all features) to the model."""
        if "samples" not in model_state:
            model_state["samples"] = []
            model_state["feature_names"] = list(values.keys())
        
        sample = [values.get(f, 0) for f in model_state["feature_names"]]
        model_state["samples"].append(sample)
        
        # Keep only recent samples
        if len(model_state["samples"]) > self.max_samples:
            model_state["samples"] = model_state["samples"][-self.max_samples:]
        
        return model_state
    
    def _path_length(self, point: List[float], samples: List[List[float]], height: int = 0, limit: int = 10) -> float:
        """Calculate average path length for a point through random trees."""
        if height >= limit or len(samples) <= 1:
            return height + self._c(len(samples))
        
        if not samples or not point:
            return height
        
        n_features = len(point)
        if n_features == 0:
            return height
        
        # Random feature and split
        import random
        feature_idx = random.randint(0, n_features - 1)
        feature_values = [s[feature_idx] for s in samples if len(s) > feature_idx]
        
        if not feature_values:
            return height
        
        min_val, max_val = min(feature_values), max(feature_values)
        if min_val == max_val:
            return height + self._c(len(samples))
        
        split_value = random.uniform(min_val, max_val)
        
        if point[feature_idx] < split_value:
            left_samples = [s for s in samples if len(s) > feature_idx and s[feature_idx] < split_value]
            return self._path_length(point, left_samples, height + 1, limit)
        else:
            right_samples = [s for s in samples if len(s) > feature_idx and s[feature_idx] >= split_value]
            return self._path_length(point, right_samples, height + 1, limit)
    
    def _c(self, n: int) -> float:
        """Average path length of unsuccessful search in BST."""
        if n <= 1:
            return 0
        return 2 * (math.log(n - 1) + 0.5772156649) - (2 * (n - 1) / n)
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Calculate isolation score for the sample."""
        samples = model_state.get("samples", [])
        feature_names = model_state.get("feature_names", list(values.keys()))
        
        if len(samples) < self.min_samples:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                threshold=0.5,
                anomaly_fields=[],
                details={"message": "Not enough training samples"},
            )
        
        point = [values.get(f, 0) for f in feature_names]
        
        # Average path length over multiple trees
        avg_path_length = 0.0
        for _ in range(self.n_estimators):
            avg_path_length += self._path_length(point, samples)
        avg_path_length /= self.n_estimators
        
        # Normalize to [0, 1] score where 1 = anomaly
        c = self._c(len(samples))
        score = 2 ** (-avg_path_length / c) if c > 0 else 0.5
        
        threshold = 1 - self.contamination
        is_anomaly = score > threshold
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(score, 4),
            threshold=round(threshold, 4),
            anomaly_fields=list(values.keys()) if is_anomaly else [],
            details={
                "avg_path_length": round(avg_path_length, 4),
                "expected_path_length": round(c, 4),
                "n_samples": len(samples),
            },
        )


class MahalanobisDetector(BaseAnomalyDetector):
    """
    Mahalanobis Distance based anomaly detection.
    
    Considers correlation between features.
    Good for detecting anomalies in correlated data.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__(parameters)
        self.threshold = self.parameters.get("threshold", 3.0)
        self.min_samples = self.parameters.get("min_samples", 50)
        self.max_samples = self.parameters.get("max_samples", 500)
    
    def update_stats(self, field_name: str, value: float, stats: Dict) -> Dict:
        """Update covariance matrix incrementally."""
        # Similar to Isolation Forest, we need complete samples
        return stats
    
    def _add_sample(self, values: Dict[str, float], model_state: Dict) -> Dict:
        """Add sample and update covariance."""
        if "samples" not in model_state:
            model_state["samples"] = []
            model_state["feature_names"] = list(values.keys())
        
        sample = [values.get(f, 0) for f in model_state["feature_names"]]
        model_state["samples"].append(sample)
        
        if len(model_state["samples"]) > self.max_samples:
            model_state["samples"] = model_state["samples"][-self.max_samples:]
        
        # Recompute mean and covariance
        if len(model_state["samples"]) >= self.min_samples:
            self._compute_covariance(model_state)
        
        return model_state
    
    def _compute_covariance(self, model_state: Dict):
        """Compute mean and inverse covariance matrix."""
        samples = model_state["samples"]
        n = len(samples)
        d = len(samples[0]) if samples else 0
        
        if n < d + 1:  # Need more samples than dimensions
            return
        
        # Calculate mean
        mean = [sum(s[i] for s in samples) / n for i in range(d)]
        
        # Calculate covariance matrix
        cov = [[0.0] * d for _ in range(d)]
        for i in range(d):
            for j in range(d):
                cov[i][j] = sum((s[i] - mean[i]) * (s[j] - mean[j]) for s in samples) / (n - 1)
        
        # Add small regularization for numerical stability
        for i in range(d):
            cov[i][i] += 1e-6
        
        # Compute inverse (simple for small matrices)
        try:
            inv_cov = self._matrix_inverse(cov)
            model_state["mean"] = mean
            model_state["inv_cov"] = inv_cov
        except Exception as e:
            logger.warning(f"Failed to compute inverse covariance: {e}")
    
    def _matrix_inverse(self, matrix: List[List[float]]) -> List[List[float]]:
        """Simple matrix inverse using Gauss-Jordan elimination."""
        n = len(matrix)
        # Augment with identity
        aug = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(matrix)]
        
        for i in range(n):
            # Find pivot
            max_row = max(range(i, n), key=lambda r: abs(aug[r][i]))
            aug[i], aug[max_row] = aug[max_row], aug[i]
            
            if abs(aug[i][i]) < 1e-10:
                raise ValueError("Matrix is singular")
            
            # Scale pivot row
            scale = aug[i][i]
            aug[i] = [x / scale for x in aug[i]]
            
            # Eliminate column
            for j in range(n):
                if i != j:
                    factor = aug[j][i]
                    aug[j] = [aug[j][k] - factor * aug[i][k] for k in range(2 * n)]
        
        return [row[n:] for row in aug]
    
    def evaluate(self, values: Dict[str, float], model_state: Dict) -> AnomalyResult:
        """Calculate Mahalanobis distance for the sample."""
        mean = model_state.get("mean")
        inv_cov = model_state.get("inv_cov")
        feature_names = model_state.get("feature_names", list(values.keys()))
        
        if mean is None or inv_cov is None:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                threshold=self.threshold,
                anomaly_fields=[],
                details={"message": "Not enough training data for covariance"},
            )
        
        point = [values.get(f, 0) for f in feature_names]
        d = len(mean)
        
        # Calculate Mahalanobis distance
        diff = [point[i] - mean[i] for i in range(d)]
        
        # d^T * inv_cov * d
        temp = [sum(diff[j] * inv_cov[i][j] for j in range(d)) for i in range(d)]
        distance_sq = sum(diff[i] * temp[i] for i in range(d))
        distance = math.sqrt(max(0, distance_sq))
        
        is_anomaly = distance > self.threshold
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(distance, 4),
            threshold=self.threshold,
            anomaly_fields=list(values.keys()) if is_anomaly else [],
            details={
                "mahalanobis_distance": round(distance, 4),
                "mean": [round(m, 4) for m in mean],
            },
        )


# Factory for creating detectors
DETECTOR_CLASSES = {
    "zscore": ZScoreDetector,
    "hbos": HBOSDetector,
    "ecod": ECODDetector,
    "isolation_forest": IsolationForestDetector,
    "mahalanobis": MahalanobisDetector,
}


def create_detector(algorithm: str, parameters: Dict[str, Any] = None) -> BaseAnomalyDetector:
    """Create an anomaly detector of the specified type."""
    if algorithm not in DETECTOR_CLASSES:
        raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list(DETECTOR_CLASSES.keys())}")
    
    return DETECTOR_CLASSES[algorithm](parameters)


class AnomalyEngine:
    """
    Main engine for managing anomaly detection across CDC events.
    
    Handles:
    - Training (updating statistics)
    - Evaluation (checking for anomalies)
    - Integration with Rule Engine
    """
    
    def __init__(self):
        self.detectors: Dict[int, BaseAnomalyDetector] = {}
    
    def get_detector(self, detector_id: int, algorithm: str, parameters: Dict[str, Any]) -> BaseAnomalyDetector:
        """Get or create a detector instance."""
        if detector_id not in self.detectors:
            self.detectors[detector_id] = create_detector(algorithm, parameters)
        return self.detectors[detector_id]
    
    def process_event(
        self,
        detector_config: Dict[str, Any],
        event_data: Dict[str, Any],
        model_state: Dict[str, Any],
    ) -> Tuple[AnomalyResult, Dict[str, Any]]:
        """
        Process a CDC event for anomaly detection.
        
        Returns:
            Tuple of (AnomalyResult, updated_model_state)
        """
        detector_id = detector_config.get("id")
        algorithm = detector_config.get("algorithm", "zscore")
        parameters = detector_config.get("parameters", {})
        target_columns = detector_config.get("target_columns", [])
        
        detector = self.get_detector(detector_id, algorithm, parameters)
        
        # Extract numeric values for target columns
        values = {}
        data = event_data.get("data", event_data)
        
        for col in target_columns:
            if col in data:
                try:
                    values[col] = float(data[col])
                except (ValueError, TypeError):
                    continue
        
        if not values:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                threshold=0.0,
                details={"message": "No numeric values to evaluate"},
            ), model_state
        
        # Initialize model state if needed
        if "field_stats" not in model_state:
            model_state["field_stats"] = {}
        
        # Update statistics (training)
        for field_name, value in values.items():
            model_state["field_stats"] = detector.update_stats(
                field_name, value, model_state["field_stats"]
            )
        
        # For multi-dimensional detectors, add complete sample
        if algorithm in ["isolation_forest", "mahalanobis"]:
            if hasattr(detector, "_add_sample"):
                model_state = detector._add_sample(values, model_state)
        
        # Evaluate for anomaly
        result = detector.evaluate(values, model_state)
        
        return result, model_state


# Global engine instance
anomaly_engine = AnomalyEngine()

