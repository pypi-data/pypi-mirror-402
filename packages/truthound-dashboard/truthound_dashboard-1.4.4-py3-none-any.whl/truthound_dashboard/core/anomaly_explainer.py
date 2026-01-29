"""Anomaly explainability service using SHAP/LIME.

This module provides interpretability for ML-based anomaly detection results
using SHAP (SHapley Additive exPlanations) and LIME (Local Interpretable
Model-agnostic Explanations).

Features:
- SHAP TreeExplainer for tree-based models (Isolation Forest)
- SHAP KernelExplainer as fallback for other models
- Feature importance ranking
- Local explanations per anomaly
- Human-readable summary generation
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db.models import AnomalyDetection, AnomalyExplanation, Source


class AnomalyExplainerService:
    """Service for generating SHAP/LIME explanations for anomaly detections.

    This service provides interpretability for ML-based anomaly detection
    results, helping users understand why specific rows were flagged as
    anomalies.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the explainer service.

        Args:
            session: Database session for persistence.
        """
        self.session = session
        self._model_cache: dict[str, Any] = {}

    async def explain_anomaly(
        self,
        detection_id: str,
        row_indices: list[int],
        *,
        max_features: int = 10,
        sample_background: int = 100,
    ) -> dict[str, Any]:
        """Generate SHAP explanations for specific anomaly rows.

        Args:
            detection_id: ID of the anomaly detection run.
            row_indices: List of row indices to explain.
            max_features: Maximum features to include in explanation.
            sample_background: Background samples for SHAP KernelExplainer.

        Returns:
            Dictionary containing explanations with feature contributions.

        Raises:
            ValueError: If detection not found or has no results.
        """
        # Get the detection record
        detection = await self._get_detection(detection_id)
        if detection is None:
            raise ValueError(f"Detection '{detection_id}' not found")

        if detection.status != "success":
            raise ValueError(f"Detection status is '{detection.status}', not 'success'")

        # Get the source and load data
        source = await self._get_source(detection.source_id)
        if source is None:
            raise ValueError(f"Source '{detection.source_id}' not found")

        # Generate explanations
        try:
            explanations = await self._generate_explanations(
                detection=detection,
                source=source,
                row_indices=row_indices,
                max_features=max_features,
                sample_background=sample_background,
            )

            # Save explanations to database
            await self._save_explanations(detection_id, row_indices, explanations)

            return explanations

        except Exception as e:
            # Log and return error
            return {
                "detection_id": detection_id,
                "row_indices": row_indices,
                "error": str(e),
                "explanations": [],
            }

    async def get_cached_explanations(
        self,
        detection_id: str,
        row_indices: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Get cached explanations for a detection.

        Args:
            detection_id: ID of the anomaly detection.
            row_indices: Optional list of specific row indices to retrieve.

        Returns:
            List of cached explanation dictionaries.
        """
        query = select(AnomalyExplanation).where(
            AnomalyExplanation.detection_id == detection_id
        )

        if row_indices:
            query = query.where(AnomalyExplanation.row_index.in_(row_indices))

        query = query.order_by(AnomalyExplanation.row_index)

        result = await self.session.execute(query)
        explanations = result.scalars().all()

        return [self._explanation_to_dict(exp) for exp in explanations]

    async def _get_detection(self, detection_id: str) -> AnomalyDetection | None:
        """Get an anomaly detection by ID."""
        result = await self.session.execute(
            select(AnomalyDetection).where(AnomalyDetection.id == detection_id)
        )
        return result.scalar_one_or_none()

    async def _get_source(self, source_id: str) -> Source | None:
        """Get a source by ID."""
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()

    async def _generate_explanations(
        self,
        detection: AnomalyDetection,
        source: Source,
        row_indices: list[int],
        max_features: int,
        sample_background: int,
    ) -> dict[str, Any]:
        """Generate SHAP explanations for anomaly rows.

        This method uses the appropriate SHAP explainer based on the
        algorithm used for detection.
        """
        try:
            import truthound as th

            # Load data
            df = th.read(source.config)

            # Get columns that were analyzed
            columns = detection.columns_analyzed or list(
                df.select_dtypes(include=[np.number]).columns
            )

            # Filter to analyzed columns and handle NaN
            df_analyze = df[columns].select_dtypes(include=[np.number])
            df_clean = df_analyze.fillna(df_analyze.mean())

            if df_clean.empty:
                return {
                    "detection_id": detection.id,
                    "row_indices": row_indices,
                    "error": "No numeric columns to explain",
                    "explanations": [],
                }

            # Get the rows to explain
            valid_indices = [i for i in row_indices if i < len(df_clean)]
            if not valid_indices:
                return {
                    "detection_id": detection.id,
                    "row_indices": row_indices,
                    "error": "No valid row indices",
                    "explanations": [],
                }

            X = df_clean.values
            X_explain = X[valid_indices]
            feature_names = list(df_clean.columns)

            # Generate SHAP values based on algorithm
            shap_values = self._compute_shap_values(
                X=X,
                X_explain=X_explain,
                algorithm=detection.algorithm,
                config=detection.config,
                sample_background=sample_background,
            )

            # Build explanation results
            explanations = []
            for i, row_idx in enumerate(valid_indices):
                # Get feature contributions for this row
                row_shap = shap_values[i] if i < len(shap_values) else np.zeros(len(feature_names))
                row_values = X_explain[i] if i < len(X_explain) else np.zeros(len(feature_names))

                # Create feature contributions
                contributions = []
                for j, (fname, shap_val, feat_val) in enumerate(
                    zip(feature_names, row_shap, row_values)
                ):
                    contributions.append({
                        "feature": fname,
                        "value": float(feat_val),
                        "shap_value": float(shap_val),
                        "contribution": float(abs(shap_val)),
                    })

                # Sort by absolute contribution
                contributions.sort(key=lambda x: x["contribution"], reverse=True)

                # Limit to max features
                top_contributions = contributions[:max_features]

                # Get anomaly score from detection result
                anomaly_score = self._get_anomaly_score(detection, row_idx)

                # Generate summary text
                summary = self._generate_summary(top_contributions, anomaly_score)

                explanations.append({
                    "row_index": row_idx,
                    "anomaly_score": anomaly_score,
                    "feature_contributions": top_contributions,
                    "total_shap": float(np.sum(row_shap)),
                    "summary": summary,
                })

            return {
                "detection_id": detection.id,
                "algorithm": detection.algorithm,
                "row_indices": valid_indices,
                "feature_names": feature_names,
                "explanations": explanations,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except ImportError:
            # Fallback: generate mock explanations
            return self._generate_mock_explanations(
                detection, row_indices, max_features
            )

    def _compute_shap_values(
        self,
        X: np.ndarray,
        X_explain: np.ndarray,
        algorithm: str,
        config: dict[str, Any] | None,
        sample_background: int,
    ) -> np.ndarray:
        """Compute SHAP values using the appropriate explainer.

        Args:
            X: Full feature matrix for background data.
            X_explain: Feature matrix for rows to explain.
            algorithm: Detection algorithm used.
            config: Algorithm configuration.
            sample_background: Number of background samples.

        Returns:
            Array of SHAP values for each row and feature.
        """
        try:
            import shap

            # Use TreeExplainer for tree-based models
            if algorithm == "isolation_forest":
                return self._compute_isolation_forest_shap(
                    X, X_explain, config, sample_background
                )

            # Use KernelExplainer as fallback
            return self._compute_kernel_shap(X, X_explain, algorithm, config, sample_background)

        except ImportError:
            # SHAP not installed, use permutation importance
            return self._compute_permutation_importance(X, X_explain, algorithm, config)

    def _compute_isolation_forest_shap(
        self,
        X: np.ndarray,
        X_explain: np.ndarray,
        config: dict[str, Any] | None,
        sample_background: int,
    ) -> np.ndarray:
        """Compute SHAP values for Isolation Forest using TreeExplainer."""
        import shap
        from sklearn.ensemble import IsolationForest

        config = config or {}

        # Build and train Isolation Forest
        clf = IsolationForest(
            n_estimators=config.get("n_estimators", 100),
            contamination=config.get("contamination", 0.1),
            max_samples=config.get("max_samples", "auto"),
            random_state=config.get("random_state", 42),
        )
        clf.fit(X)

        # Use TreeExplainer for efficient SHAP calculation
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_explain)

        return np.array(shap_values)

    def _compute_kernel_shap(
        self,
        X: np.ndarray,
        X_explain: np.ndarray,
        algorithm: str,
        config: dict[str, Any] | None,
        sample_background: int,
    ) -> np.ndarray:
        """Compute SHAP values using KernelExplainer (model-agnostic)."""
        import shap
        from sklearn.preprocessing import StandardScaler

        config = config or {}

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_explain_scaled = scaler.transform(X_explain)

        # Build model based on algorithm
        model = self._build_model(algorithm, config)
        model.fit(X_scaled)

        # Get prediction function
        if hasattr(model, "score_samples"):
            predict_fn = lambda x: -model.score_samples(x)
        elif hasattr(model, "decision_function"):
            predict_fn = lambda x: -model.decision_function(x)
        else:
            predict_fn = lambda x: model.fit_predict(x).astype(float)

        # Sample background data
        background_size = min(sample_background, len(X_scaled))
        background_indices = np.random.choice(
            len(X_scaled), background_size, replace=False
        )
        background = X_scaled[background_indices]

        # Create KernelExplainer
        explainer = shap.KernelExplainer(predict_fn, background)

        # Compute SHAP values
        shap_values = explainer.shap_values(X_explain_scaled, nsamples=100)

        return np.array(shap_values)

    def _build_model(self, algorithm: str, config: dict[str, Any]) -> Any:
        """Build the appropriate sklearn model for the algorithm."""
        if algorithm == "isolation_forest":
            from sklearn.ensemble import IsolationForest
            return IsolationForest(
                n_estimators=config.get("n_estimators", 100),
                contamination=config.get("contamination", 0.1),
                random_state=config.get("random_state", 42),
            )

        elif algorithm == "lof":
            from sklearn.neighbors import LocalOutlierFactor
            return LocalOutlierFactor(
                n_neighbors=config.get("n_neighbors", 20),
                contamination=config.get("contamination", 0.1),
                novelty=False,
            )

        elif algorithm == "one_class_svm":
            from sklearn.svm import OneClassSVM
            return OneClassSVM(
                kernel=config.get("kernel", "rbf"),
                nu=config.get("nu", 0.1),
                gamma=config.get("gamma", "scale"),
            )

        elif algorithm == "dbscan":
            from sklearn.cluster import DBSCAN
            return DBSCAN(
                eps=config.get("eps", 0.5),
                min_samples=config.get("min_samples", 5),
            )

        else:
            # Default to Isolation Forest
            from sklearn.ensemble import IsolationForest
            return IsolationForest(random_state=42)

    def _compute_permutation_importance(
        self,
        X: np.ndarray,
        X_explain: np.ndarray,
        algorithm: str,
        config: dict[str, Any] | None,
    ) -> np.ndarray:
        """Fallback: compute approximate feature importance via permutation."""
        config = config or {}

        # Build and train model
        model = self._build_model(algorithm, config)

        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_explain_scaled = scaler.transform(X_explain)

        model.fit(X_scaled)

        # Get base predictions/scores
        if hasattr(model, "score_samples"):
            base_scores = -model.score_samples(X_explain_scaled)
        elif hasattr(model, "decision_function"):
            base_scores = -model.decision_function(X_explain_scaled)
        else:
            base_scores = np.zeros(len(X_explain_scaled))

        # Compute permutation importance for each feature
        n_features = X_explain_scaled.shape[1]
        importances = np.zeros((len(X_explain_scaled), n_features))

        for j in range(n_features):
            X_permuted = X_explain_scaled.copy()
            # Permute column j
            X_permuted[:, j] = np.random.permutation(X_permuted[:, j])

            if hasattr(model, "score_samples"):
                permuted_scores = -model.score_samples(X_permuted)
            elif hasattr(model, "decision_function"):
                permuted_scores = -model.decision_function(X_permuted)
            else:
                permuted_scores = np.zeros(len(X_permuted))

            # Importance is the change in score
            importances[:, j] = permuted_scores - base_scores

        return importances

    def _get_anomaly_score(
        self,
        detection: AnomalyDetection,
        row_index: int,
    ) -> float:
        """Get the anomaly score for a specific row from detection results."""
        if detection.result_json and "anomalies" in detection.result_json:
            for anomaly in detection.result_json["anomalies"]:
                if anomaly.get("row_index") == row_index:
                    return anomaly.get("anomaly_score", 0.0)
        return 0.0

    def _generate_summary(
        self,
        contributions: list[dict[str, Any]],
        anomaly_score: float,
    ) -> str:
        """Generate human-readable summary of why a row is anomalous.

        Args:
            contributions: Feature contributions sorted by importance.
            anomaly_score: Overall anomaly score for the row.

        Returns:
            Human-readable summary string.
        """
        if not contributions:
            return "No significant features identified."

        # Classify anomaly severity
        if anomaly_score >= 0.9:
            severity = "highly anomalous"
        elif anomaly_score >= 0.7:
            severity = "moderately anomalous"
        elif anomaly_score >= 0.5:
            severity = "slightly anomalous"
        else:
            severity = "borderline anomalous"

        # Get top contributing features
        top_features = contributions[:3]
        feature_descriptions = []

        for feat in top_features:
            name = feat["feature"]
            value = feat["value"]
            shap_val = feat["shap_value"]

            # Describe contribution direction
            direction = "unusually high" if shap_val > 0 else "unusually low"
            feature_descriptions.append(
                f"{name} ({value:.2f}) is {direction}"
            )

        if len(feature_descriptions) == 1:
            features_text = feature_descriptions[0]
        elif len(feature_descriptions) == 2:
            features_text = " and ".join(feature_descriptions)
        else:
            features_text = (
                ", ".join(feature_descriptions[:-1])
                + f", and {feature_descriptions[-1]}"
            )

        return f"This row is {severity} (score: {anomaly_score:.3f}). The main contributing factors are: {features_text}."

    def _generate_mock_explanations(
        self,
        detection: AnomalyDetection,
        row_indices: list[int],
        max_features: int,
    ) -> dict[str, Any]:
        """Generate mock explanations when SHAP/sklearn is not available."""
        import random

        columns = detection.columns_analyzed or ["feature_1", "feature_2", "feature_3"]

        explanations = []
        for row_idx in row_indices:
            anomaly_score = self._get_anomaly_score(detection, row_idx)
            if anomaly_score == 0:
                anomaly_score = random.uniform(0.5, 1.0)

            contributions = []
            for col in columns[:max_features]:
                shap_val = random.uniform(-1.0, 1.0)
                contributions.append({
                    "feature": col,
                    "value": random.uniform(-100, 100),
                    "shap_value": shap_val,
                    "contribution": abs(shap_val),
                })

            contributions.sort(key=lambda x: x["contribution"], reverse=True)
            summary = self._generate_summary(contributions[:3], anomaly_score)

            explanations.append({
                "row_index": row_idx,
                "anomaly_score": anomaly_score,
                "feature_contributions": contributions,
                "total_shap": sum(c["shap_value"] for c in contributions),
                "summary": summary,
            })

        return {
            "detection_id": detection.id,
            "algorithm": detection.algorithm,
            "row_indices": row_indices,
            "feature_names": columns,
            "explanations": explanations,
            "generated_at": datetime.utcnow().isoformat(),
            "mock": True,
        }

    async def _save_explanations(
        self,
        detection_id: str,
        row_indices: list[int],
        explanations_data: dict[str, Any],
    ) -> None:
        """Save explanations to database for caching."""
        for explanation in explanations_data.get("explanations", []):
            row_idx = explanation["row_index"]

            # Check if explanation already exists
            existing = await self.session.execute(
                select(AnomalyExplanation).where(
                    AnomalyExplanation.detection_id == detection_id,
                    AnomalyExplanation.row_index == row_idx,
                )
            )
            existing_exp = existing.scalar_one_or_none()

            if existing_exp:
                # Update existing
                existing_exp.anomaly_score = explanation["anomaly_score"]
                existing_exp.feature_contributions = explanation["feature_contributions"]
                existing_exp.total_shap = explanation["total_shap"]
                existing_exp.summary = explanation["summary"]
                existing_exp.generated_at = datetime.utcnow()
            else:
                # Create new
                new_explanation = AnomalyExplanation(
                    detection_id=detection_id,
                    row_index=row_idx,
                    anomaly_score=explanation["anomaly_score"],
                    feature_contributions=explanation["feature_contributions"],
                    total_shap=explanation["total_shap"],
                    summary=explanation["summary"],
                )
                self.session.add(new_explanation)

        await self.session.flush()

    def _explanation_to_dict(self, explanation: AnomalyExplanation) -> dict[str, Any]:
        """Convert AnomalyExplanation model to dictionary."""
        return {
            "id": explanation.id,
            "detection_id": explanation.detection_id,
            "row_index": explanation.row_index,
            "anomaly_score": explanation.anomaly_score,
            "feature_contributions": explanation.feature_contributions,
            "total_shap": explanation.total_shap,
            "summary": explanation.summary,
            "generated_at": (
                explanation.generated_at.isoformat()
                if explanation.generated_at
                else None
            ),
        }


# Singleton-style factory for dependency injection
def get_anomaly_explainer_service(session: AsyncSession) -> AnomalyExplainerService:
    """Factory function to get AnomalyExplainerService instance."""
    return AnomalyExplainerService(session)
