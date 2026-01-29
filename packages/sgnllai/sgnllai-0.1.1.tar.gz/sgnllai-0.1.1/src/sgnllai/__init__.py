"""SGN-LLAI: LIGO-specific superevent pipeline with GraceDB integration."""

# Re-export from sgn-skig for convenience
from sgneskig.pipeline import MetricsPipeline
from sgneskig.sinks import KafkaSink
from sgneskig.sources import KafkaSource

# LIGO-specific transforms
from sgnllai.transforms.superevent_creator import SuperEventCreator

try:
    from sgnllai._version import __version__
except ModuleNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "KafkaSource",
    "SuperEventCreator",
    "KafkaSink",
    "MetricsPipeline",
    "__version__",
]
