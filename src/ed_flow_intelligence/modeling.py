"""Interpretable public and hybrid forecasting models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ed_flow_intelligence.forecasting import public_pressure_index


class ModelRegistryEntry(BaseModel):
    """Metadata for a model output shown in the app."""

    model_name: str
    target: str
    features: list[str]
    training_window: str
    validation_window: str
    metrics: dict[str, float] = Field(default_factory=dict)
    limitations: str
    lineage: str
    capability_tier: str


@dataclass
class ForecastBundle:
    """Forecast, validation, registry, and driver output."""

    hourly: pd.DataFrame
    daily: pd.DataFrame
    validation: pd.DataFrame
    registry: pd.DataFrame
    drivers: pd.DataFrame


FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "estimated_wait_mins",
    "environmental_stress_index",
    "travel_friction_index",
    "weather_alert_count",
    "pediatric_pressure_index",
    "school_in_session",
]


def build_public_feature_matrix(public_data: dict[str, pd.DataFrame], facility: str) -> pd.DataFrame:
    """Build a site-hour feature matrix from public/synthetic context."""

    wait = public_data.get("public_wait_times", pd.DataFrame()).copy()
    if wait.empty:
        return pd.DataFrame()
    wait = wait[wait["facility"] == facility].copy()
    if wait.empty:
        return pd.DataFrame()
    wait["timestamp"] = pd.to_datetime(wait["posted_timestamp"], errors="coerce").dt.floor("h")
    wait = wait.dropna(subset=["timestamp"])
    env = _site_time(public_data.get("environmental_stress", pd.DataFrame()), facility, "timestamp")
    travel = _site_time(public_data.get("travel_friction", pd.DataFrame()), facility, "timestamp")
    facilities = public_data.get("facility_reference", pd.DataFrame())
    zone = facilities.loc[facilities["facility"] == facility, "zone"].iloc[0] if not facilities.empty and facility in facilities["facility"].values else "Edmonton"
    respiratory = public_data.get("respiratory_surveillance", pd.DataFrame()).copy()
    if not respiratory.empty:
        respiratory = respiratory[respiratory["zone"] == zone].copy()
        respiratory = respiratory.sort_values("week_start").groupby("week_start", as_index=False)["pediatric_pressure_index"].mean()
    frame = wait[["facility", "zone", "city", "timestamp", "estimated_wait_mins"]].copy()
    frame = frame.merge(env, on=["facility", "timestamp"], how="left")
    frame = frame.merge(travel, on=["facility", "timestamp"], how="left")
    frame["week_start"] = frame["timestamp"].dt.to_period("W").dt.start_time
    if not respiratory.empty:
        frame = frame.merge(respiratory, on="week_start", how="left")
    calendar = public_data.get("calendar_context", pd.DataFrame()).copy()
    if not calendar.empty:
        calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce").dt.normalize()
        frame["date"] = frame["timestamp"].dt.normalize()
        frame = frame.merge(calendar[["date", "school_in_session"]], on="date", how="left")
    frame["hour"] = frame["timestamp"].dt.hour
    frame["day_of_week"] = frame["timestamp"].dt.dayofweek
    frame["is_weekend"] = frame["day_of_week"].isin([5, 6]).astype(int)
    for column in FEATURE_COLUMNS:
        if column not in frame:
            frame[column] = 0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(frame[column].median() if frame[column].notna().any() else 0)
    frame["target_external_pressure"] = _normalise(frame["estimated_wait_mins"]) * 0.5
    frame["target_external_pressure"] += frame["environmental_stress_index"].clip(0, 1) * 0.18
    frame["target_external_pressure"] += frame["travel_friction_index"].clip(0, 1) * 0.14
    frame["target_external_pressure"] += frame["pediatric_pressure_index"].clip(0, 1) * 0.18
    frame["target_external_pressure"] = frame["target_external_pressure"].clip(0, 1)
    return frame.sort_values("timestamp").reset_index(drop=True)


def forecast_external_pressure(
    public_data: dict[str, pd.DataFrame],
    facility: str,
    horizon_hours: int = 72,
    horizon_days: int = 14,
) -> ForecastBundle:
    """Forecast public external pressure with baselines, ML, ensemble, intervals, and validation."""

    features = build_public_feature_matrix(public_data, facility)
    if features.empty:
        empty = pd.DataFrame()
        return ForecastBundle(empty, empty, empty, empty, empty)
    train, holdout = _time_holdout(features)
    x_train = train[FEATURE_COLUMNS]
    y_train = train["target_external_pressure"]
    x_holdout = holdout[FEATURE_COLUMNS] if not holdout.empty else x_train.tail(min(12, len(x_train)))
    y_holdout = holdout["target_external_pressure"] if not holdout.empty else y_train.tail(min(12, len(y_train)))
    ridge = Ridge(alpha=1.0).fit(x_train, y_train)
    forest = RandomForestRegressor(n_estimators=80, min_samples_leaf=3, random_state=17).fit(x_train, y_train)
    validation = _validation_table(train, x_holdout, y_holdout, ridge, forest)
    future = _future_features(features, public_data, facility, horizon_hours)
    seasonal = _seasonal_naive(features, horizon_hours)
    moving = np.repeat(float(features["target_external_pressure"].tail(12).mean()), len(future))
    ridge_pred = ridge.predict(future[FEATURE_COLUMNS]).clip(0, 1)
    forest_pred = forest.predict(future[FEATURE_COLUMNS]).clip(0, 1)
    ensemble = (0.2 * seasonal + 0.2 * moving + 0.3 * ridge_pred + 0.3 * forest_pred).clip(0, 1)
    residual = _ensemble_residual(validation)
    hourly = future[["timestamp", "hour", "day_of_week", "estimated_wait_mins", "environmental_stress_index", "travel_friction_index", "pediatric_pressure_index"]].copy()
    hourly["model_seasonal_naive"] = seasonal
    hourly["model_moving_average"] = moving
    hourly["model_regression"] = ridge_pred
    hourly["model_random_forest"] = forest_pred
    hourly["p50_pressure"] = ensemble
    hourly["p10_pressure"] = (ensemble - residual * 1.28).clip(0, 1)
    hourly["p90_pressure"] = (ensemble + residual * 1.28).clip(0, 1)
    hourly["confidence"] = np.where(residual < 0.08, "higher", np.where(residual < 0.15, "moderate", "wide"))
    hourly["target"] = "external_pressure_index"
    hourly["lineage"] = "HYBRID_OPEN_SYNTHETIC"
    daily = _daily_from_hourly(hourly, horizon_days)
    drivers = feature_driver_table(ridge, forest, future)
    registry = model_registry_frame(features, validation, FEATURE_COLUMNS)
    return ForecastBundle(hourly=hourly, daily=daily, validation=validation, registry=registry, drivers=drivers)


def forecast_internal_targets(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str) -> pd.DataFrame:
    """Produce internal-ready target nowcasts using synthetic TB_ED_VISITS rows in local mode."""

    site = visits[visits["INSTITUTION_NAME"] == facility].copy() if "INSTITUTION_NAME" in visits else visits.copy()
    pressure = public_pressure_index(public_data)
    pressure_value = float(pressure.loc[pressure["facility"] == facility, "public_pressure_index"].iloc[0]) if not pressure.empty and facility in pressure["facility"].values else 0.35
    if site.empty:
        return pd.DataFrame()
    los = pd.to_numeric(site["ED_LOS_HRS"], errors="coerce")
    pia = pd.to_numeric(site["ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS"], errors="coerce")
    boarding = pd.to_numeric(site["ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS"], errors="coerce")
    admitted = site["DISPOSITION_PERFORMANCE_REPORT"].eq("Admitted") if "DISPOSITION_PERFORMANCE_REPORT" in site else site["DISPOSITION_GROUP"].eq("Admitted")
    lwbs = site["DISPOSITION_GROUP"].eq("LWBS")
    pediatric = site["PATIENT_AGE_GROUP"].isin(["Newborn", "Neonate", "Paediatric"])
    rows = [
        ("arrivals", len(site), len(site) * (1 + pressure_value * 0.2), "HYBRID_OPEN_INTERNAL_READY"),
        ("pediatric_arrivals", pediatric.sum(), pediatric.sum() * (1 + pressure_value * 0.28), "HYBRID_OPEN_INTERNAL_READY"),
        ("admission_probability", admitted.mean(), min(admitted.mean() + pressure_value * 0.025, 1), "SECURE_INTERNAL_READY_SCHEMA"),
        ("lwbs_risk", lwbs.mean(), min(lwbs.mean() + pressure_value * 0.055, 1), "SECURE_INTERNAL_READY_SCHEMA"),
        ("ed_los_p50_hrs", los.median(), los.median() * (1 + pressure_value * 0.08), "SECURE_INTERNAL_READY_SCHEMA"),
        ("ed_los_p90_hrs", los.quantile(0.9), los.quantile(0.9) * (1 + pressure_value * 0.12), "SECURE_INTERNAL_READY_SCHEMA"),
        ("pia_p50_hrs", pia.median(), pia.median() * (1 + pressure_value * 0.18), "SECURE_INTERNAL_READY_SCHEMA"),
        ("pia_p90_hrs", pia.quantile(0.9), pia.quantile(0.9) * (1 + pressure_value * 0.24), "SECURE_INTERNAL_READY_SCHEMA"),
        ("boarding_risk", boarding.notna().mean(), min(boarding.notna().mean() + pressure_value * 0.04, 1), "SECURE_INTERNAL_READY_SCHEMA"),
    ]
    out = pd.DataFrame(rows, columns=["target", "baseline", "pressure_adjusted_prediction", "lineage"])
    out["uncertainty"] = np.where(out["target"].str.contains("p90|boarding|lwbs"), "wide", "moderate")
    out["validation_status"] = "synthetic local demo; Snowflake holdout validation required"
    return out


def rolling_origin_backtest(feature_frame: pd.DataFrame, min_train_size: int = 18) -> pd.DataFrame:
    """Run a compact rolling-origin backtest for the ensemble approach."""

    rows = []
    if len(feature_frame) < min_train_size + 6:
        return pd.DataFrame(rows)
    for cutoff in range(min_train_size, len(feature_frame) - 1, 4):
        train = feature_frame.iloc[:cutoff]
        test = feature_frame.iloc[[cutoff]]
        ridge = Ridge(alpha=1.0).fit(train[FEATURE_COLUMNS], train["target_external_pressure"])
        forest = RandomForestRegressor(n_estimators=40, min_samples_leaf=3, random_state=17).fit(train[FEATURE_COLUMNS], train["target_external_pressure"])
        seasonal = float(train["target_external_pressure"].iloc[-24]) if len(train) >= 24 else float(train["target_external_pressure"].iloc[-1])
        moving = float(train["target_external_pressure"].tail(12).mean())
        pred = 0.2 * seasonal + 0.2 * moving + 0.3 * float(ridge.predict(test[FEATURE_COLUMNS])[0]) + 0.3 * float(forest.predict(test[FEATURE_COLUMNS])[0])
        rows.append(
            {
                "origin_timestamp": train["timestamp"].iloc[-1],
                "target_timestamp": test["timestamp"].iloc[0],
                "actual": float(test["target_external_pressure"].iloc[0]),
                "prediction": float(np.clip(pred, 0, 1)),
                "absolute_error": abs(float(test["target_external_pressure"].iloc[0]) - float(np.clip(pred, 0, 1))),
            }
        )
    return pd.DataFrame(rows)


def _site_time(frame: pd.DataFrame, facility: str, timestamp_col: str) -> pd.DataFrame:
    if frame.empty or "facility" not in frame:
        return pd.DataFrame({"facility": [], "timestamp": []})
    out = frame[frame["facility"] == facility].copy()
    if out.empty:
        return pd.DataFrame({"facility": [], "timestamp": []})
    out["timestamp"] = pd.to_datetime(out[timestamp_col], errors="coerce").dt.floor("h")
    keep = ["facility", "timestamp"] + [c for c in ["environmental_stress_index", "travel_friction_index", "weather_alert_count", "road_incidents", "aqhi"] if c in out]
    return out[keep].drop_duplicates(["facility", "timestamp"])


def _normalise(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(series.median() if series.notna().any() else 0)
    span = max(float(values.max() - values.min()), 1e-9)
    return (values - float(values.min())) / span


def _time_holdout(frame: pd.DataFrame, holdout_fraction: float = 0.25) -> tuple[pd.DataFrame, pd.DataFrame]:
    split = max(int(len(frame) * (1 - holdout_fraction)), min(len(frame) - 1, 12))
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _validation_table(train: pd.DataFrame, x_holdout: pd.DataFrame, y_holdout: pd.Series, ridge: Ridge, forest: RandomForestRegressor) -> pd.DataFrame:
    seasonal = np.repeat(float(train["target_external_pressure"].iloc[-24] if len(train) >= 24 else train["target_external_pressure"].iloc[-1]), len(y_holdout))
    moving = np.repeat(float(train["target_external_pressure"].tail(12).mean()), len(y_holdout))
    reg = ridge.predict(x_holdout).clip(0, 1)
    rf = forest.predict(x_holdout).clip(0, 1)
    ensemble = (0.2 * seasonal + 0.2 * moving + 0.3 * reg + 0.3 * rf).clip(0, 1)
    rows = []
    for name, pred in [
        ("seasonal_naive", seasonal),
        ("moving_average", moving),
        ("regression_ridge", reg),
        ("random_forest", rf),
        ("ensemble", ensemble),
    ]:
        rows.append(_metric_row(name, y_holdout.to_numpy(), np.asarray(pred)))
    return pd.DataFrame(rows)


def _metric_row(model: str, actual: np.ndarray, pred: np.ndarray) -> dict[str, float | str]:
    mae = float(mean_absolute_error(actual, pred))
    rmse = float(np.sqrt(mean_squared_error(actual, pred)))
    denominator = max(float(np.abs(actual).sum()), 1e-9)
    wape = float(np.abs(actual - pred).sum() / denominator)
    naive_scale = max(float(np.abs(np.diff(actual)).mean()) if len(actual) > 1 else mae, 1e-9)
    interval_lower = np.clip(pred - mae * 1.28, 0, 1)
    interval_upper = np.clip(pred + mae * 1.28, 0, 1)
    coverage = float(((actual >= interval_lower) & (actual <= interval_upper)).mean())
    surge_threshold = float(np.quantile(actual, 0.8)) if len(actual) else 1
    surge_recall = float(((pred >= surge_threshold) & (actual >= surge_threshold)).sum() / max((actual >= surge_threshold).sum(), 1))
    return {
        "model": model,
        "mae": mae,
        "rmse": rmse,
        "wape": wape,
        "mase": mae / naive_scale,
        "interval_coverage": coverage,
        "top_decile_surge_recall": surge_recall,
    }


def _ensemble_residual(validation: pd.DataFrame) -> float:
    row = validation[validation["model"] == "ensemble"]
    if row.empty:
        return 0.12
    return float(np.clip(row["mae"].iloc[0], 0.05, 0.25))


def _future_features(features: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str, horizon_hours: int) -> pd.DataFrame:
    last_ts = pd.to_datetime(features["timestamp"]).max()
    future_ts = pd.date_range(last_ts + pd.Timedelta(hours=1), periods=horizon_hours, freq="h")
    env = _site_time(public_data.get("environmental_stress", pd.DataFrame()), facility, "timestamp")
    travel = _site_time(public_data.get("travel_friction", pd.DataFrame()), facility, "timestamp")
    future = pd.DataFrame({"timestamp": future_ts, "facility": facility})
    future = future.merge(env, on=["facility", "timestamp"], how="left")
    future = future.merge(travel, on=["facility", "timestamp"], how="left")
    recent = features.tail(24)
    future["estimated_wait_mins"] = np.resize(recent["estimated_wait_mins"].to_numpy(), len(future))
    future["pediatric_pressure_index"] = float(features["pediatric_pressure_index"].tail(12).mean())
    future["school_in_session"] = (future["timestamp"].dt.dayofweek < 5).astype(int)
    future["hour"] = future["timestamp"].dt.hour
    future["day_of_week"] = future["timestamp"].dt.dayofweek
    future["is_weekend"] = future["day_of_week"].isin([5, 6]).astype(int)
    for column in FEATURE_COLUMNS:
        if column not in future:
            future[column] = float(features[column].tail(24).mean()) if column in features else 0
        future[column] = pd.to_numeric(future[column], errors="coerce").fillna(float(features[column].tail(24).mean()) if column in features else 0)
    return future


def _seasonal_naive(features: pd.DataFrame, horizon_hours: int) -> np.ndarray:
    values = features["target_external_pressure"].to_numpy()
    if len(values) >= 24:
        base = values[-24:]
    else:
        base = values
    return np.resize(base, horizon_hours).clip(0, 1)


def _daily_from_hourly(hourly: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    out = hourly.copy()
    out["forecast_date"] = pd.to_datetime(out["timestamp"]).dt.date
    daily = out.groupby("forecast_date", as_index=False).agg(
        p10_pressure=("p10_pressure", "mean"),
        p50_pressure=("p50_pressure", "mean"),
        p90_pressure=("p90_pressure", "mean"),
        peak_p50_pressure=("p50_pressure", "max"),
        confidence=("confidence", lambda values: values.mode().iloc[0] if not values.mode().empty else "moderate"),
    )
    return daily.head(horizon_days)


def feature_driver_table(ridge: Ridge, forest: RandomForestRegressor, future: pd.DataFrame) -> pd.DataFrame:
    """Summarize model feature contributions for app display."""

    coef = np.abs(ridge.coef_)
    rf = getattr(forest, "feature_importances_", np.zeros(len(FEATURE_COLUMNS)))
    rows = []
    for feature, c, imp in zip(FEATURE_COLUMNS, coef, rf):
        recent_value = float(pd.to_numeric(future[feature], errors="coerce").tail(24).mean())
        rows.append(
            {
                "feature": feature,
                "regression_weight_abs": float(c),
                "tree_importance": float(imp),
                "recent_value": recent_value,
                "directional_interpretation": _driver_interpretation(feature, recent_value),
            }
        )
    out = pd.DataFrame(rows)
    out["combined_driver_score"] = _normalise(out["regression_weight_abs"]) * 0.45 + _normalise(out["tree_importance"]) * 0.55
    return out.sort_values("combined_driver_score", ascending=False).reset_index(drop=True)


def _driver_interpretation(feature: str, value: float) -> str:
    mapping = {
        "estimated_wait_mins": "posted wait-time fallback is the strongest public pressure proxy",
        "environmental_stress_index": "weather, heat, smoke, AQHI, or alerts may be adding external stress",
        "travel_friction_index": "road, transit, event, or weather access friction may shift arrival timing",
        "pediatric_pressure_index": "respiratory context may lift pediatric arrivals and acuity mix",
        "school_in_session": "school calendar can shape pediatric respiratory spread and injury timing",
        "hour": "time-of-day demand shape",
        "day_of_week": "day-of-week demand shape",
        "is_weekend": "weekend/holiday-like access pattern",
        "weather_alert_count": "weather alerts may affect access and respiratory/heat/cold risk",
    }
    return mapping.get(feature, f"current feature value {value:.2f}")


def model_registry_frame(features: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Return model registry rows with validation context."""

    validation_map = {row["model"]: row for _, row in validation.iterrows()}
    entries = []
    for model_name, tier, limitations in [
        ("seasonal_naive", "public prototype capability", "Baseline repeats recent seasonality; useful as a humility check."),
        ("moving_average", "public prototype capability", "Smooths recent pressure; slow to detect shocks."),
        ("regression_ridge", "public prototype capability", "Interpretable linear approximation on synthetic/public fallback features."),
        ("random_forest", "public prototype capability", "Captures nonlinear feature interactions but remains synthetic-demo only locally."),
        ("ensemble", "public prototype capability", "Combines baselines and richer models; requires real backtesting before operations use."),
    ]:
        row = validation_map.get(model_name, {})
        entries.append(
            ModelRegistryEntry(
                model_name=model_name,
                target="external_pressure_index",
                features=feature_columns,
                training_window=f"{features['timestamp'].min()} to {features['timestamp'].max()}",
                validation_window="last chronological holdout slice",
                metrics={k: float(row[k]) for k in ["mae", "rmse", "wape", "mase", "interval_coverage", "top_decile_surge_recall"] if k in row},
                limitations=limitations,
                lineage="HYBRID_OPEN_SYNTHETIC",
                capability_tier=tier,
            ).model_dump(mode="json")
        )
    return pd.DataFrame(entries)
