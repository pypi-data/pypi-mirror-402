from __future__ import annotations
__all__ = ['HardwareMetricReportingJob']
from itertools import groupby
import os
import time
from typing import TYPE_CHECKING
from minfx.neptune_v2.common.hardware.gauges.gauge_factory import GaugeFactory
from minfx.neptune_v2.common.hardware.gauges.gauge_mode import GaugeMode
from minfx.neptune_v2.common.hardware.gpu.gpu_monitor import GPUMonitor
from minfx.neptune_v2.common.hardware.metrics.metrics_factory import MetricsFactory
from minfx.neptune_v2.common.hardware.metrics.reports.metric_reporter_factory import MetricReporterFactory
from minfx.neptune_v2.common.hardware.resources.system_resource_info_factory import SystemResourceInfoFactory
from minfx.neptune_v2.common.hardware.system.system_monitor import SystemMonitor
from minfx.neptune_v2.common.utils import in_docker
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.threading.daemon import Daemon
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.types.series import FloatSeries
_logger = get_logger()

class HardwareMetricReportingJob(BackgroundJob):

    def __init__(self, period=10, attribute_namespace='monitoring'):
        self._period = period
        self._thread = None
        self._started = False
        self._gauges_in_resource = {}
        self._attribute_namespace = attribute_namespace

    def start(self, container):
        gauge_mode = GaugeMode.CGROUP if in_docker() else GaugeMode.SYSTEM
        system_resource_info = SystemResourceInfoFactory(system_monitor=SystemMonitor(), gpu_monitor=GPUMonitor(), os_environ=os.environ).create(gauge_mode=gauge_mode)
        gauge_factory = GaugeFactory(gauge_mode=gauge_mode)
        metrics_factory = MetricsFactory(gauge_factory=gauge_factory, system_resource_info=system_resource_info)
        metrics_container = metrics_factory.create_metrics_container()
        metric_reporter = MetricReporterFactory(time.time()).create(metrics=metrics_container.metrics())
        for metric in metrics_container.metrics():
            self._gauges_in_resource[metric.resource_type] = len(metric.gauges)
        for metric in metrics_container.metrics():
            for gauge in metric.gauges:
                path = self.get_attribute_name(metric.resource_type, gauge.name())
                if not container.get_attribute(path):
                    container[path] = FloatSeries([], min=metric.min_value, max=metric.max_value, unit=metric.unit)
        self._thread = self.ReportingThread(self, self._period, container, metric_reporter)
        self._thread.start()
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._thread.interrupt()

    def pause(self):
        self._thread.pause()

    def resume(self):
        self._thread.resume()

    def join(self, seconds=None):
        if not self._started:
            return
        self._thread.join(seconds)

    def get_attribute_name(self, resource_type, gauge_name):
        gauges_count = self._gauges_in_resource.get(resource_type, None)
        if gauges_count is None or gauges_count != 1:
            return f'{self._attribute_namespace}/{resource_type}_{gauge_name}'.lower()
        return f'{self._attribute_namespace}/{resource_type}'.lower()

    class ReportingThread(Daemon):

        def __init__(self, outer, period, container, metric_reporter):
            super().__init__(sleep_time=period, name='NeptuneReporting')
            self._outer = outer
            self._container = container
            self._metric_reporter = metric_reporter

        def work(self):
            metric_reports = self._metric_reporter.report(time.time())
            for report in metric_reports:
                for gauge_name, metric_values in groupby(report.values, lambda value: value.gauge_name):
                    attr = self._container[self._outer.get_attribute_name(report.metric.resource_type, gauge_name)]
                    for metric_value in metric_values:
                        attr.log(value=metric_value.value, timestamp=metric_value.timestamp)