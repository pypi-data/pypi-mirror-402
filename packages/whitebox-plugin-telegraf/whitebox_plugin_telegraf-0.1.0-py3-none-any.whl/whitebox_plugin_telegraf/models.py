from django.db import models
from django.db.models.functions import Now


class HardwareMetric(models.Model):
    """
    Base model for all hardware metrics collected by Telegraf.

    Uses db_default for database-level defaults, allowing Telegraf
    to insert directly via PostgreSQL without going through Django ORM.
    """

    # Timestamps with database-level defaults for direct SQL inserts
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    timestamp = models.DateTimeField(db_index=True, help_text="Metric timestamp")
    hostname = models.CharField(
        max_length=255, db_default="whitebox", help_text="Host identifier"
    )

    class Meta:
        abstract = True
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
        ]


class CPUMetric(HardwareMetric):
    usage_user = models.FloatField(db_default=0.0, help_text="% CPU time in user space")
    usage_system = models.FloatField(
        db_default=0.0, help_text="% CPU time in kernel space"
    )
    usage_idle = models.FloatField(db_default=100.0, help_text="% CPU time idle")
    usage_iowait = models.FloatField(
        null=True, blank=True, help_text="% CPU time waiting for I/O"
    )
    usage_active = models.FloatField(
        null=True, blank=True, help_text="% Total active CPU time"
    )
    usage_guest = models.FloatField(
        null=True, blank=True, help_text="% CPU time running guest VMs"
    )
    usage_guest_nice = models.FloatField(
        null=True, blank=True, help_text="% CPU time running niced guest VMs"
    )
    usage_irq = models.FloatField(
        null=True, blank=True, help_text="% CPU time servicing interrupts"
    )
    usage_nice = models.FloatField(
        null=True, blank=True, help_text="% CPU time running niced processes"
    )
    usage_softirq = models.FloatField(
        null=True, blank=True, help_text="% CPU time servicing soft interrupts"
    )
    usage_steal = models.FloatField(
        null=True, blank=True, help_text="% CPU time stolen by hypervisor"
    )

    class Meta:
        verbose_name = "CPU Metric"
        verbose_name_plural = "CPU Metrics"
        ordering = ["-timestamp"]


class MemoryMetric(HardwareMetric):
    total = models.BigIntegerField(db_default=0, help_text="Total memory in bytes")
    available = models.BigIntegerField(
        db_default=0, help_text="Available memory in bytes"
    )
    used = models.BigIntegerField(db_default=0, help_text="Used memory in bytes")
    used_percent = models.FloatField(db_default=0.0, help_text="% memory used")
    cached = models.BigIntegerField(
        null=True, blank=True, help_text="Cached memory in bytes"
    )
    buffered = models.BigIntegerField(
        null=True, blank=True, help_text="Buffered memory in bytes"
    )

    # Active/Inactive Memory
    active = models.BigIntegerField(
        null=True, blank=True, help_text="Recently used memory in bytes"
    )
    inactive = models.BigIntegerField(
        null=True, blank=True, help_text="Memory not recently used in bytes"
    )

    # Free/Available
    free = models.BigIntegerField(
        null=True, blank=True, help_text="Completely unused memory in bytes"
    )
    available_percent = models.FloatField(
        null=True, blank=True, help_text="% memory available"
    )

    # Shared/Mapped
    shared = models.BigIntegerField(
        null=True, blank=True, help_text="Shared memory in bytes"
    )
    mapped = models.BigIntegerField(
        null=True, blank=True, help_text="Mapped files in bytes"
    )

    # Dirty/Writeback
    dirty = models.BigIntegerField(
        null=True, blank=True, help_text="Memory waiting to be written in bytes"
    )
    write_back = models.BigIntegerField(
        null=True, blank=True, help_text="Memory being written back in bytes"
    )
    write_back_tmp = models.BigIntegerField(
        null=True, blank=True, help_text="Temporary writeback memory in bytes"
    )

    # Swap
    swap_total = models.BigIntegerField(
        null=True, blank=True, help_text="Total swap space in bytes"
    )
    swap_free = models.BigIntegerField(
        null=True, blank=True, help_text="Free swap space in bytes"
    )
    swap_cached = models.BigIntegerField(
        null=True, blank=True, help_text="Cached swap in bytes"
    )

    # Slab
    slab = models.BigIntegerField(
        null=True, blank=True, help_text="Kernel slab memory in bytes"
    )
    sreclaimable = models.BigIntegerField(
        null=True, blank=True, help_text="Reclaimable slab in bytes"
    )
    sunreclaim = models.BigIntegerField(
        null=True, blank=True, help_text="Unreclaimable slab in bytes"
    )

    # Page Tables
    page_tables = models.BigIntegerField(
        null=True, blank=True, help_text="Page table memory in bytes"
    )

    # Commit
    commit_limit = models.BigIntegerField(
        null=True, blank=True, help_text="Total committable memory in bytes"
    )
    committed_as = models.BigIntegerField(
        null=True, blank=True, help_text="Currently committed memory in bytes"
    )

    # High/Low (legacy)
    high_total = models.BigIntegerField(
        null=True, blank=True, help_text="High memory total in bytes"
    )
    high_free = models.BigIntegerField(
        null=True, blank=True, help_text="High memory free in bytes"
    )
    low_total = models.BigIntegerField(
        null=True, blank=True, help_text="Low memory total in bytes"
    )
    low_free = models.BigIntegerField(
        null=True, blank=True, help_text="Low memory free in bytes"
    )

    # Huge Pages
    huge_page_size = models.BigIntegerField(
        null=True, blank=True, help_text="Size of huge pages in bytes"
    )
    huge_pages_total = models.BigIntegerField(
        null=True, blank=True, help_text="Total huge pages"
    )
    huge_pages_free = models.BigIntegerField(
        null=True, blank=True, help_text="Free huge pages"
    )

    # Vmalloc
    vmalloc_total = models.BigIntegerField(
        null=True, blank=True, help_text="Total vmalloc area in bytes"
    )
    vmalloc_used = models.BigIntegerField(
        null=True, blank=True, help_text="Used vmalloc area in bytes"
    )
    vmalloc_chunk = models.BigIntegerField(
        null=True, blank=True, help_text="Largest free vmalloc chunk in bytes"
    )

    class Meta:
        verbose_name = "Memory Metric"
        verbose_name_plural = "Memory Metrics"
        ordering = ["-timestamp"]


class DiskMetric(HardwareMetric):
    path = models.CharField(max_length=255, db_default="/", help_text="Mount path")
    device = models.CharField(
        max_length=255, db_default="unknown", help_text="Device name"
    )
    fstype = models.CharField(
        max_length=50, db_default="unknown", help_text="Filesystem type"
    )
    total = models.BigIntegerField(db_default=0, help_text="Total space in bytes")
    used = models.BigIntegerField(db_default=0, help_text="Used space in bytes")
    free = models.BigIntegerField(db_default=0, help_text="Free space in bytes")
    used_percent = models.FloatField(db_default=0.0, help_text="% disk used")
    inodes_total = models.BigIntegerField(
        null=True, blank=True, help_text="Total inodes"
    )
    inodes_used = models.BigIntegerField(null=True, blank=True, help_text="Used inodes")
    inodes_free = models.BigIntegerField(null=True, blank=True, help_text="Free inodes")
    inodes_used_percent = models.FloatField(
        null=True, blank=True, help_text="% inodes used"
    )

    class Meta:
        verbose_name = "Disk Metric"
        verbose_name_plural = "Disk Metrics"
        ordering = ["-timestamp"]


class DiskIOMetric(HardwareMetric):
    device = models.CharField(
        max_length=255, db_default="unknown", help_text="Device name"
    )
    reads = models.BigIntegerField(db_default=0, help_text="Number of reads")
    writes = models.BigIntegerField(db_default=0, help_text="Number of writes")
    read_bytes = models.BigIntegerField(db_default=0, help_text="Bytes read")
    write_bytes = models.BigIntegerField(db_default=0, help_text="Bytes written")
    read_time_ms = models.BigIntegerField(
        db_default=0, help_text="Time spent reading (ms)"
    )
    write_time_ms = models.BigIntegerField(
        db_default=0, help_text="Time spent writing (ms)"
    )
    io_time_ms = models.BigIntegerField(
        db_default=0, help_text="Time spent doing I/Os (ms)"
    )
    io_await = models.FloatField(
        null=True, blank=True, help_text="Average I/O wait time (ms)"
    )
    io_svctm = models.FloatField(
        null=True, blank=True, help_text="Average service time (ms)"
    )
    io_util = models.FloatField(
        null=True, blank=True, help_text="I/O utilization percentage"
    )
    iops_in_progress = models.IntegerField(
        db_default=0, help_text="I/O operations currently in progress"
    )
    merged_reads = models.BigIntegerField(
        null=True, blank=True, help_text="Number of merged read operations"
    )
    merged_writes = models.BigIntegerField(
        null=True, blank=True, help_text="Number of merged write operations"
    )
    weighted_io_time = models.BigIntegerField(
        null=True, blank=True, help_text="Weighted I/O time (ms)"
    )

    class Meta:
        verbose_name = "Disk I/O Metric"
        verbose_name_plural = "Disk I/O Metrics"
        ordering = ["-timestamp"]


class NetworkMetric(HardwareMetric):
    interface = models.CharField(
        max_length=255, db_default="unknown", help_text="Network interface name"
    )
    bytes_sent = models.BigIntegerField(db_default=0, help_text="Bytes sent")
    bytes_recv = models.BigIntegerField(db_default=0, help_text="Bytes received")
    packets_sent = models.BigIntegerField(db_default=0, help_text="Packets sent")
    packets_recv = models.BigIntegerField(db_default=0, help_text="Packets received")
    err_in = models.BigIntegerField(db_default=0, help_text="Receive errors")
    err_out = models.BigIntegerField(db_default=0, help_text="Send errors")
    drop_in = models.BigIntegerField(db_default=0, help_text="Dropped incoming packets")
    drop_out = models.BigIntegerField(
        db_default=0, help_text="Dropped outgoing packets"
    )
    speed = models.IntegerField(null=True, blank=True, help_text="Link speed in Mbps")

    class Meta:
        verbose_name = "Network Metric"
        verbose_name_plural = "Network Metrics"
        ordering = ["-timestamp"]


class SystemMetric(HardwareMetric):
    uptime = models.BigIntegerField(db_default=0, help_text="System uptime in seconds")
    processes_running = models.IntegerField(
        db_default=0, help_text="Number of running processes"
    )
    processes_total = models.IntegerField(
        db_default=0, help_text="Total number of processes"
    )
    load_1m = models.FloatField(
        null=True, blank=True, help_text="1-minute load average"
    )
    load_5m = models.FloatField(
        null=True, blank=True, help_text="5-minute load average"
    )
    load_15m = models.FloatField(
        null=True, blank=True, help_text="15-minute load average"
    )
    n_cpus = models.IntegerField(
        null=True, blank=True, help_text="Number of logical CPUs"
    )
    n_physical_cpus = models.IntegerField(
        null=True, blank=True, help_text="Number of physical CPUs"
    )
    uptime_format = models.CharField(
        max_length=50, null=True, blank=True, help_text="Human-readable uptime"
    )

    class Meta:
        verbose_name = "System Metric"
        verbose_name_plural = "System Metrics"
        ordering = ["-timestamp"]


class TemperatureMetric(HardwareMetric):
    sensor = models.CharField(
        max_length=255, db_default="unknown", help_text="Temperature sensor name"
    )
    temp = models.FloatField(db_default=0.0, help_text="Temperature in Celsius")

    class Meta:
        verbose_name = "Temperature Metric"
        verbose_name_plural = "Temperature Metrics"
        ordering = ["-timestamp"]
