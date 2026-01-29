"""
Performance monitoring for bulk operations.

Tracks operation timing and provides metrics for performance analysis.
"""

import time
import logging
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class BulkMetrics:
    """
    Stores aggregate metrics for bulk operations.
    """
    
    def __init__(self):
        """Initialize empty metrics."""
        self.total_operations = 0
        self.total_records = 0
        self.total_duration = 0.0
        self.operations = {}  # {operation_type: {count, records, duration}}
    
    def record_operation(self, operation_type, count, duration):
        """
        Record an operation's metrics.
        
        Args:
            operation_type: Type of operation ('create', 'update', etc.)
            count: Number of records processed
            duration: Duration in seconds
        """
        self.total_operations += 1
        self.total_records += count
        self.total_duration += duration
        
        if operation_type not in self.operations:
            self.operations[operation_type] = {
                'count': 0,
                'records': 0,
                'duration': 0.0
            }
        
        self.operations[operation_type]['count'] += 1
        self.operations[operation_type]['records'] += count
        self.operations[operation_type]['duration'] += duration
    
    def get_average_duration(self):
        """
        Get average duration per operation.
        
        Returns:
            Average duration in seconds
        """
        if self.total_operations == 0:
            return 0.0
        return self.total_duration / self.total_operations
    
    def get_records_per_second(self):
        """
        Get overall records per second.
        
        Returns:
            Records per second
        """
        if self.total_duration == 0:
            return 0.0
        return self.total_records / self.total_duration
    
    def get_operation_stats(self, operation_type):
        """
        Get statistics for a specific operation type.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Dict with operation statistics or None
        """
        if operation_type not in self.operations:
            return None
        
        op_data = self.operations[operation_type]
        avg_duration = op_data['duration'] / op_data['count'] if op_data['count'] > 0 else 0
        records_per_sec = op_data['records'] / op_data['duration'] if op_data['duration'] > 0 else 0
        
        return {
            'total_operations': op_data['count'],
            'total_records': op_data['records'],
            'total_duration': op_data['duration'],
            'avg_duration': avg_duration,
            'records_per_second': records_per_sec
        }
    
    def summary(self):
        """
        Generate metrics summary.
        
        Returns:
            Dict with comprehensive metrics
        """
        summary_data = {
            'total_operations': self.total_operations,
            'total_records': self.total_records,
            'total_duration': round(self.total_duration, 3),
            'avg_duration_per_operation': round(self.get_average_duration(), 3),
            'records_per_second': round(self.get_records_per_second(), 2),
            'by_operation': {}
        }
        
        for op_type in self.operations:
            summary_data['by_operation'][op_type] = self.get_operation_stats(op_type)
        
        return summary_data


class BulkPerformanceMonitor:
    """
    Monitors bulk operation performance.
    """
    
    def __init__(self, enabled=False):
        """
        Initialize monitoring state.
        
        Args:
            enabled: Whether monitoring is enabled
        """
        self.enabled = enabled
        self.metrics = BulkMetrics()
        self._current_operation = None
        self._start_time = None
    
    @contextmanager
    def monitor_operation(self, operation_type, count):
        """
        Context manager for monitoring an operation.
        
        Args:
            operation_type: Type of operation ('create', 'update', etc.)
            count: Number of records being processed
            
        Yields:
            None
            
        Example:
            with monitor.monitor_operation('create', 100):
                # perform bulk create
                pass
        """
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_operation(operation_type, count, duration)
    
    def start_operation(self, operation_type, count):
        """
        Start timing an operation.
        
        Args:
            operation_type: Type of operation
            count: Number of records
        """
        if not self.enabled:
            return
        
        self._current_operation = {
            'type': operation_type,
            'count': count,
            'start_time': time.time()
        }
    
    def end_operation(self):
        """
        End timing and record metrics.
        
        Returns:
            Duration in seconds
        """
        if not self.enabled or not self._current_operation:
            return 0.0
        
        duration = time.time() - self._current_operation['start_time']
        
        self.record_operation(
            self._current_operation['type'],
            self._current_operation['count'],
            duration
        )
        
        self._current_operation = None
        return duration
    
    def record_operation(self, operation_type, count, duration):
        """
        Record operation metrics.
        
        Args:
            operation_type: Type of operation
            count: Number of records processed
            duration: Duration in seconds
        """
        if not self.enabled:
            return
        
        self.metrics.record_operation(operation_type, count, duration)
        self.log_operation(operation_type, count, duration)
        self.warn_if_slow(operation_type, count, duration)
    
    def log_operation(self, operation_type, count, duration):
        """
        Log operation details.
        
        Args:
            operation_type: Type of operation
            count: Number of records
            duration: Duration in seconds
        """
        if not self.enabled:
            return
        
        records_per_sec = count / duration if duration > 0 else 0
        
        logger.info(
            f'Bulk {operation_type}: {count} records in {duration:.3f}s '
            f'({records_per_sec:.0f} records/sec)'
        )
    
    def warn_if_slow(self, operation_type, count, duration, threshold=1.0):
        """
        Log warning if operation exceeds threshold.
        
        Args:
            operation_type: Type of operation
            count: Number of records
            duration: Duration in seconds
            threshold: Warning threshold in seconds
        """
        if not self.enabled:
            return
        
        if duration > threshold:
            records_per_sec = count / duration if duration > 0 else 0
            logger.warning(
                f'Slow bulk {operation_type}: {count} records took {duration:.3f}s '
                f'({records_per_sec:.0f} records/sec) - exceeds {threshold}s threshold'
            )
    
    def get_metrics(self):
        """
        Get current metrics object.
        
        Returns:
            BulkMetrics instance
        """
        return self.metrics
    
    def get_summary(self):
        """
        Get metrics summary.
        
        Returns:
            Dict with summary data
        """
        return self.metrics.summary()
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = BulkMetrics()
        self._current_operation = None
        self._start_time = None


# Global monitor instance
_global_monitor = None


def get_monitor(enabled=None):
    """
    Get global monitor instance.
    
    Args:
        enabled: Override enabled state (uses settings if None)
        
    Returns:
        BulkPerformanceMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        if enabled is None:
            from .settings import bulk_settings
            enabled = bulk_settings.enable_performance_monitoring
        
        _global_monitor = BulkPerformanceMonitor(enabled=enabled)
    
    return _global_monitor


def reset_monitor():
    """Reset global monitor instance."""
    global _global_monitor
    if _global_monitor:
        _global_monitor.reset()

