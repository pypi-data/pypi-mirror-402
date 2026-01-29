# Whitebox Plugin - Telegraf

Hardware resource monitoring plugin for [whitebox](https://gitlab.com/whitebox-aero) using Telegraf to collect system metrics directly into PostgreSQL.

## Metrics Collected

- **CPU**: Usage percentages (user, system, idle, iowait)
- **Memory**: Total, used, available, cached, swap
- **Disk**: Space usage by mount point
- **Disk I/O**: Read/write operations and throughput
- **Network**: Bytes and packets per interface
- **System**: Uptime, load averages, process counts
- **Temperature**: Sensor readings

## Models

| Model | Description |
|-------|-------------|
| `CPUMetric` | CPU utilization data |
| `MemoryMetric` | Memory and swap usage |
| `DiskMetric` | Disk space by mount point |
| `DiskIOMetric` | Disk I/O statistics |
| `NetworkMetric` | Network interface statistics |
| `SystemMetric` | Uptime, load, process counts |
| `TemperatureMetric` | Temperature sensor readings |

## Installation

Install the plugin to whitebox:

```
poetry add whitebox-plugin-telegraf
```

## Additional Instructions

- [Plugin Development Guide](https://docs.whitebox.aero/plugin_guide/#plugin-development-workflow)
- [Plugin Testing Guide](https://docs.whitebox.aero/plugin_guide/#testing-plugins)
- [Contributing Guidelines](https://docs.whitebox.aero/development_guide/#contributing)
