"""Shared portfolio-level recurrence and ratio stats for dataset, features and rules."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

RECURRENCE_THRESHOLD = 8


@dataclass(frozen=True)
class PortfolioStats:
    provider_counts: pd.Series
    beneficiary_counts: pd.Series

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> PortfolioStats:
        provider_counts = (
            df["id_proveedor"].astype(str).value_counts()
            if "id_proveedor" in df.columns
            else pd.Series(dtype=int)
        )
        beneficiary_counts = (
            df["beneficiario"].astype(str).value_counts()
            if "beneficiario" in df.columns
            else pd.Series(dtype=int)
        )
        return cls(provider_counts=provider_counts, beneficiary_counts=beneficiary_counts)

    def monto_ratio(self, df: pd.DataFrame) -> pd.Series:
        return df["monto_reclamado"].astype(float) / df["suma_asegurada"].astype(float).clip(lower=1)

    def proveedor_recurrencia(self, df: pd.DataFrame) -> pd.Series:
        if "id_proveedor" not in df.columns:
            return pd.Series(0, index=df.index, dtype=int)
        return df["id_proveedor"].astype(str).map(self.provider_counts).fillna(0).astype(int)

    def beneficiario_recurrencia(self, df: pd.DataFrame) -> pd.Series:
        if "beneficiario" not in df.columns:
            return pd.Series(0, index=df.index, dtype=int)
        return df["beneficiario"].astype(str).map(self.beneficiary_counts).fillna(0).astype(int)

    def enrich_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recurrence counts and boolean flags when not already present."""
        out = df.copy()
        if "proveedor_recurrencia_count" not in out.columns:
            out["proveedor_recurrencia_count"] = self.proveedor_recurrencia(out).astype(float)
        if "beneficiario_recurrencia_count" not in out.columns:
            out["beneficiario_recurrencia_count"] = self.beneficiario_recurrencia(out).astype(float)
        if "proveedor_recurrente" not in out.columns:
            out["proveedor_recurrente"] = out["proveedor_recurrencia_count"] >= RECURRENCE_THRESHOLD
        if "beneficiario_recurrente" not in out.columns:
            out["beneficiario_recurrente"] = out["beneficiario_recurrencia_count"] >= RECURRENCE_THRESHOLD
        return out
