"""Human signals: the atomic unit HUMAN PORTAL is built on.

Every adapter normalizes its source into HumanSignal records (who, what,
sentiment, source, timestamp, region — per PROJECT.md), keeping the raw
payload alongside so signals can be re-derived when this schema evolves.
"""

from app.signals.adapter import SignalAdapter, run_adapter
from app.signals.schema import HumanSignal, RawPayload, SignalRegion

__all__ = ["HumanSignal", "RawPayload", "SignalRegion", "SignalAdapter", "run_adapter"]
