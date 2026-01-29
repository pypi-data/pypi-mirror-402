# sgn-skig

SGN infrastructure for **S**cald, **K**afka, **I**nfluxDB, and **G**rafana.

Provides reusable metrics collection, pipeline infrastructure, and generic elements for [SGN](https://git.ligo.org/cbc/sgn) pipelines.

## Installation

```bash
pip install sgn-skig
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Features

### MetricsPipeline

A drop-in replacement for `sgn.Pipeline` that adds automatic metrics infrastructure:

```python
from sgneskig import MetricsPipeline

pipeline = MetricsPipeline(
    name="my-pipeline",
    influxdb_host="localhost",
    influxdb_port=8086,
    influxdb_db="my_metrics",
)

# Insert elements - metrics are automatically configured
pipeline.insert(source, transform, sink)
pipeline.connect(source, transform)
pipeline.connect(transform, sink)

# Export Grafana dashboard from discovered metrics
pipeline.export_grafana_dashboard("dashboard.json")
```

### MetricsCollectorMixin

Add metrics collection to any SGN element:

```python
from dataclasses import dataclass
from sgn.base import TransformElement
from sgneskig.metrics import MetricsCollectorMixin, metrics

@dataclass
class MyTransform(TransformElement, MetricsCollectorMixin):
    # Declarative metrics schema - auto-discovered by MetricsPipeline
    metrics_schema = metrics([
        ("events_processed", "counter", ["pipeline"], "Events processed"),
        ("process_time", "timing", [], "Processing duration"),
    ])

    # Enable automatic cycle time tracking
    track_elapsed_time: bool = True
    elapsed_metric_name: str = "my_transform_elapsed"

    def __post_init__(self):
        super().__post_init__()
        self._init_metrics()

    def internal(self):
        with self.time_operation("process_time"):
            # ... do work ...
            pass
        self.increment_counter("events_processed", tags={"pipeline": "SGNL"})
```

### Kafka Integration

**KafkaSource** - Read from Kafka topics with automatic batching:

```python
from sgneskig.sources import KafkaSource

source = KafkaSource(
    name="kafka_source",
    bootstrap_servers="localhost:9092",
    topics=["events"],
    group_id="my-consumer",
    auto_offset_reset="latest",
)
```

**KafkaSink** - Write to Kafka topics:

```python
from sgneskig.sinks import KafkaSink

sink = KafkaSink(
    name="kafka_sink",
    bootstrap_servers="localhost:9092",
    topic="output-events",
)
```

### Generic Transforms

**DelayBuffer** - Buffer events for a configurable delay:

```python
from sgneskig.transforms import DelayBuffer

buffer = DelayBuffer(
    name="delay_buffer",
    delay_seconds=30.0,  # Hold events for 30s
)
```

**EventLatency** - Measure end-to-end latency:

```python
from sgneskig.transforms import EventLatency

latency = EventLatency(
    name="latency_tracker",
    timestamp_field="gpstime",  # Field containing event timestamp
)
```

**RoundRobinDistributor** - Distribute work across multiple outputs:

```python
from sgneskig.transforms import RoundRobinDistributor

distributor = RoundRobinDistributor(
    name="distributor",
    num_outputs=4,  # Creates output pads: out_0, out_1, out_2, out_3
)
```

### Grafana Integration

Generate dashboards and datasources from your pipeline's metrics:

```python
# After inserting elements into the pipeline
pipeline.export_grafana_dashboard("grafana/dashboards/my-pipeline.json")
pipeline.export_grafana_datasource("grafana/provisioning/datasources/influxdb.yaml")

# Or get the exporter for more control
exporter = pipeline.get_grafana_exporter(dashboard_title="My Pipeline Metrics")
print(exporter.datasource_curl_command())
```

## CLI Tools

### sgn-grafana-datasource

Generate Grafana datasource provisioning YAML:

```bash
sgn-grafana-datasource --host localhost --port 8086 --db my_metrics > datasource.yaml
```

### sgn-grafana-import

Import a dashboard JSON file into Grafana:

```bash
sgn-grafana-import dashboard.json --grafana-url http://localhost:3000 --auth admin:admin
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MetricsPipeline                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     MetricsWriter                         │  │
│  │  (shared writer for direct InfluxDB writes via ligo.scald)│  │
│  └──────────────────────────────────────────────────────────┘  │
│           ▲                    ▲                    ▲          │
│           │                    │                    │          │
│  ┌────────┴───────┐   ┌───────┴────────┐   ┌───────┴───────┐  │
│  │  KafkaSource   │──▶│  MyTransform   │──▶│   KafkaSink   │  │
│  │  (metrics via  │   │  (metrics via  │   │  (metrics via │  │
│  │   mixin)       │   │   mixin)       │   │   mixin)      │  │
│  └────────────────┘   └────────────────┘   └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                         ┌────────────┐
                         │  InfluxDB  │
                         │ (1s, 10s,  │
                         │  100s, ... │
                         │ retention) │
                         └────────────┘
                                │
                                ▼
                         ┌────────────┐
                         │  Grafana   │
                         └────────────┘
```

## Metrics Storage

sgn-skig uses [ligo.scald](https://lscsoft.docs.ligo.org/scald/) for multi-resolution time series storage. Data is automatically aggregated at multiple resolutions:

- `1s` - 1 second buckets
- `10s` - 10 second buckets
- `100s` - ~1.5 minute buckets
- `1000s` - ~16 minute buckets
- `10000s` - ~2.7 hour buckets
- `100000s` - ~1 day buckets

Retention policies are created automatically on first write.

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Run all checks
make
```

## License

MPL-2.0
