#!/usr/bin/env python
"""SGN-LLAI Mock Event Publisher

Publishes realistic mock GW events to Kafka using MockGWEventSource from sgnligo.
Events include proper coinc XML, realistic SNR/timing, and pipeline latencies.

Metrics tracked:
- publish_latency: Time between event generation and Kafka publish (per pipeline)
"""

from __future__ import annotations

import argparse
import logging

from sgn.sources import SignalEOS
from sgneskig.pipeline import MetricsPipeline
from sgneskig.sinks import KafkaSink
from sgneskig.transforms import EventLatency
from sgnligo.sources import MockGWEventSource


def main() -> None:
    """Run the mock event publisher pipeline."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Kafka arguments
    kafka_group = parser.add_argument_group("Kafka")
    kafka_group.add_argument(
        "--kafka-server",
        default="localhost:9092",
        help="Kafka bootstrap server (default: localhost:9092)",
    )
    kafka_group.add_argument(
        "--topic",
        default="event-topic",
        help="Kafka topic to publish events to (default: event-topic)",
    )

    # Event generation arguments
    event_group = parser.add_argument_group("Event Generation")
    event_group.add_argument(
        "--event-cadence",
        type=float,
        default=20.0,
        help="Seconds between coalescence times (default: 20.0)",
    )
    event_group.add_argument(
        "--ifos",
        default="H1,L1,V1",
        help="Comma-separated list of detectors (default: H1,L1,V1)",
    )

    # InfluxDB arguments
    influx_group = parser.add_argument_group("InfluxDB (metrics)")
    influx_group.add_argument(
        "--influxdb-host",
        default="localhost",
        help="InfluxDB host (default: localhost)",
    )
    influx_group.add_argument(
        "--influxdb-port",
        type=int,
        default=8086,
        help="InfluxDB port (default: 8086)",
    )
    influx_group.add_argument(
        "--influxdb-db",
        default="sgnllai_metrics",
        help="InfluxDB database (default: sgnllai_metrics)",
    )
    influx_group.add_argument(
        "--metrics-dry-run",
        action="store_true",
        help="Log metrics but don't write to InfluxDB",
    )

    # Grafana export
    parser.add_argument(
        "--export-dashboard",
        metavar="PATH",
        help="Export Grafana dashboard JSON to PATH and exit (don't run pipeline)",
    )

    # Logging arguments
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from MockGWEventSource",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Parse IFOs
    ifos = [ifo.strip() for ifo in args.ifos.split(",")]

    logger.info("Creating mock event publisher pipeline...")
    logger.info(f"  Kafka server: {args.kafka_server}")
    logger.info(f"  Output topic: {args.topic}")
    logger.info(f"  Event cadence: {args.event_cadence}s")
    logger.info(f"  Detectors: {ifos}")
    logger.info(
        f"  Metrics: {args.influxdb_host}:{args.influxdb_port}/{args.influxdb_db}"
        f"{' [DRY-RUN]' if args.metrics_dry_run else ''}"
    )

    # Create MetricsPipeline for dashboard export support
    pipeline = MetricsPipeline(
        name="mock-publisher-pipeline",
        influxdb_host=args.influxdb_host,
        influxdb_port=args.influxdb_port,
        influxdb_db=args.influxdb_db,
    )

    # Create MockGWEventSource
    source = MockGWEventSource(
        name="Mock GW Events",
        event_cadence=args.event_cadence,
        ifos=ifos,
        verbose=args.verbose,
    )

    # Get the pipeline names from the source
    pipeline_names = source.source_pad_names
    logger.info(f"  Pipelines: {pipeline_names}")

    # Create EventLatency, KafkaSink, and MetricsSink for each source pad
    # Flow: source --[pipeline]--> latency --[topic]--> sink
    #                                 |
    #                            [metrics]--> metrics_sink
    #
    # By setting input/output pad names to match upstream/downstream,
    # connect() can use implicit linking (no link_map needed).
    # connect() also auto-inserts elements, so no insert() calls needed.
    latency_panel_config = {
        "visualizations": [
            {"type": "timeseries", "draw_style": "points", "show_points": "always"},
            {"type": "histogram", "bucket_count": 20},
        ]
    }
    for pipeline_name in pipeline_names:
        latency = EventLatency(
            name=f"{pipeline_name}: Latency",
            metric_name="publish_latency",
            time_field="gpstime",
            tag_field="pipeline",
            input_pad_name=pipeline_name,  # Match source pad name
            output_pad_name=args.topic,  # Match sink pad name
            panel_config=latency_panel_config,
        )
        sink = KafkaSink(
            name=f"{pipeline_name}: Kafka",
            bootstrap_servers=args.kafka_server,
            topics=[args.topic],
        )

        # Connect with implicit pad matching (no link_map needed)
        # Metrics are written directly via shared MetricsWriter (no metrics pads needed)
        pipeline.connect(source, latency)
        pipeline.connect(latency, sink)

    if args.export_dashboard:
        pipeline.export_grafana_dashboard(
            args.export_dashboard, "SGN-LLAI Mock Publisher"
        )
        logger.info(f"Dashboard exported to {args.export_dashboard}")
    else:
        logger.info("Starting publisher pipeline (Ctrl+C to stop)...")
        with SignalEOS():
            pipeline.run()
        logger.info("Publisher pipeline has shut down cleanly.")


if __name__ == "__main__":
    main()
