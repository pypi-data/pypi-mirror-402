"""LIGO-specific sinks for SGN pipelines."""

from sgnllai.sinks.gracedb_event_sink import GraceDBEventSink
from sgnllai.sinks.gracedb_sink import GraceDBSink

__all__ = ["GraceDBEventSink", "GraceDBSink"]
