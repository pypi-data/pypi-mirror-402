"""
Model Monitoring System for Calabi Compressed Models

This module provides comprehensive monitoring tools for tracking:
- Inference performance metrics
- Model accuracy degradation over time
- Resource utilization
- Alerting for performance anomalies
"""

import torch
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import numpy as np
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics."""
    timestamp: datetime
    latency_ms: float
    throughput_samples_per_sec: float
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_memory_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None


@dataclass
class AccuracyMetrics:
    """Data class for storing accuracy-related metrics."""
    timestamp: datetime
    mse_error: float
    cosine_similarity: float
    kl_divergence: float
    accuracy_drop_percent: float


class MetricsCollector:
    """Collect and store various performance metrics."""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.performance_metrics: deque = deque(maxlen=buffer_size)
        self.accuracy_metrics: deque = deque(maxlen=buffer_size)
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=buffer_size))
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def collect_performance(self, latency_ms: float, throughput: float):
        """Collect performance metrics."""
        with self.lock:
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                throughput_samples_per_sec=throughput,
                memory_usage_mb=self._get_memory_usage(),
                cpu_usage_percent=self._get_cpu_usage()
            )
            
            if torch.cuda.is_available():
                metrics.gpu_memory_mb = self._get_gpu_memory()
                metrics.gpu_utilization_percent = self._get_gpu_utilization()
            
            self.performance_metrics.append(metrics)
    
    def collect_accuracy(self, original_output: torch.Tensor, 
                        compressed_output: torch.Tensor, 
                        ground_truth: Optional[torch.Tensor] = None):
        """Collect accuracy metrics comparing original vs compressed model."""
        with self.lock:
            # Calculate various accuracy metrics
            mse_error = torch.mean((original_output - compressed_output) ** 2).item()
            
            # Cosine similarity
            cos_sim = torch.nn.functional.cosine_similarity(
                original_output.flatten(), compressed_output.flatten(), dim=0
            ).item()
            
            # KL divergence (add small epsilon to avoid log(0))
            orig_probs = torch.softmax(original_output, dim=-1)
            comp_probs = torch.softmax(compressed_output, dim=-1)
            kl_div = torch.sum(orig_probs * torch.log(orig_probs / (comp_probs + 1e-8))).item()
            
            # Accuracy drop calculation
            accuracy_drop = 0.0
            if ground_truth is not None:
                orig_acc = (torch.argmax(original_output, dim=-1) == ground_truth).float().mean().item()
                comp_acc = (torch.argmax(compressed_output, dim=-1) == ground_truth).float().mean().item()
                accuracy_drop = ((orig_acc - comp_acc) / orig_acc * 100) if orig_acc > 0 else 0.0
            
            metrics = AccuracyMetrics(
                timestamp=datetime.now(),
                mse_error=mse_error,
                cosine_similarity=cos_sim,
                kl_divergence=kl_div,
                accuracy_drop_percent=accuracy_drop
            )
            
            self.accuracy_metrics.append(metrics)
    
    def collect_custom_metric(self, metric_name: str, value: float):
        """Collect custom metrics."""
        with self.lock:
            self.custom_metrics[metric_name].append({
                'timestamp': datetime.now(),
                'value': value
            })
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if PSUTIL_AVAILABLE:
            return psutil.Process().memory_info().rss / 1024 / 1024
        return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        if PSUTIL_AVAILABLE:
            return psutil.cpu_percent(interval=0.1)
        return 0.0
    
    def _get_gpu_memory(self) -> Optional[float]:
        """Get GPU memory usage in MB."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024 / 1024
        return None
    
    def _get_gpu_utilization(self) -> Optional[float]:
        """Get GPU utilization percentage."""
        if torch.cuda.is_available():
            # This is a rough estimate - real GPU utilization requires nvidia-ml-py
            return None  # Placeholder
        return None
    
    def get_recent_performance(self, n: int = 100) -> List[PerformanceMetrics]:
        """Get recent performance metrics."""
        with self.lock:
            return list(self.performance_metrics)[-n:]
    
    def get_recent_accuracy(self, n: int = 100) -> List[AccuracyMetrics]:
        """Get recent accuracy metrics."""
        with self.lock:
            return list(self.accuracy_metrics)[-n:]


class AnomalyDetector:
    """Detect performance anomalies using statistical methods."""
    
    def __init__(self, window_size: int = 50, threshold_std: float = 3.0):
        self.window_size = window_size
        self.threshold_std = threshold_std
        self.baseline_stats = {}
        self.alerts = []
    
    def establish_baseline(self, metrics_collector: MetricsCollector, 
                          samples: int = 200):
        """Establish baseline performance metrics."""
        recent_perf = metrics_collector.get_recent_performance(samples)
        
        if len(recent_perf) < 10:
            raise ValueError("Need at least 10 samples to establish baseline")
        
        # Calculate baseline statistics
        latencies = [m.latency_ms for m in recent_perf]
        throughputs = [m.throughput_samples_per_sec for m in recent_perf]
        
        self.baseline_stats = {
            'latency_mean': np.mean(latencies),
            'latency_std': np.std(latencies),
            'throughput_mean': np.mean(throughputs),
            'throughput_std': np.std(throughputs)
        }
        
        print(f"Baseline established: Latency mean={self.baseline_stats['latency_mean']:.2f}ms")
    
    def detect_anomalies(self, metrics_collector: MetricsCollector) -> List[Dict]:
        """Detect anomalies in recent metrics."""
        if not self.baseline_stats:
            return []
        
        recent_perf = metrics_collector.get_recent_performance(10)
        alerts = []
        
        for metric in recent_perf:
            # Check latency anomaly
            latency_zscore = abs(metric.latency_ms - self.baseline_stats['latency_mean']) / self.baseline_stats['latency_std']
            if latency_zscore > self.threshold_std:
                alerts.append({
                    'timestamp': metric.timestamp,
                    'type': 'latency_anomaly',
                    'value': metric.latency_ms,
                    'z_score': latency_zscore,
                    'severity': 'high' if latency_zscore > self.threshold_std * 2 else 'medium'
                })
            
            # Check throughput anomaly
            throughput_zscore = abs(metric.throughput_samples_per_sec - self.baseline_stats['throughput_mean']) / self.baseline_stats['throughput_std']
            if throughput_zscore > self.threshold_std:
                alerts.append({
                    'timestamp': metric.timestamp,
                    'type': 'throughput_anomaly',
                    'value': metric.throughput_samples_per_sec,
                    'z_score': throughput_zscore,
                    'severity': 'high' if throughput_zscore > self.threshold_std * 2 else 'medium'
                })
        
        self.alerts.extend(alerts)
        return alerts


class PerformanceDashboard:
    """Create performance dashboards and reports."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, output_path: str, time_window_hours: float = 24):
        """Generate a comprehensive performance report."""
        cutoff_time = datetime.now().timestamp() - (time_window_hours * 3600)
        
        # Filter metrics by time window
        perf_metrics = [m for m in self.collector.get_recent_performance() 
                       if m.timestamp.timestamp() >= cutoff_time]
        acc_metrics = [m for m in self.collector.get_recent_accuracy()
                      if m.timestamp.timestamp() >= cutoff_time]
        
        if not perf_metrics:
            self.logger.warning("No performance metrics found in time window")
            return
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'time_window_hours': time_window_hours,
            'total_requests': len(perf_metrics),
            'performance_summary': self._calculate_performance_summary(perf_metrics),
            'accuracy_summary': self._calculate_accuracy_summary(acc_metrics),
            'alerts': self._generate_alerts(perf_metrics)
        }
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Performance report saved to {output_path}")
        return report
    
    def _calculate_performance_summary(self, metrics: List[PerformanceMetrics]) -> Dict:
        """Calculate performance summary statistics."""
        if not metrics:
            return {}
        
        latencies = [m.latency_ms for m in metrics]
        throughputs = [m.throughput_samples_per_sec for m in metrics]
        memory_usages = [m.memory_usage_mb for m in metrics]
        
        return {
            'latency_ms': {
                'mean': np.mean(latencies),
                'median': np.median(latencies),
                'std': np.std(latencies),
                'min': np.min(latencies),
                'max': np.max(latencies),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99)
            },
            'throughput_samples_per_sec': {
                'mean': np.mean(throughputs),
                'median': np.median(throughputs),
                'std': np.std(throughputs),
                'min': np.min(throughputs),
                'max': np.max(throughputs)
            },
            'memory_usage_mb': {
                'mean': np.mean(memory_usages),
                'max': np.max(memory_usages)
            }
        }
    
    def _calculate_accuracy_summary(self, metrics: List[AccuracyMetrics]) -> Dict:
        """Calculate accuracy summary statistics."""
        if not metrics:
            return {}
        
        mses = [m.mse_error for m in metrics]
        similarities = [m.cosine_similarity for m in metrics]
        kl_divs = [m.kl_divergence for m in metrics]
        accuracy_drops = [m.accuracy_drop_percent for m in metrics]
        
        return {
            'mse_error': {
                'mean': np.mean(mses),
                'max': np.max(mses)
            },
            'cosine_similarity': {
                'mean': np.mean(similarities),
                'min': np.min(similarities)
            },
            'kl_divergence': {
                'mean': np.mean(kl_divs),
                'max': np.max(kl_divs)
            },
            'accuracy_drop_percent': {
                'mean': np.mean(accuracy_drops),
                'max': np.max(accuracy_drops)
            }
        }
    
    def _generate_alerts(self, metrics: List[PerformanceMetrics]) -> List[Dict]:
        """Generate alerts based on performance thresholds."""
        alerts = []
        
        # High latency alerts
        high_latency_threshold = 100  # ms
        high_latency_count = sum(1 for m in metrics if m.latency_ms > high_latency_threshold)
        if high_latency_count > len(metrics) * 0.1:  # More than 10% of requests
            alerts.append({
                'type': 'high_latency',
                'count': high_latency_count,
                'percentage': high_latency_count / len(metrics) * 100,
                'threshold': high_latency_threshold
            })
        
        # Low throughput alerts
        low_throughput_threshold = 10  # samples/sec
        low_throughput_count = sum(1 for m in metrics if m.throughput_samples_per_sec < low_throughput_threshold)
        if low_throughput_count > len(metrics) * 0.1:
            alerts.append({
                'type': 'low_throughput',
                'count': low_throughput_count,
                'percentage': low_throughput_count / len(metrics) * 100,
                'threshold': low_throughput_threshold
            })
        
        return alerts
    
    def plot_performance_trends(self, save_path: str, hours_back: int = 24):
        """Plot performance trends over time."""
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib not available for plotting")
            return
        
        cutoff_time = datetime.now().timestamp() - (hours_back * 3600)
        metrics = [m for m in self.collector.get_recent_performance() 
                  if m.timestamp.timestamp() >= cutoff_time]
        
        if not metrics:
            print("No metrics available for plotting")
            return
        
        timestamps = [m.timestamp for m in metrics]
        latencies = [m.latency_ms for m in metrics]
        throughputs = [m.throughput_samples_per_sec for m in metrics]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Latency plot
        ax1.plot(timestamps, latencies, 'b-', alpha=0.7)
        ax1.set_ylabel('Latency (ms)')
        ax1.set_title(f'Performance Trends - Last {hours_back} Hours')
        ax1.grid(True)
        
        # Throughput plot
        ax2.plot(timestamps, throughputs, 'r-', alpha=0.7)
        ax2.set_ylabel('Throughput (samples/sec)')
        ax2.set_xlabel('Time')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
        print(f"Performance trend plot saved to {save_path}")


class ModelMonitor:
    """Main monitoring class that combines all monitoring components."""
    
    def __init__(self, buffer_size: int = 1000):
        self.metrics_collector = MetricsCollector(buffer_size)
        self.anomaly_detector = AnomalyDetector()
        self.dashboard = PerformanceDashboard(self.metrics_collector)
        self.is_monitoring = False
        self.monitoring_thread = None
    
    def start_monitoring(self, check_interval: float = 60.0):
        """Start continuous monitoring in background thread."""
        if self.is_monitoring:
            print("Monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        print(f"Monitoring started with {check_interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        print("Monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Perform periodic checks
                self._perform_periodic_checks()
                time.sleep(interval)
            except Exception as e:
                print(f"Monitoring error: {e}")
    
    def _perform_periodic_checks(self):
        """Perform periodic monitoring checks."""
        # This would integrate with your inference system to collect real metrics
        # For now, this is a placeholder
        pass
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        recent_perf = self.metrics_collector.get_recent_performance(10)
        recent_acc = self.metrics_collector.get_recent_accuracy(10)
        
        return {
            'monitoring_active': self.is_monitoring,
            'recent_performance_samples': len(recent_perf),
            'recent_accuracy_samples': len(recent_acc),
            'latest_latency_ms': recent_perf[-1].latency_ms if recent_perf else None,
            'latest_throughput': recent_perf[-1].throughput_samples_per_sec if recent_perf else None,
            'latest_accuracy_drop': recent_acc[-1].accuracy_drop_percent if recent_acc else None
        }


# Convenience functions
def create_monitor(buffer_size: int = 1000) -> ModelMonitor:
    """Create a configured model monitor."""
    return ModelMonitor(buffer_size)


def quick_performance_check(model, sample_input, num_iterations: int = 100) -> Dict[str, float]:
    """Quick performance assessment of a model."""
    model.eval()
    latencies = []
    
    # Warmup
    with torch.no_grad():
        for _ in range(10):
            _ = model(sample_input)
    
    # Timing
    with torch.no_grad():
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = model(sample_input)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
    
    return {
        'mean_latency_ms': np.mean(latencies),
        'std_latency_ms': np.std(latencies),
        'p95_latency_ms': np.percentile(latencies, 95),
        'throughput_samples_per_sec': 1000 / np.mean(latencies) * sample_input.shape[0]
    }


__all__ = [
    'MetricsCollector',
    'AnomalyDetector', 
    'PerformanceDashboard',
    'ModelMonitor',
    'PerformanceMetrics',
    'AccuracyMetrics',
    'create_monitor',
    'quick_performance_check'
]