# -*- coding: utf-8 -*-
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Any

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.cluster import MiniBatchKMeans
import scipy.sparse as sp


class DomainClusterer:
    """
    Per-domain incremental clustering (local & offline):
      - Text -> HashingVectorizer (1-2 grams, 2^16 features, alternate_sign=False)
      - MiniBatchKMeans with incremental updates
      - Starts with 1 cluster ("General")
      - Grows #clusters gradually when enough samples accumulated

    Stored on disk at: <models_dir>/<domain>.pkl
    Returns 'label' = SubTopicIndex (0..N-1) used to derive TopicID.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.models_dir = Path(cfg.get("models_dir", "models"))
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Fixed-size hashing avoids serialization of large vocabularies
        self.vectorizer = HashingVectorizer(
            n_features=2**16,
            alternate_sign=False,
            ngram_range=(1, 2),
            norm="l2"
        )
        self.min_emails_per_subcluster = int(cfg.get("min_emails_per_subcluster", 8))
        self.reservoir_size = 400  # keep a small buffer of recent samples per domain

    def _model_path(self, domain: str) -> Path:
        safe = (domain or "unknown.local").lower()
        return self.models_dir / f"{safe}.pkl"

    def _new_model(self, n_clusters: int):
        return {
            "kmeans": MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=128),
            "n_samples": 0,
            "reservoir": []  # list of sparse row-vectors
        }

    def _load(self, domain: str):
        p = self._model_path(domain)
        if p.exists():
            with open(p, "rb") as f:
                return pickle.load(f)
        m = self._new_model(1)  # start with one "General" cluster
        with open(p, "wb") as f:
            pickle.dump(m, f)
        return m

    def _save(self, domain: str, model):
        with open(self._model_path(domain), "wb") as f:
            pickle.dump(model, f)

    def _add_to_reservoir(self, m, X_row):
        if len(m["reservoir"]) < self.reservoir_size:
            m["reservoir"].append(X_row)
        else:
            # simple FIFO
            m["reservoir"].pop(0)
            m["reservoir"].append(X_row)

    def assign(self, domain: str, subject_canon: str, clean_body: str) -> int:
        """
        Given domain + cleaned text, returns current cluster label for subtopic index.
        """
        m = self._load(domain)
        text = f"{subject_canon}\n{clean_body}"
        X = self.vectorizer.transform([text])  # 1 x d sparse row

        # warm-up: ensure model can predict
        try:
            label = int(m["kmeans"].predict(X)[0])
        except Exception:
            # Initialize kmeans centers with the first sample
            m["kmeans"].partial_fit(X)
            label = int(m["kmeans"].predict(X)[0])

        # Update counters & reservoir
        self._add_to_reservoir(m, X)
        m["n_samples"] += 1

        # Growth policy:
        # After seeing >= min_emails_per_subcluster * current_clusters, try to grow by +1
        n_clusters = m["kmeans"].n_clusters
        if m["n_samples"] >= self.min_emails_per_subcluster * n_clusters:
            new_k = n_clusters + 1
            # Stack reservoir rows for a small 'refit'
            if m["reservoir"]:
                X_all = sp.vstack(m["reservoir"])
                new_model = self._new_model(new_k)
                new_model["kmeans"].fit(X_all)
                # reset sample counter but keep reservoir
                new_model["reservoir"] = m["reservoir"]
                new_model["n_samples"] = 0
                m = new_model

        # Persist model
        self._save(domain, m)
        return label
