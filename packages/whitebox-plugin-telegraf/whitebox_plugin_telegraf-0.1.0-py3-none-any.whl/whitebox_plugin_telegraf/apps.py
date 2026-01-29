from django.apps import AppConfig
from plugin.registry import model_registry


class WhiteboxPluginTelegrafConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whitebox_plugin_telegraf"
    verbose_name = "Hardware Monitoring (Telegraf)"

    def ready(self):
        from .models import (
            CPUMetric,
            MemoryMetric,
            DiskMetric,
            DiskIOMetric,
            NetworkMetric,
            SystemMetric,
            TemperatureMetric,
        )

        model_registry.register("telegraf.CPUMetric", CPUMetric)
        model_registry.register("telegraf.MemoryMetric", MemoryMetric)
        model_registry.register("telegraf.DiskMetric", DiskMetric)
        model_registry.register("telegraf.DiskIOMetric", DiskIOMetric)
        model_registry.register("telegraf.NetworkMetric", NetworkMetric)
        model_registry.register("telegraf.SystemMetric", SystemMetric)
        model_registry.register("telegraf.TemperatureMetric", TemperatureMetric)
