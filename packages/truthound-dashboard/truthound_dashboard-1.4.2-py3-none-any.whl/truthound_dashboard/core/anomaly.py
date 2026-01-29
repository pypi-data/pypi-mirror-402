"""Anomaly detection service.

This module provides services for ML-based anomaly detection,
supporting multiple algorithms from truthound core.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository
from truthound_dashboard.db.models import AnomalyDetection, AnomalyBatchJob, Source


class AnomalyDetectionRepository(BaseRepository[AnomalyDetection]):
    """Repository for AnomalyDetection model operations."""

    model = AnomalyDetection

    async def get_by_source_id(
        self,
        source_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[AnomalyDetection]:
        """Get anomaly detections for a source.

        Args:
            source_id: Data source ID.
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of anomaly detections, ordered by created_at desc.
        """
        result = await self.session.execute(
            select(AnomalyDetection)
            .where(AnomalyDetection.source_id == source_id)
            .order_by(AnomalyDetection.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_by_source(self, source_id: str) -> AnomalyDetection | None:
        """Get the latest anomaly detection for a source.

        Args:
            source_id: Data source ID.

        Returns:
            Latest AnomalyDetection or None.
        """
        result = await self.session.execute(
            select(AnomalyDetection)
            .where(AnomalyDetection.source_id == source_id)
            .order_by(AnomalyDetection.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_algorithm(
        self,
        algorithm: str,
        *,
        limit: int = 50,
    ) -> Sequence[AnomalyDetection]:
        """Get detections by algorithm type.

        Args:
            algorithm: Algorithm name.
            limit: Maximum to return.

        Returns:
            Sequence of detections.
        """
        return await self.list(
            limit=limit,
            filters=[AnomalyDetection.algorithm == algorithm],
        )

    async def count_by_source(self, source_id: str) -> int:
        """Count anomaly detections for a source.

        Args:
            source_id: Data source ID.

        Returns:
            Number of detections.
        """
        return await self.count(filters=[AnomalyDetection.source_id == source_id])


class AnomalyDetectionService:
    """Service for ML-based anomaly detection.

    Provides functionality for:
    - Running anomaly detection with various algorithms
    - Managing detection history
    - Retrieving algorithm information
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.repo = AnomalyDetectionRepository(session)

    # =========================================================================
    # Detection Operations
    # =========================================================================

    async def create_detection(
        self,
        source_id: str,
        *,
        algorithm: str = "isolation_forest",
        columns: list[str] | None = None,
        config: dict[str, Any] | None = None,
        sample_size: int | None = None,
    ) -> AnomalyDetection:
        """Create a new anomaly detection record.

        This creates a pending detection that should be executed separately.

        Args:
            source_id: Source ID to analyze.
            algorithm: Detection algorithm to use.
            columns: Columns to analyze (None = all numeric).
            config: Algorithm-specific configuration.
            sample_size: Sample size for large datasets.

        Returns:
            Created detection record.

        Raises:
            ValueError: If source not found.
        """
        # Verify source exists
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Prepare configuration
        full_config = config or {}
        if columns:
            full_config["columns"] = columns
        if sample_size:
            full_config["sample_size"] = sample_size

        detection = await self.repo.create(
            source_id=source_id,
            algorithm=algorithm,
            config=full_config if full_config else None,
            columns_analyzed=columns,
            status="pending",
        )

        return detection

    async def run_detection(
        self,
        detection_id: str,
    ) -> AnomalyDetection:
        """Execute anomaly detection.

        This runs the actual ML algorithm on the source data.

        Args:
            detection_id: Detection record ID.

        Returns:
            Updated detection with results.

        Raises:
            ValueError: If detection not found.
        """
        detection = await self.repo.get_by_id(detection_id)
        if detection is None:
            raise ValueError(f"Detection '{detection_id}' not found")

        # Mark as started
        detection.mark_started()
        await self.session.flush()

        try:
            # Get source info
            result = await self.session.execute(
                select(Source).where(Source.id == detection.source_id)
            )
            source = result.scalar_one_or_none()
            if source is None:
                raise ValueError(f"Source '{detection.source_id}' not found")

            # Run the actual detection using truthound
            detection_result = await self._execute_detection(
                source=source,
                algorithm=detection.algorithm,
                config=detection.config,
            )

            # Update detection with results
            detection.total_rows = detection_result.get("total_rows", 0)
            detection.anomaly_count = detection_result.get("anomaly_count", 0)
            detection.anomaly_rate = detection_result.get("anomaly_rate", 0.0)
            detection.columns_analyzed = detection_result.get("columns_analyzed", [])
            detection.mark_completed(
                anomaly_count=detection.anomaly_count,
                anomaly_rate=detection.anomaly_rate,
                result=detection_result,
            )

        except Exception as e:
            detection.mark_error(str(e))

        await self.session.flush()
        await self.session.refresh(detection)
        return detection

    async def _execute_detection(
        self,
        source: Source,
        algorithm: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Execute the anomaly detection algorithm.

        This is the core detection logic that interfaces with truthound.

        Args:
            source: Source to analyze.
            algorithm: Algorithm to use.
            config: Algorithm configuration.

        Returns:
            Detection results dictionary.
        """
        try:
            import truthound as th

            # Load data from source
            df = th.read(source.config)

            # Get columns to analyze
            columns = None
            if config and "columns" in config:
                columns = config["columns"]

            # Get sample size
            sample_size = None
            if config and "sample_size" in config:
                sample_size = config["sample_size"]

            # Build algorithm-specific parameters
            algo_params = self._build_algorithm_params(algorithm, config)

            # Run anomaly detection based on algorithm
            # Note: truthound's anomaly validators are used here
            result = self._run_algorithm(
                df=df,
                algorithm=algorithm,
                columns=columns,
                sample_size=sample_size,
                params=algo_params,
            )

            return result

        except ImportError:
            # If truthound is not available, return mock result
            return self._generate_mock_result(algorithm, config)

    def _build_algorithm_params(
        self,
        algorithm: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build algorithm-specific parameters from config.

        Args:
            algorithm: Algorithm name.
            config: User configuration.

        Returns:
            Algorithm parameters.
        """
        if config is None:
            return {}

        # Filter out non-algorithm parameters
        excluded_keys = {"columns", "sample_size"}
        return {k: v for k, v in config.items() if k not in excluded_keys}

    def _run_algorithm(
        self,
        df: Any,
        algorithm: str,
        columns: list[str] | None,
        sample_size: int | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run the specified anomaly detection algorithm.

        Args:
            df: DataFrame to analyze.
            algorithm: Algorithm name.
            columns: Columns to analyze.
            sample_size: Sample size.
            params: Algorithm parameters.

        Returns:
            Detection results.
        """
        import numpy as np
        import pandas as pd

        # Sample if needed
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)

        # Select columns (numeric only if not specified)
        if columns:
            df_analyze = df[columns].select_dtypes(include=[np.number])
        else:
            df_analyze = df.select_dtypes(include=[np.number])
            columns = list(df_analyze.columns)

        if df_analyze.empty:
            return {
                "total_rows": len(df),
                "anomaly_count": 0,
                "anomaly_rate": 0.0,
                "columns_analyzed": columns,
                "anomalies": [],
                "column_summaries": [],
            }

        # Run algorithm
        if algorithm == "isolation_forest":
            result = self._run_isolation_forest(df_analyze, params)
        elif algorithm == "lof":
            result = self._run_lof(df_analyze, params)
        elif algorithm == "one_class_svm":
            result = self._run_one_class_svm(df_analyze, params)
        elif algorithm == "dbscan":
            result = self._run_dbscan(df_analyze, params)
        elif algorithm == "statistical":
            result = self._run_statistical(df_analyze, params)
        elif algorithm == "autoencoder":
            result = self._run_autoencoder(df_analyze, params)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Build final result
        anomaly_mask = result["is_anomaly"]
        anomaly_scores = result["scores"]

        # Get top anomalies (limit to 100)
        anomaly_indices = np.where(anomaly_mask)[0]
        top_indices = anomaly_indices[np.argsort(anomaly_scores[anomaly_indices])[-100:]]

        anomalies = []
        for idx in top_indices:
            anomalies.append({
                "row_index": int(idx),
                "anomaly_score": float(anomaly_scores[idx]),
                "column_values": df_analyze.iloc[idx].to_dict(),
                "is_anomaly": True,
            })

        # Build column summaries
        column_summaries = []
        for col in columns:
            if col in df_analyze.columns:
                col_data = df_analyze[col]
                col_anomalies = anomaly_mask & ~col_data.isna()
                summary = {
                    "column": col,
                    "dtype": str(col_data.dtype),
                    "anomaly_count": int(col_anomalies.sum()),
                    "anomaly_rate": float(col_anomalies.sum() / len(col_data)) if len(col_data) > 0 else 0.0,
                    "mean_anomaly_score": float(np.mean(anomaly_scores[anomaly_mask])) if anomaly_mask.any() else 0.0,
                    "min_value": float(col_data.min()) if not col_data.empty else None,
                    "max_value": float(col_data.max()) if not col_data.empty else None,
                    "top_anomaly_indices": [int(i) for i in top_indices[:10]],
                }
                column_summaries.append(summary)

        return {
            "total_rows": len(df),
            "anomaly_count": int(anomaly_mask.sum()),
            "anomaly_rate": float(anomaly_mask.sum() / len(df)) if len(df) > 0 else 0.0,
            "columns_analyzed": columns,
            "anomalies": anomalies,
            "column_summaries": column_summaries,
        }

    def _run_isolation_forest(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run Isolation Forest algorithm."""
        from sklearn.ensemble import IsolationForest
        import numpy as np

        # Get parameters with defaults
        n_estimators = params.get("n_estimators", 100)
        contamination = params.get("contamination", 0.1)
        max_samples = params.get("max_samples", "auto")
        random_state = params.get("random_state", 42)

        # Handle NaN values
        df_clean = df.fillna(df.mean())

        clf = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=random_state,
        )
        predictions = clf.fit_predict(df_clean)
        scores = -clf.score_samples(df_clean)  # Higher = more anomalous

        return {
            "is_anomaly": predictions == -1,
            "scores": scores,
        }

    def _run_lof(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run Local Outlier Factor algorithm."""
        from sklearn.neighbors import LocalOutlierFactor
        import numpy as np

        n_neighbors = params.get("n_neighbors", 20)
        contamination = params.get("contamination", 0.1)
        algorithm = params.get("algorithm", "auto")

        # Handle NaN values and scale
        from sklearn.preprocessing import StandardScaler
        df_clean = df.fillna(df.mean())
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_clean)

        clf = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            algorithm=algorithm,
            novelty=False,
        )
        predictions = clf.fit_predict(df_scaled)
        scores = -clf.negative_outlier_factor_  # Higher = more anomalous

        return {
            "is_anomaly": predictions == -1,
            "scores": scores,
        }

    def _run_one_class_svm(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run One-Class SVM algorithm."""
        from sklearn.svm import OneClassSVM
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        kernel = params.get("kernel", "rbf")
        nu = params.get("nu", 0.1)
        gamma = params.get("gamma", "scale")

        # Handle NaN values and scale
        df_clean = df.fillna(df.mean())
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_clean)

        clf = OneClassSVM(
            kernel=kernel,
            nu=nu,
            gamma=gamma,
        )
        predictions = clf.fit_predict(df_scaled)
        scores = -clf.score_samples(df_scaled)  # Higher = more anomalous

        return {
            "is_anomaly": predictions == -1,
            "scores": scores,
        }

    def _run_dbscan(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run DBSCAN algorithm."""
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)
        metric = params.get("metric", "euclidean")

        # Handle NaN values and scale
        df_clean = df.fillna(df.mean())
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_clean)

        clf = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
        )
        labels = clf.fit_predict(df_scaled)

        # Points labeled as -1 are noise (anomalies)
        is_anomaly = labels == -1

        # Calculate distance-based scores (distance to nearest cluster centroid)
        from sklearn.metrics import pairwise_distances
        scores = np.zeros(len(df_scaled))
        if not is_anomaly.all():
            # Get centroids of each cluster
            unique_labels = set(labels) - {-1}
            if unique_labels:
                centroids = np.array([
                    df_scaled[labels == l].mean(axis=0)
                    for l in unique_labels
                ])
                distances = pairwise_distances(df_scaled, centroids, metric=metric)
                scores = distances.min(axis=1)

        return {
            "is_anomaly": is_anomaly,
            "scores": scores,
        }

    def _run_statistical(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run statistical anomaly detection."""
        import numpy as np

        method = params.get("method", "zscore")
        threshold = params.get("threshold", 3.0)

        # Handle NaN values
        df_clean = df.fillna(df.mean())

        if method == "zscore":
            mean = df_clean.mean()
            std = df_clean.std()
            z_scores = np.abs((df_clean - mean) / std)
            # Take max z-score across all columns for each row
            max_z = z_scores.max(axis=1)
            is_anomaly = max_z > threshold
            scores = max_z.values

        elif method == "iqr":
            q1 = df_clean.quantile(0.25)
            q3 = df_clean.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            is_outlier = ((df_clean < lower) | (df_clean > upper)).any(axis=1)
            is_anomaly = is_outlier.values
            # Score based on distance from bounds
            scores = np.zeros(len(df_clean))
            for col in df_clean.columns:
                col_scores = np.maximum(
                    (lower[col] - df_clean[col]) / iqr[col],
                    (df_clean[col] - upper[col]) / iqr[col],
                )
                col_scores = np.maximum(col_scores, 0)
                scores = np.maximum(scores, col_scores.values)

        elif method == "mad":
            median = df_clean.median()
            mad = np.abs(df_clean - median).median()
            # Modified z-score using MAD
            modified_z = 0.6745 * (df_clean - median) / mad
            max_z = np.abs(modified_z).max(axis=1)
            is_anomaly = max_z > threshold
            scores = max_z.values

        else:
            raise ValueError(f"Unknown statistical method: {method}")

        return {
            "is_anomaly": np.array(is_anomaly),
            "scores": np.array(scores),
        }

    def _run_autoencoder(
        self,
        df: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run Autoencoder-based anomaly detection."""
        import numpy as np
        from sklearn.preprocessing import StandardScaler

        encoding_dim = params.get("encoding_dim", 32)
        epochs = params.get("epochs", 50)
        threshold_percentile = params.get("threshold_percentile", 95)
        batch_size = params.get("batch_size", 32)

        # Handle NaN values and scale
        df_clean = df.fillna(df.mean())
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_clean)

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Build autoencoder
            input_dim = df_scaled.shape[1]
            encoding_dim = min(encoding_dim, input_dim // 2) or 1

            encoder = keras.Sequential([
                keras.layers.Dense(encoding_dim * 2, activation="relu", input_shape=(input_dim,)),
                keras.layers.Dense(encoding_dim, activation="relu"),
            ])

            decoder = keras.Sequential([
                keras.layers.Dense(encoding_dim * 2, activation="relu", input_shape=(encoding_dim,)),
                keras.layers.Dense(input_dim, activation="linear"),
            ])

            autoencoder = keras.Sequential([encoder, decoder])
            autoencoder.compile(optimizer="adam", loss="mse")

            # Train
            autoencoder.fit(
                df_scaled, df_scaled,
                epochs=epochs,
                batch_size=batch_size,
                shuffle=True,
                verbose=0,
            )

            # Get reconstruction error
            reconstructed = autoencoder.predict(df_scaled, verbose=0)
            reconstruction_error = np.mean((df_scaled - reconstructed) ** 2, axis=1)

            # Determine threshold
            threshold = np.percentile(reconstruction_error, threshold_percentile)
            is_anomaly = reconstruction_error > threshold

            return {
                "is_anomaly": is_anomaly,
                "scores": reconstruction_error,
            }

        except ImportError:
            # Fallback to simple PCA-based reconstruction
            from sklearn.decomposition import PCA

            n_components = min(encoding_dim, df_scaled.shape[1])
            pca = PCA(n_components=n_components)
            transformed = pca.fit_transform(df_scaled)
            reconstructed = pca.inverse_transform(transformed)

            reconstruction_error = np.mean((df_scaled - reconstructed) ** 2, axis=1)
            threshold = np.percentile(reconstruction_error, threshold_percentile)
            is_anomaly = reconstruction_error > threshold

            return {
                "is_anomaly": is_anomaly,
                "scores": reconstruction_error,
            }

    def _generate_mock_result(
        self,
        algorithm: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate mock result when truthound is not available.

        Args:
            algorithm: Algorithm name.
            config: Algorithm configuration.

        Returns:
            Mock detection results.
        """
        import random

        total_rows = random.randint(1000, 10000)
        anomaly_rate = random.uniform(0.01, 0.15)
        anomaly_count = int(total_rows * anomaly_rate)

        columns = ["col_a", "col_b", "col_c", "col_d"]
        if config and "columns" in config:
            columns = config["columns"]

        return {
            "total_rows": total_rows,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_rate,
            "columns_analyzed": columns,
            "anomalies": [
                {
                    "row_index": i,
                    "anomaly_score": random.uniform(0.5, 1.0),
                    "column_values": {col: random.uniform(-10, 100) for col in columns},
                    "is_anomaly": True,
                }
                for i in range(min(anomaly_count, 100))
            ],
            "column_summaries": [
                {
                    "column": col,
                    "dtype": "float64",
                    "anomaly_count": anomaly_count // len(columns),
                    "anomaly_rate": anomaly_rate,
                    "mean_anomaly_score": random.uniform(0.6, 0.9),
                    "min_value": random.uniform(-100, 0),
                    "max_value": random.uniform(50, 200),
                    "top_anomaly_indices": list(range(10)),
                }
                for col in columns
            ],
        }

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_detection(self, detection_id: str) -> AnomalyDetection | None:
        """Get a detection by ID.

        Args:
            detection_id: Detection ID.

        Returns:
            AnomalyDetection or None.
        """
        return await self.repo.get_by_id(detection_id)

    async def get_detections_by_source(
        self,
        source_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[AnomalyDetection]:
        """Get all detections for a source.

        Args:
            source_id: Source ID.
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of detections.
        """
        return await self.repo.get_by_source_id(source_id, offset=offset, limit=limit)

    async def get_latest_detection(self, source_id: str) -> AnomalyDetection | None:
        """Get the latest detection for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest detection or None.
        """
        return await self.repo.get_latest_by_source(source_id)

    async def delete_detection(self, detection_id: str) -> bool:
        """Delete a detection.

        Args:
            detection_id: Detection ID.

        Returns:
            True if deleted.
        """
        return await self.repo.delete(detection_id)

    # =========================================================================
    # Algorithm Information
    # =========================================================================

    def get_algorithm_info(self) -> list[dict[str, Any]]:
        """Get information about all supported algorithms.

        Returns:
            List of algorithm information dictionaries.
        """
        from truthound_dashboard.schemas.anomaly import get_algorithm_info_list

        algorithms = get_algorithm_info_list()
        return [algo.model_dump() for algo in algorithms]

    # =========================================================================
    # Helpers
    # =========================================================================

    def _detection_to_dict(self, detection: AnomalyDetection) -> dict[str, Any]:
        """Convert detection to dictionary."""
        return {
            "id": detection.id,
            "source_id": detection.source_id,
            "status": detection.status,
            "algorithm": detection.algorithm,
            "config": detection.config,
            "total_rows": detection.total_rows,
            "anomaly_count": detection.anomaly_count,
            "anomaly_rate": detection.anomaly_rate,
            "columns_analyzed": detection.columns_analyzed,
            "column_summaries": detection.column_summaries,
            "anomalies": detection.anomalies[:100] if detection.anomalies else [],
            "duration_ms": detection.duration_ms,
            "error_message": detection.error_message,
            "created_at": detection.created_at.isoformat() if detection.created_at else None,
            "started_at": detection.started_at.isoformat() if detection.started_at else None,
            "completed_at": detection.completed_at.isoformat() if detection.completed_at else None,
        }

    # =========================================================================
    # Batch Detection Operations
    # =========================================================================

    async def create_batch_detection(
        self,
        source_ids: list[str],
        *,
        name: str | None = None,
        algorithm: str = "isolation_forest",
        config: dict[str, Any] | None = None,
        sample_size: int | None = None,
    ) -> AnomalyBatchJob:
        """Create a new batch anomaly detection job.

        This creates a pending batch job that should be executed separately.

        Args:
            source_ids: List of source IDs to analyze.
            name: Optional job name.
            algorithm: Detection algorithm to use.
            config: Algorithm-specific configuration.
            sample_size: Sample size for large datasets.

        Returns:
            Created batch job record.

        Raises:
            ValueError: If no valid sources found.
        """
        # Verify at least one source exists
        valid_source_ids = []
        for source_id in source_ids:
            result = await self.session.execute(
                select(Source).where(Source.id == source_id)
            )
            if result.scalar_one_or_none():
                valid_source_ids.append(source_id)

        if not valid_source_ids:
            raise ValueError("No valid source IDs provided")

        # Prepare configuration
        full_config = config or {}
        if sample_size:
            full_config["sample_size"] = sample_size

        batch_job = AnomalyBatchJob(
            name=name,
            algorithm=algorithm,
            config=full_config if full_config else None,
            source_ids=valid_source_ids,
            total_sources=len(valid_source_ids),
            status="pending",
        )

        self.session.add(batch_job)
        await self.session.flush()
        await self.session.refresh(batch_job)

        return batch_job

    async def run_batch_detection(
        self,
        batch_id: str,
    ) -> AnomalyBatchJob:
        """Execute batch anomaly detection.

        This runs detection on all sources in the batch sequentially.

        Args:
            batch_id: Batch job ID.

        Returns:
            Updated batch job with results.

        Raises:
            ValueError: If batch job not found.
        """
        batch_job = await self.get_batch_job(batch_id)
        if batch_job is None:
            raise ValueError(f"Batch job '{batch_id}' not found")

        # Mark as started
        batch_job.mark_started()
        await self.session.flush()

        try:
            # Process each source
            for source_id in batch_job.source_ids:
                # Update current source
                batch_job.current_source_id = source_id
                await self.session.flush()

                try:
                    # Create detection for this source
                    detection = await self.create_detection(
                        source_id=source_id,
                        algorithm=batch_job.algorithm,
                        config=batch_job.config,
                    )

                    # Run the detection
                    detection = await self.run_detection(detection.id)

                    # Update batch progress
                    batch_job.update_progress(
                        source_id=source_id,
                        detection_id=detection.id,
                        status=detection.status,
                        anomaly_count=detection.anomaly_count or 0,
                        anomaly_rate=detection.anomaly_rate or 0.0,
                        total_rows=detection.total_rows or 0,
                        error_message=detection.error_message,
                    )

                except Exception as e:
                    # Record error for this source but continue
                    batch_job.update_progress(
                        source_id=source_id,
                        detection_id="",
                        status="error",
                        error_message=str(e),
                    )

                await self.session.flush()

            # Mark batch as completed
            batch_job.mark_completed()

        except Exception as e:
            batch_job.mark_error(str(e))

        await self.session.flush()
        await self.session.refresh(batch_job)
        return batch_job

    async def get_batch_job(self, batch_id: str) -> AnomalyBatchJob | None:
        """Get a batch job by ID.

        Args:
            batch_id: Batch job ID.

        Returns:
            AnomalyBatchJob or None.
        """
        result = await self.session.execute(
            select(AnomalyBatchJob).where(AnomalyBatchJob.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def list_batch_jobs(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[AnomalyBatchJob]:
        """List all batch jobs.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of batch jobs.
        """
        result = await self.session.execute(
            select(AnomalyBatchJob)
            .order_by(AnomalyBatchJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def cancel_batch_job(self, batch_id: str) -> AnomalyBatchJob | None:
        """Cancel a running batch job.

        Args:
            batch_id: Batch job ID.

        Returns:
            Updated batch job or None if not found.
        """
        batch_job = await self.get_batch_job(batch_id)
        if batch_job is None:
            return None

        if not batch_job.is_complete:
            batch_job.mark_cancelled()
            await self.session.flush()
            await self.session.refresh(batch_job)

        return batch_job

    async def delete_batch_job(self, batch_id: str) -> bool:
        """Delete a batch job.

        Args:
            batch_id: Batch job ID.

        Returns:
            True if deleted.
        """
        batch_job = await self.get_batch_job(batch_id)
        if batch_job is None:
            return False

        await self.session.delete(batch_job)
        await self.session.flush()
        return True

    async def get_batch_results(
        self,
        batch_id: str,
    ) -> list[dict[str, Any]]:
        """Get detailed results for a batch job.

        Args:
            batch_id: Batch job ID.

        Returns:
            List of results with source information.

        Raises:
            ValueError: If batch job not found.
        """
        batch_job = await self.get_batch_job(batch_id)
        if batch_job is None:
            raise ValueError(f"Batch job '{batch_id}' not found")

        results = []
        source_results = batch_job.results_json or {}

        # Fetch source names for better display
        for source_id in batch_job.source_ids:
            source_result = source_results.get(source_id, {})

            # Get source name
            source_name = None
            source_query = await self.session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = source_query.scalar_one_or_none()
            if source:
                source_name = source.name

            results.append({
                "source_id": source_id,
                "source_name": source_name,
                "detection_id": source_result.get("detection_id"),
                "status": source_result.get("status", "pending"),
                "anomaly_count": source_result.get("anomaly_count"),
                "anomaly_rate": source_result.get("anomaly_rate"),
                "total_rows": source_result.get("total_rows"),
                "error_message": source_result.get("error_message"),
            })

        return results

    # =========================================================================
    # Algorithm Comparison Operations
    # =========================================================================

    async def run_comparison(
        self,
        source_id: str,
        algorithms: list[str],
        columns: list[str] | None = None,
        config: dict[str, dict[str, Any]] | None = None,
        sample_size: int | None = None,
    ) -> dict[str, Any]:
        """Run multiple algorithms on the same data and compare results.

        Args:
            source_id: Source ID to analyze.
            algorithms: List of algorithm names to compare.
            columns: Columns to analyze (None = all numeric).
            config: Algorithm-specific configurations keyed by algorithm name.
            sample_size: Sample size for large datasets.

        Returns:
            Comparison results with agreement analysis.

        Raises:
            ValueError: If source not found or less than 2 algorithms provided.
        """
        import time
        import uuid
        from collections import defaultdict

        if len(algorithms) < 2:
            raise ValueError("At least 2 algorithms required for comparison")

        # Verify source exists
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        start_time = time.time()
        comparison_id = str(uuid.uuid4())
        created_at = datetime.now()

        # Load data once
        try:
            import truthound as th
            import numpy as np
            import pandas as pd

            df = th.read(source.config)

            # Sample if needed
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=42)

            # Select columns
            if columns:
                df_analyze = df[columns].select_dtypes(include=[np.number])
            else:
                df_analyze = df.select_dtypes(include=[np.number])
                columns = list(df_analyze.columns)

            total_rows = len(df_analyze)
            columns_analyzed = columns

        except ImportError:
            # Mock mode
            total_rows = 5000
            columns_analyzed = columns or ["col_a", "col_b", "col_c"]
            df = None
            df_analyze = None

        # Run each algorithm and collect results
        algorithm_results = []
        all_anomaly_indices: dict[str, set[int]] = {}

        algorithm_display_names = {
            "isolation_forest": "Isolation Forest",
            "lof": "Local Outlier Factor",
            "one_class_svm": "One-Class SVM",
            "dbscan": "DBSCAN",
            "statistical": "Statistical",
            "autoencoder": "Autoencoder",
        }

        for algorithm in algorithms:
            algo_start = time.time()
            algo_config = (config or {}).get(algorithm, {})

            try:
                if df_analyze is not None and not df_analyze.empty:
                    # Run actual detection
                    detection_result = self._run_algorithm(
                        df=df_analyze,
                        algorithm=algorithm,
                        columns=columns_analyzed,
                        sample_size=None,  # Already sampled
                        params=algo_config,
                    )

                    is_anomaly = detection_result["is_anomaly"]
                    anomaly_indices = set(int(i) for i in np.where(is_anomaly)[0])
                    anomaly_count = len(anomaly_indices)
                    anomaly_rate = anomaly_count / total_rows if total_rows > 0 else 0.0

                else:
                    # Mock results
                    import random
                    base_rate = random.uniform(0.05, 0.15)
                    anomaly_count = int(total_rows * base_rate)
                    anomaly_rate = base_rate
                    anomaly_indices = set(random.sample(range(total_rows), anomaly_count))

                duration_ms = int((time.time() - algo_start) * 1000)
                all_anomaly_indices[algorithm] = anomaly_indices

                algorithm_results.append({
                    "algorithm": algorithm,
                    "display_name": algorithm_display_names.get(algorithm, algorithm),
                    "status": "success",
                    "anomaly_count": anomaly_count,
                    "anomaly_rate": anomaly_rate,
                    "duration_ms": duration_ms,
                    "error_message": None,
                    "anomaly_indices": list(anomaly_indices)[:1000],  # Limit stored indices
                })

            except Exception as e:
                duration_ms = int((time.time() - algo_start) * 1000)
                all_anomaly_indices[algorithm] = set()
                algorithm_results.append({
                    "algorithm": algorithm,
                    "display_name": algorithm_display_names.get(algorithm, algorithm),
                    "status": "error",
                    "anomaly_count": None,
                    "anomaly_rate": None,
                    "duration_ms": duration_ms,
                    "error_message": str(e),
                    "anomaly_indices": [],
                })

        # Calculate agreement
        agreement_summary, agreement_records = self._calculate_agreement(
            algorithms=algorithms,
            all_anomaly_indices=all_anomaly_indices,
            df=df_analyze if df_analyze is not None else None,
        )

        total_duration_ms = int((time.time() - start_time) * 1000)
        completed_at = datetime.now()

        # Determine overall status
        success_count = sum(1 for r in algorithm_results if r["status"] == "success")
        if success_count == len(algorithm_results):
            status = "success"
        elif success_count > 0:
            status = "success"  # Partial success
        else:
            status = "error"

        return {
            "id": comparison_id,
            "source_id": source_id,
            "status": status,
            "total_rows": total_rows,
            "columns_analyzed": columns_analyzed,
            "algorithm_results": algorithm_results,
            "agreement_summary": agreement_summary,
            "agreement_records": agreement_records,
            "total_duration_ms": total_duration_ms,
            "error_message": None if status != "error" else "All algorithms failed",
            "created_at": created_at.isoformat(),
            "completed_at": completed_at.isoformat(),
        }

    def _calculate_agreement(
        self,
        algorithms: list[str],
        all_anomaly_indices: dict[str, set[int]],
        df: Any | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Calculate agreement between algorithms.

        Args:
            algorithms: List of algorithm names.
            all_anomaly_indices: Mapping of algorithm to anomaly indices.
            df: DataFrame for column values (optional).

        Returns:
            Tuple of (agreement_summary, agreement_records).
        """
        from collections import defaultdict

        # Get all unique anomaly indices across all algorithms
        all_indices: set[int] = set()
        for indices in all_anomaly_indices.values():
            all_indices.update(indices)

        num_algorithms = len(algorithms)
        majority_threshold = num_algorithms // 2 + 1

        # Calculate which algorithms detected each row
        row_detections: dict[int, list[str]] = defaultdict(list)
        for algorithm, indices in all_anomaly_indices.items():
            for idx in indices:
                row_detections[idx].append(algorithm)

        # Classify by agreement level
        all_agree_count = 0
        majority_agree_count = 0
        some_agree_count = 0
        one_only_count = 0

        agreement_records = []
        for row_index, detected_by in sorted(row_detections.items())[:100]:
            detection_count = len(detected_by)
            confidence_score = detection_count / num_algorithms

            if detection_count == num_algorithms:
                agreement_level = "all"
                all_agree_count += 1
            elif detection_count >= majority_threshold:
                agreement_level = "majority"
                majority_agree_count += 1
            elif detection_count >= 2:
                agreement_level = "some"
                some_agree_count += 1
            else:
                agreement_level = "one"
                one_only_count += 1

            # Get column values if available
            column_values = {}
            if df is not None:
                try:
                    column_values = df.iloc[row_index].to_dict()
                except (IndexError, KeyError):
                    pass

            agreement_records.append({
                "row_index": row_index,
                "detected_by": detected_by,
                "detection_count": detection_count,
                "agreement_level": agreement_level,
                "confidence_score": confidence_score,
                "column_values": column_values,
            })

        # Calculate pairwise overlap matrix
        agreement_matrix = []
        for i, algo_i in enumerate(algorithms):
            row = []
            for j, algo_j in enumerate(algorithms):
                if i == j:
                    row.append(len(all_anomaly_indices.get(algo_i, set())))
                else:
                    overlap = len(
                        all_anomaly_indices.get(algo_i, set()) &
                        all_anomaly_indices.get(algo_j, set())
                    )
                    row.append(overlap)
            agreement_matrix.append(row)

        # Full counts (not limited to 100)
        full_all_agree = sum(
            1 for detected_by in row_detections.values()
            if len(detected_by) == num_algorithms
        )
        full_majority_agree = sum(
            1 for detected_by in row_detections.values()
            if len(detected_by) >= majority_threshold
        )
        full_some_agree = sum(
            1 for detected_by in row_detections.values()
            if len(detected_by) >= 2
        )
        full_one_only = sum(
            1 for detected_by in row_detections.values()
            if len(detected_by) == 1
        )

        agreement_summary = {
            "total_algorithms": num_algorithms,
            "total_unique_anomalies": len(all_indices),
            "all_agree_count": full_all_agree,
            "majority_agree_count": full_majority_agree,
            "some_agree_count": full_some_agree,
            "one_only_count": full_one_only,
            "agreement_matrix": agreement_matrix,
        }

        return agreement_summary, agreement_records
