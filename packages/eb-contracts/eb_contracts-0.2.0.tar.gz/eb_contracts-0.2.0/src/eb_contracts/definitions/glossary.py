"""
Canonical glossary for forecasting and panel-based evaluation.

This module defines core vocabulary used across contract schemas and evaluation
workflows. The definitions here are intentionally **implementation- and industry-agnostic**:

- They describe general data science / forecasting concepts.
- They do not encode enforcement rules or business logic.
- They avoid domain-specific language unless unavoidable.

These definitions exist to reduce semantic drift across codebases, repositories,
and contributors.
"""

from __future__ import annotations

ENTITY = (
    "A unit of analysis for which observations are recorded and evaluated. Examples include a site "
    "or location, a customer segment, a product, a device, or a composite such as site x product. "
    "An entity represents a real-world object or logical grouping at which outcomes are measured."
)

ENTITY_ID = (
    "An identifier representing an entity at a given grain. The identifier may be a natural key "
    "(e.g., site_id, product_id) or a composite encoding of multiple dimensions "
    "(e.g., site_id|product_id). The specific encoding strategy is an integration concern; consumers "
    "typically require only consistency and uniqueness."
)

GRAIN = (
    "The set of non-temporal dimensions that uniquely identify an entity in a dataset. Grain excludes "
    "time; temporal resolution is modeled separately via interval fields. For example, in site x product "
    "forecasts at 30-minute resolution, the grain is site x product, while 30 minutes describes the "
    "interval frequency."
)

INTERVAL = (
    "A target time window to which an observation refers. In panel datasets, intervals are commonly "
    "represented by a start timestamp (and optionally an end timestamp). Each observation corresponds "
    "to a specific entity and interval."
)

FREQUENCY = (
    "The regular spacing of intervals in a panel dataset (e.g., 15-minute, 30-minute, hourly, daily). "
    "Frequency describes temporal resolution and is often treated as metadata rather than an explicit "
    "column."
)

FORECAST = (
    "A prediction of an outcome associated with a future or target interval. Forecasts may be expressed "
    "in different representations depending on the modeling approach and evaluation needs."
)

POINT_FORECAST = (
    "A forecast representation that provides a single predicted value for each entity x interval "
    "observation."
)

QUANTILE_FORECAST = (
    "A forecast representation that provides predicted values at one or more quantile levels for each "
    "entity x interval observation. Quantile forecasts characterize uncertainty by describing the "
    "distribution of possible outcomes."
)

ISSUED_AT = (
    "A timestamp indicating when a forecast was generated. Issued time is distinct from the target "
    "interval timestamps and is important in multi-horizon and real-time forecasting contexts."
)

HORIZON = (
    "A measure of lead time between forecast issuance and the target interval. Horizon may be expressed "
    "as a number of steps ahead or derived from issued-at and interval timestamps."
)

ACTUAL = (
    "The realized (observed) outcome associated with a target interval. Depending on context, actuals "
    "may represent demand, volume, utilization, incidents, transactions, delivered quantity, or another "
    "measured value. The semantic meaning of actuals should be explicit in any evaluation."
)

UNITS = (
    "The measurement units associated with forecasted or observed values (e.g., units, dollars, minutes, "
    "events). Units are semantic information; mismatched units can yield numerically valid but "
    "substantively incorrect results."
)

COST_RATIO_R = (
    "A parameter representing asymmetric cost or loss weighting between different types of forecast error "
    "(e.g., under- versus over-forecasting). Such parameters encode domain-specific preferences or "
    "operational tradeoffs and should be treated as semantic inputs, not arbitrary tuning knobs."
)

TAU = (
    "A threshold parameter commonly used in service-level or risk-sensitive evaluation settings. "
    "Depending on context, tau may represent a service-level threshold, a target quantile level, or an "
    "operational cutoff. Its interpretation must be explicit wherever it is applied."
)

READINESS = (
    "A concept describing the suitability of a forecasting system or set of forecasts for operational use, "
    "beyond raw predictive accuracy. Readiness may incorporate cost sensitivity, service-level behavior, "
    "robustness, and other practical considerations."
)
