#!/usr/bin/env python
"""SGN-LLAI Superevent Pipeline

Reads GW events from Kafka, clusters them by GPS time, creates superevents
in GraceDB, and publishes updates to Kafka topics.

Output topics:
- supers: Superevent + triggering G event (uploaded to GraceDB)
- skipped: Events not uploaded (lower SNR than current preferred)

Metrics are written directly to InfluxDB via shared MetricsWriter.
"""

from __future__ import annotations

import argparse
import logging

from sgn.logger import configure_sgn_logging
from sgn.sources import SignalEOS
from sgneskig.pipeline import MetricsPipeline
from sgneskig.sinks import KafkaSink
from sgneskig.sources import KafkaSource
from sgneskig.transforms import DelayBuffer, EventLatency

from sgnllai.sinks.gracedb_event_sink import GraceDBEventSink
from sgnllai.transforms.superevent_creator import SuperEventCreator


def main() -> None:
    """Run the superevent pipeline."""
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
        "--input-topic",
        default="gw-event-topic",
        help="Kafka topic to read events from (default: gw-event-topic)",
    )
    kafka_group.add_argument(
        "--supers-topic",
        default="gw-superevent-topic",
        help="Kafka topic for superevent notifications (default: gw-superevent-topic)",
    )
    kafka_group.add_argument(
        "--skipped-topic",
        default="gw-skipped-topic",
        help="Kafka topic for skipped events (default: gw-skipped-topic)",
    )
    kafka_group.add_argument(
        "--offset-reset",
        default="latest",
        choices=["earliest", "latest"],
        help="Where to start reading if no committed offset (default: latest)",
    )

    # GraceDB arguments
    gracedb_group = parser.add_argument_group("GraceDB")
    gracedb_group.add_argument(
        "--gracedb-url",
        default="https://gracedb-test.ligo.org/api/",
        help="GraceDB API URL (default: gracedb-test)",
    )
    gracedb_group.add_argument(
        "--gracedb-group",
        default="CBC",
        help="GraceDB group for event uploads (default: CBC)",
    )
    gracedb_group.add_argument(
        "--gracedb-search",
        default="AllSky",
        help="Search type for event uploads (default: AllSky)",
    )

    # Clustering arguments
    cluster_group = parser.add_argument_group("Clustering")
    cluster_group.add_argument(
        "--window-duration",
        type=float,
        default=5.0,
        help="Superevent window duration in seconds (default: 5.0 = ±2.5s)",
    )
    cluster_group.add_argument(
        "--max-event-time",
        type=int,
        default=7200,
        help="Seconds to keep events before cleanup (default: 7200)",
    )

    # Delayed upload arguments
    delayed_group = parser.add_argument_group("Delayed Upload")
    delayed_group.add_argument(
        "--enable-delayed-upload",
        action="store_true",
        help="Enable delayed upload of skipped events as standalone G events",
    )
    delayed_group.add_argument(
        "--delay-seconds",
        type=float,
        default=30.0,
        help="Seconds to delay before uploading skipped events (default: 30.0)",
    )

    # InfluxDB arguments (for metrics)
    influx_group = parser.add_argument_group("InfluxDB Metrics")
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
        help="InfluxDB database name (default: sgnllai_metrics)",
    )
    influx_group.add_argument(
        "--metrics-dry-run",
        action="store_true",
        help="Log metrics but don't write to InfluxDB",
    )

    # Export arguments
    export_group = parser.add_argument_group("Export")
    export_group.add_argument(
        "--export-dashboard",
        metavar="PATH",
        help="Export Grafana dashboard JSON to PATH and exit (don't run pipeline)",
    )
    export_group.add_argument(
        "--export-manifest",
        metavar="PATH",
        help="Export metrics manifest YAML to PATH and exit (don't run pipeline)",
    )

    # Logging arguments
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure SGN logging (respects SGNLOGLEVEL env var)
    configure_sgn_logging()
    # Set log level for sgn.sgnllai hierarchy based on --log-level arg
    logger = logging.getLogger("sgn.sgnllai")
    logger.setLevel(getattr(logging, args.log_level))

    logger.info("Creating superevent pipeline...")
    logger.info(f"  Input topic: {args.input_topic}")
    logger.info(f"  Supers topic: {args.supers_topic}")
    logger.info(f"  Skipped topic: {args.skipped_topic}")
    logger.info(f"  GraceDB URL: {args.gracedb_url}")
    logger.info(
        f"  Window duration: {args.window_duration}s (±{args.window_duration/2}s)"
    )
    if args.enable_delayed_upload:
        logger.info(f"  Delayed upload: ENABLED ({args.delay_seconds}s delay)")
        logger.info("    Skipped events → Kafka (immediate) + GraceDB (delayed)")
    else:
        logger.info("  Delayed upload: DISABLED")
        logger.info("    Skipped events → Kafka only (no GraceDB upload)")
    logger.info(
        f"  Metrics: {args.influxdb_host}:{args.influxdb_port}/{args.influxdb_db}"
        f"{' [DRY-RUN]' if args.metrics_dry_run else ''}"
    )

    # Create pipeline elements with clear names for topology visualization
    # Naming convention: "Type: Description" where Type indicates Kafka/GraceDB/etc.

    source = KafkaSource(
        name="Kafka: GW Events In",
        bootstrap_servers=args.kafka_server,
        topics=[args.input_topic],
        auto_offset_reset=args.offset_reset,
    )

    creator = SuperEventCreator(
        name="GraceDB: Superevent Creator",
        gracedb_url=args.gracedb_url,
        gracedb_group=args.gracedb_group,
        gracedb_search=args.gracedb_search,
        window_duration=args.window_duration,
        max_event_time=args.max_event_time,
        input_pad_name=args.input_topic,  # Direct from source
        supers_pad_name="supers_out",
        skipped_pad_name="skipped_out",
    )

    # Superevent latency: measures time from superevent t_0 to when we emit it
    superevent_latency = EventLatency(
        name="Measure: Superevent Latency",
        metric_name="superevent_latency",
        time_field="t_0",
        tag_field="action",  # "created" or "updated"
        description="Superevent latency (t_0 to emission)",
        panel_config={
            "width": "quarter",
            "visualizations": [
                {"type": "timeseries", "draw_style": "points", "show_points": "always"},
                {"type": "histogram", "bucket_count": 20},
            ],
        },
        input_pad_name="supers_out",
        output_pad_name=args.supers_topic,
    )

    supers_sink = KafkaSink(
        name="Kafka: Superevents Out",
        bootstrap_servers=args.kafka_server,
        topics=[args.supers_topic],
        key_field="superevent_id",
    )

    skipped_sink = KafkaSink(
        name="Kafka: Skipped Events Out",
        bootstrap_servers=args.kafka_server,
        topics={"skipped_out": args.skipped_topic},  # pad name → topic
    )

    # Delayed upload elements (only created if enabled)
    delay_buffer = None
    delayed_latency = None
    delayed_event_sink = None
    if args.enable_delayed_upload:
        delay_buffer = DelayBuffer(
            name=f"Buffer: {int(args.delay_seconds)}s Delay",
            delay_seconds=args.delay_seconds,
            input_pad_name="skipped_out",  # Match creator's skipped pad name
            output_pad_name="delayed_out",
        )
        # Delayed event latency: measures time from gpstime to when event exits buffer
        delayed_latency = EventLatency(
            name="Measure: Delayed Event Latency",
            metric_name="delayed_event_latency",
            time_field="gpstime",
            tag_field="pipeline",
            description="Delayed event latency (gpstime to post-buffer)",
            panel_config={
                "width": "quarter",
                "visualizations": [
                    {
                        "type": "timeseries",
                        "draw_style": "points",
                        "show_points": "always",
                    },
                    {"type": "histogram", "bucket_count": 20},
                ],
            },
            input_pad_name="delayed_out",
            output_pad_name="latency_out",
        )
        delayed_event_sink = GraceDBEventSink(
            name="GraceDB: Delayed G-Events",
            gracedb_url=args.gracedb_url,
            gracedb_group=args.gracedb_group,
            gracedb_search=args.gracedb_search,
            input_pad_name="latency_out",  # Match delayed_latency's output pad
        )

    # Build pipeline
    # Note: Metrics written directly via shared MetricsWriter (no metrics pads)
    # source -> creator -> superevent_latency -> supers_sink
    #                  \-> skipped_sink (always - Kafka)
    #                  \-> delay_buffer -> delayed_latency -> delayed_event_sink
    pipeline = MetricsPipeline(
        name="superevent-pipeline",
        influxdb_host=args.influxdb_host,
        influxdb_port=args.influxdb_port,
        influxdb_db=args.influxdb_db,
        grafana_influxdb_url=f"http://{args.influxdb_host}:{args.influxdb_port}",
    )

    # Insert core elements (skipped_sink always included for Kafka)
    elements = [
        source,
        creator,
        superevent_latency,
        supers_sink,
        skipped_sink,
    ]

    # Add delayed upload elements if enabled (in addition to Kafka)
    if args.enable_delayed_upload:
        elements.extend([delay_buffer, delayed_latency, delayed_event_sink])

    pipeline.insert(*elements)

    # Connect the pipeline
    pipeline.connect(source, creator)
    pipeline.connect(creator, superevent_latency)
    pipeline.connect(superevent_latency, supers_sink)

    # Skipped events always go to Kafka
    pipeline.connect(creator, skipped_sink)

    # When delayed upload enabled, also send through delay buffer to GraceDB
    if args.enable_delayed_upload:
        pipeline.connect(creator, delay_buffer)
        pipeline.connect(delay_buffer, delayed_latency)
        pipeline.connect(delayed_latency, delayed_event_sink)

    # Log discovered metrics from the pipeline
    metrics_schema = pipeline.get_metrics_schema()
    if metrics_schema:
        logger.info(f"Discovered {len(metrics_schema)} metrics from pipeline elements:")
        for metric in metrics_schema:
            logger.info(f"  - {metric.name} ({metric.metric_type})")

    # Handle export-only modes (exit without running pipeline)
    if args.export_dashboard:
        pipeline.export_grafana_dashboard(
            args.export_dashboard, "SGN-LLAI Superevent Pipeline"
        )
        logger.info(f"Dashboard exported to {args.export_dashboard}")
        return

    if args.export_manifest:
        pipeline.write_metrics_manifest(args.export_manifest)
        logger.info(f"Manifest exported to {args.export_manifest}")
        return

    logger.info("Starting pipeline (Ctrl+C to stop)...")
    with SignalEOS():
        pipeline.run()

    logger.info("Pipeline has shut down cleanly.")


if __name__ == "__main__":
    main()
