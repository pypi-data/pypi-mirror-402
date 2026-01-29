#!/usr/bin/env python
"""SGN-LLAI Bayestar Pipeline

Reads superevent notifications from Kafka, runs Bayestar sky localization
in parallel, generates PNG plots, and uploads results to GraceDB.

Architecture (fan-out pattern):

                         ┌──▶ Latency ──▶ GraceDBSink (FITS)
  Kafka → Distributor → [Bayestar] ──┤
                         └──▶ Plotter ──▶ GraceDBSink (PNG)

  Each worker chain uses fan-out: Bayestar output goes to both
  the latency tracker (then FITS sink) and the Plotter (then PNG sink).
  The latency tracker measures time from superevent t_0 to skymap ready.
"""

from __future__ import annotations

import argparse
import logging

from sgn.groups import select
from sgn.logger import configure_sgn_logging
from sgn.sources import SignalEOS
from sgn.subprocess import Parallelize
from sgneskig.pipeline import MetricsPipeline
from sgneskig.sources import KafkaSource
from sgneskig.transforms import EventLatency, RoundRobinDistributor

from sgnllai.sinks.gracedb_sink import GraceDBSink
from sgnllai.transforms.bayestar_processor import BayestarProcessor
from sgnllai.transforms.skymap_plotter import SkymapPlotter


def main() -> None:
    """Run the Bayestar sky localization pipeline."""
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
        default="gw-superevent-topic",
        help="Kafka topic to read superevents from (default: gw-superevent-topic)",
    )
    kafka_group.add_argument(
        "--offset-reset",
        default="latest",
        choices=["earliest", "latest"],
        help="Where to start reading if no committed offset (default: latest)",
    )

    # Bayestar arguments
    bayestar_group = parser.add_argument_group("Bayestar")
    bayestar_group.add_argument(
        "--num-workers",
        type=int,
        default=4,
        help="Number of parallel Bayestar workers (default: 4)",
    )
    bayestar_group.add_argument(
        "--f-low",
        type=float,
        default=30.0,
        help="Low frequency cutoff in Hz (default: 30.0)",
    )
    bayestar_group.add_argument(
        "--waveform",
        default="IMRPhenomD",
        help="Waveform approximant (default: IMRPhenomD)",
    )
    bayestar_group.add_argument(
        "--output-dir",
        default="/tmp/bayestar",  # noqa: S108
        help="Directory for temporary FITS files (default: /tmp/bayestar)",
    )

    # GraceDB arguments
    gracedb_group = parser.add_argument_group("GraceDB")
    gracedb_group.add_argument(
        "--gracedb-url",
        default="https://gracedb-test.ligo.org/api/",
        help="GraceDB API URL (default: gracedb-test)",
    )
    gracedb_group.add_argument(
        "--tag-name",
        default="sky_loc",
        help="GraceDB tag for sky maps (default: sky_loc)",
    )

    # Plot arguments
    plot_group = parser.add_argument_group("Plot")
    plot_group.add_argument(
        "--projection",
        default="astro hours mollweide",
        help="Sky map projection (default: 'astro hours mollweide')",
    )
    plot_group.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="PNG resolution in DPI (default: 150)",
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
        help="Don't write metrics to InfluxDB (log only)",
    )
    influx_group.add_argument(
        "--no-metrics",
        action="store_true",
        help="Disable metrics collection entirely",
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

    # Configure SGN logging
    configure_sgn_logging()
    logger = logging.getLogger("sgn.sgnllai")
    logger.setLevel(getattr(logging, args.log_level))

    metrics_enabled = not args.no_metrics

    logger.info("Creating Bayestar pipeline...")
    logger.info(f"  Input topic: {args.input_topic}")
    logger.info(f"  Workers: {args.num_workers}")
    logger.info(f"  GraceDB URL: {args.gracedb_url}")
    logger.info(f"  Bayestar: f_low={args.f_low}Hz, waveform={args.waveform}")
    if metrics_enabled:
        logger.info(
            f"  Metrics: {args.influxdb_host}:{args.influxdb_port}/{args.influxdb_db}"
            f"{' [DRY-RUN]' if args.metrics_dry_run else ''}"
        )
    else:
        logger.info("  Metrics: [DISABLED]")

    # Create pipeline elements with clear names for topology visualization
    # Naming convention: "Type: Description" where Type indicates the system/function
    source = KafkaSource(
        name="Kafka: Superevents In",
        bootstrap_servers=args.kafka_server,
        topics=[args.input_topic],
        auto_offset_reset=args.offset_reset,
    )

    distributor = RoundRobinDistributor(
        name="Distribute: Round Robin",
        num_workers=args.num_workers,
        input_pad_name=args.input_topic,
        metrics_enabled=metrics_enabled,
    )

    # Build pipeline
    pipeline = MetricsPipeline(
        name="bayestar-pipeline",
        influxdb_host=args.influxdb_host,
        influxdb_port=args.influxdb_port,
        influxdb_db=args.influxdb_db,
        grafana_influxdb_url=f"http://{args.influxdb_host}:{args.influxdb_port}",
    )
    pipeline.insert(source, distributor)
    pipeline.connect(source, distributor)

    # Create N parallel worker chains with fan-out architecture
    # Note: Metrics written directly via shared MetricsWriter (no metrics pads)
    for i in range(args.num_workers):
        # Bayestar processor
        bayestar = BayestarProcessor(
            name=f"Bayestar: Worker {i}",
            worker_id=i,
            f_low=args.f_low,
            waveform=args.waveform,
            output_dir=args.output_dir,
            metrics_enabled=metrics_enabled,
        )

        # FITS sink (uploads FITS to GraceDB superevent)
        fits_sink = GraceDBSink(
            name=f"GraceDB: FITS {i}",
            gracedb_url=args.gracedb_url,
            file_data_field="fits_data",
            filename_template="bayestar.fits.gz",
            tag_name=args.tag_name,
            file_type="fits",
            message_template="sky localization complete",
            graceid_path="superevent_id",
            metrics_enabled=metrics_enabled,
        )

        # Skymap plotter (FITS → PNG)
        plotter = SkymapPlotter(
            name=f"Plot: Skymap {i}",
            projection=args.projection,
            dpi=args.dpi,
            metrics_enabled=metrics_enabled,
        )

        # PNG sink (uploads PNG to GraceDB superevent)
        png_sink = GraceDBSink(
            name=f"GraceDB: PNG {i}",
            gracedb_url=args.gracedb_url,
            file_data_field="png_data",
            filename_template="bayestar.png",
            tag_name=args.tag_name,
            file_type="png",
            message_template="Mollweide projection of bayestar.fits.gz ({filename})",
            graceid_path="superevent_id",
            metrics_enabled=metrics_enabled,
        )

        # Skymap latency: measures time from superevent t_0 to when FITS is ready
        skymap_latency = EventLatency(
            name=f"Measure: Skymap Latency {i}",
            metric_name="skymap_latency",
            time_field="t_0",
            tag_field=None,
            description="Skymap latency (t_0 to FITS ready)",
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
            input_pad_name="out",
            output_pad_name="latency_out",
            metrics_enabled=metrics_enabled,
        )

        # Insert elements
        pipeline.insert(bayestar, fits_sink, plotter, png_sink, skymap_latency)

        # Connect with fan-out pattern:
        #   distributor → bayestar
        #   bayestar "out" → skymap_latency → fits_sink (FITS upload)
        #   bayestar "out" → plotter → png_sink (PNG upload)
        pipeline.connect(select(distributor, f"worker_{i}"), bayestar)
        pipeline.connect(select(bayestar, "out"), skymap_latency)
        pipeline.connect(select(skymap_latency, "latency_out"), fits_sink)
        pipeline.connect(select(bayestar, "out"), plotter)  # Fan-out: to plotter
        pipeline.connect(select(plotter, "out"), png_sink)

    # Log discovered metrics
    metrics_schema = pipeline.get_metrics_schema()
    if metrics_schema:
        logger.info(f"Discovered {len(metrics_schema)} metrics from pipeline elements:")
        for metric in metrics_schema[:10]:  # Show first 10
            logger.info(f"  - {metric.name} ({metric.metric_type})")
        if len(metrics_schema) > 10:
            logger.info(f"  ... and {len(metrics_schema) - 10} more")

    # Handle export-only modes (exit without running pipeline)
    if args.export_dashboard:
        pipeline.export_grafana_dashboard(
            args.export_dashboard, "SGN-LLAI Bayestar Pipeline"
        )
        logger.info(f"Dashboard exported to {args.export_dashboard}")
        return

    if args.export_manifest:
        pipeline.write_metrics_manifest(args.export_manifest)
        logger.info(f"Manifest exported to {args.export_manifest}")
        return

    logger.info("Starting pipeline (Ctrl+C to stop)...")

    # Run with parallelization support
    with SignalEOS():
        if Parallelize.needs_parallelization(pipeline):
            with Parallelize(pipeline) as p:
                p.run()
        else:
            pipeline.run()

    logger.info("Pipeline has shut down cleanly.")


if __name__ == "__main__":
    main()
