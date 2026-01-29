"""
StatSD Server Implementation

A TCP + UDP StatSD server that collects metrics, batches them,
and forwards to a remote stats endpoint every 10 seconds.
"""

import logging
import signal
import socket
import socketserver
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional, Union

from heare.config import SettingsDefinition, Setting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('heare.stats.server')


class MetricAggregator:
    """
    Thread-safe metric aggregator that collects and batches metrics.
    
    Supports:
    - Counters (c): Accumulated values
    - Gauges (g): Last value wins
    - Timers (ms): List of timing values
    - Histograms (h): List of histogram values
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
    
    def record_counter(self, name: str, value: float, sample_rate: float = 1.0):
        """Record a counter metric, applying sample rate correction."""
        with self._lock:
            # Apply sample rate correction
            adjusted_value = value / sample_rate if sample_rate > 0 else value
            self._counters[name] += adjusted_value
            logger.debug(f"Recorded counter: {name} = {self._counters[name]}")
    
    def record_gauge(self, name: str, value: float, delta: bool = False):
        """Record a gauge metric. If delta is True, add to existing value."""
        with self._lock:
            if delta and name in self._gauges:
                self._gauges[name] += value
            else:
                self._gauges[name] = value
            logger.debug(f"Recorded gauge: {name} = {self._gauges[name]}")
    
    def record_timer(self, name: str, value: float):
        """Record a timer metric (in milliseconds)."""
        with self._lock:
            self._timers[name].append(value)
            logger.debug(f"Recorded timer: {name} = {value}")
    
    def record_histogram(self, name: str, value: float):
        """Record a histogram metric."""
        with self._lock:
            self._histograms[name].append(value)
            logger.debug(f"Recorded histogram: {name} = {value}")
    
    def flush(self) -> dict:
        """
        Flush all metrics and return them as a dict.
        Clears all internal state.
        """
        with self._lock:
            result = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'timers': {k: list(v) for k, v in self._timers.items()},
                'histograms': {k: list(v) for k, v in self._histograms.items()}
            }
            
            # Clear all metrics
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
            self._histograms.clear()
            
            return result
    
    def get_metric_names(self) -> List[str]:
        """Get all unique metric names currently stored."""
        with self._lock:
            names = set()
            names.update(self._counters.keys())
            names.update(self._gauges.keys())
            names.update(self._timers.keys())
            names.update(self._histograms.keys())
            return sorted(names)


class StatsdProtocolParser:
    """
    Parser for the StatsD wire protocol.
    
    Format: <metric_name>:<value>|<type>[@<sample_rate>]
    
    Types:
    - c: Counter
    - g: Gauge (supports +/- prefix for delta)
    - ms: Timer (milliseconds)
    - h: Histogram
    - s: Set (not implemented, will be logged and skipped)
    """
    
    @staticmethod
    def parse_line(line: str) -> Optional[dict]:
        """
        Parse a single StatsD protocol line.
        
        Returns a dict with:
        - name: metric name
        - value: numeric value
        - type: metric type (counter, gauge, timer, histogram)
        - sample_rate: optional sample rate (default 1.0)
        - delta: for gauges, whether this is a delta update
        
        Returns None if the line cannot be parsed.
        """
        line = line.strip()
        if not line:
            return None
        
        try:
            # Split on first colon to get metric name
            name_part, rest = line.split(':', 1)
            name = name_part.strip()
            
            if not name:
                return None
            
            # Split value|type[@sample_rate]
            if '|' not in rest:
                return None
            
            value_part, type_and_rate = rest.split('|', 1)
            
            # Parse sample rate if present
            sample_rate = 1.0
            if '@' in type_and_rate:
                type_part, rate_part = type_and_rate.split('@', 1)
                try:
                    sample_rate = float(rate_part)
                except ValueError:
                    sample_rate = 1.0
            else:
                type_part = type_and_rate
            
            type_part = type_part.strip().lower()
            
            # Parse value - handle gauge delta notation (+/-)
            delta = False
            value_str = value_part.strip()
            
            if type_part == 'g' and value_str and value_str[0] in ('+', '-'):
                delta = True
            
            try:
                value = float(value_str)
            except ValueError:
                return None
            
            # Map type codes to type names
            type_map = {
                'c': 'counter',
                'g': 'gauge',
                'ms': 'timer',
                'h': 'histogram',
                's': 'set'  # Not implemented but recognized
            }
            
            metric_type = type_map.get(type_part)
            if not metric_type:
                logger.warning(f"Unknown metric type: {type_part}")
                return None
            
            if metric_type == 'set':
                logger.debug(f"Set metrics not implemented, skipping: {name}")
                return None
            
            return {
                'name': name,
                'value': value,
                'type': metric_type,
                'sample_rate': sample_rate,
                'delta': delta
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse line '{line}': {e}")
            return None
    
    @staticmethod
    def parse_message(data: bytes) -> List[dict]:
        """
        Parse a StatsD message (potentially containing multiple metrics).
        
        Messages can be newline-separated for batch sending.
        """
        metrics = []
        try:
            text = data.decode('utf-8', errors='replace')
            for line in text.split('\n'):
                parsed = StatsdProtocolParser.parse_line(line)
                if parsed:
                    metrics.append(parsed)
        except Exception as e:
            logger.warning(f"Failed to parse message: {e}")
        
        return metrics


class UDPHandler(socketserver.BaseRequestHandler):
    """Handler for UDP StatsD messages."""
    
    def handle(self):
        data = self.request[0]
        logger.debug(f"UDP received: {data}")
        metrics = StatsdProtocolParser.parse_message(data)
        
        for metric in metrics:
            logger.debug(f"Recording metric: {metric}")
            self.server.record_metric(metric)


class TCPHandler(socketserver.StreamRequestHandler):
    """Handler for TCP StatsD messages."""
    
    def handle(self):
        """Handle TCP connection - read lines until connection closes."""
        try:
            while True:
                line = self.rfile.readline()
                if not line:
                    break
                
                logger.debug(f"TCP received: {line}")
                metrics = StatsdProtocolParser.parse_message(line)
                for metric in metrics:
                    logger.debug(f"Recording metric: {metric}")
                    self.server.record_metric(metric)
        except Exception as e:
            logger.debug(f"TCP connection error: {e}")


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    """Threaded UDP server."""
    allow_reuse_address = True
    
    def __init__(self, server_address, handler_class, aggregator, prefix=None):
        super().__init__(server_address, handler_class)
        self.aggregator = aggregator
        self.prefix = prefix
    
    def record_metric(self, metric: dict):
        """Record a metric with optional prefix."""
        name = metric['name']
        if self.prefix:
            name = f"{self.prefix}.{name}"
        
        value = metric['value']
        metric_type = metric['type']
        
        if metric_type == 'counter':
            self.aggregator.record_counter(name, value, metric.get('sample_rate', 1.0))
        elif metric_type == 'gauge':
            self.aggregator.record_gauge(name, value, metric.get('delta', False))
        elif metric_type == 'timer':
            self.aggregator.record_timer(name, value)
        elif metric_type == 'histogram':
            self.aggregator.record_histogram(name, value)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server."""
    allow_reuse_address = True
    
    def __init__(self, server_address, handler_class, aggregator, prefix=None):
        super().__init__(server_address, handler_class)
        self.aggregator = aggregator
        self.prefix = prefix
    
    def record_metric(self, metric: dict):
        """Record a metric with optional prefix."""
        name = metric['name']
        if self.prefix:
            name = f"{self.prefix}.{name}"
        
        value = metric['value']
        metric_type = metric['type']
        
        if metric_type == 'counter':
            self.aggregator.record_counter(name, value, metric.get('sample_rate', 1.0))
        elif metric_type == 'gauge':
            self.aggregator.record_gauge(name, value, metric.get('delta', False))
        elif metric_type == 'timer':
            self.aggregator.record_timer(name, value)
        elif metric_type == 'histogram':
            self.aggregator.record_histogram(name, value)


class StatsdServer:
    """
    Main StatSD server that handles UDP and TCP connections,
    aggregates metrics, and flushes to a remote endpoint.
    """
    
    def __init__(
        self,
        listen_host: str = '0.0.0.0',
        listen_port: int = 8125,
        remote_host: str = None,
        remote_port: int = 443,
        secret: str = None,
        prefix: Optional[str] = None,
        flush_interval: float = 10.0
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.secret = secret
        self.prefix = prefix
        self.flush_interval = flush_interval
        
        self.aggregator = MetricAggregator()
        
        self.udp_server = None
        self.tcp_server = None
        self.flush_thread = None
        self.running = False
        
        # Import here to avoid circular dependency
        self._http_session = None
    
    def _get_http_session(self):
        """Lazily create HTTP session."""
        if self._http_session is None:
            import requests
            self._http_session = requests.Session()
        return self._http_session
    
    def _flush_metrics(self):
        """Flush aggregated metrics to the remote endpoint."""
        metrics = self.aggregator.flush()
        
        # Check if there are any metrics to send
        has_metrics = any(
            len(v) > 0 if isinstance(v, (dict, list)) else v
            for v in metrics.values()
        )
        
        if not has_metrics:
            logger.debug("No metrics to flush")
            return
        
        # Get all metric names for logging
        metric_names = set()
        for group in ['counters', 'gauges', 'timers', 'histograms']:
            metric_names.update(metrics.get(group, {}).keys())
        
        if metric_names:
            logger.info(f"Flushing {len(metric_names)} metrics: {sorted(metric_names)}")
        
        # Remove empty groups
        metrics = {k: v for k, v in metrics.items() if v}
        
        if not metrics:
            return
        
        # Send to remote
        if not self.remote_host:
            logger.warning("No remote host configured, metrics logged but not forwarded")
            return
        
        try:
            scheme = 'https' if self.remote_port == 443 else 'http'
            url = f"{scheme}://{self.remote_host}:{self.remote_port}/http"
            
            session = self._get_http_session()
            response = session.post(
                url=url,
                json=metrics,
                auth=(self.secret, '') if self.secret else None,
                timeout=10
            )
            
            if response.status_code >= 400:
                logger.error(f"Failed to send metrics: HTTP {response.status_code}")
            else:
                logger.debug(f"Successfully flushed metrics to {url}")
                
        except Exception as e:
            logger.error(f"Error sending metrics to remote: {e}")
    
    def _flush_loop(self):
        """Background thread that flushes metrics periodically."""
        logger.info(f"Flush thread started, interval: {self.flush_interval}s")
        
        while self.running:
            time.sleep(self.flush_interval)
            if self.running:
                try:
                    self._flush_metrics()
                except Exception as e:
                    logger.error(f"Error in flush loop: {e}")
    
    def start(self):
        """Start the StatSD server (UDP + TCP listeners and flush thread)."""
        if self.running:
            logger.warning("Server already running")
            return
        
        self.running = True
        
        # Start UDP server
        try:
            self.udp_server = ThreadedUDPServer(
                (self.listen_host, self.listen_port),
                UDPHandler,
                self.aggregator,
                self.prefix
            )
            udp_thread = threading.Thread(target=self.udp_server.serve_forever)
            udp_thread.daemon = True
            udp_thread.start()
            logger.info(f"UDP server started on {self.listen_host}:{self.listen_port}")
        except Exception as e:
            logger.error(f"Failed to start UDP server: {e}")
            raise
        
        # Start TCP server
        try:
            self.tcp_server = ThreadedTCPServer(
                (self.listen_host, self.listen_port),
                TCPHandler,
                self.aggregator,
                self.prefix
            )
            tcp_thread = threading.Thread(target=self.tcp_server.serve_forever)
            tcp_thread.daemon = True
            tcp_thread.start()
            logger.info(f"TCP server started on {self.listen_host}:{self.listen_port}")
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            # Clean up UDP server if TCP fails
            if self.udp_server:
                self.udp_server.shutdown()
            raise
        
        # Start flush thread
        self.flush_thread = threading.Thread(target=self._flush_loop)
        self.flush_thread.daemon = True
        self.flush_thread.start()
        
        logger.info(f"StatSD server started. Forwarding to {self.remote_host}:{self.remote_port}")
    
    def stop(self):
        """Stop the StatSD server."""
        logger.info("Stopping StatSD server...")
        self.running = False
        
        # Final flush
        try:
            self._flush_metrics()
        except Exception as e:
            logger.error(f"Error during final flush: {e}")
        
        if self.udp_server:
            self.udp_server.shutdown()
            
        if self.tcp_server:
            self.tcp_server.shutdown()
        
        if self._http_session:
            self._http_session.close()
        
        logger.info("StatSD server stopped")
    
    def run_forever(self):
        """Run the server until interrupted."""
        self.start()
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


class StatsServerSettings(SettingsDefinition):
    """Configuration settings for the StatSD server."""
    
    listen_host = Setting(str, default='0.0.0.0')
    listen_port = Setting(int, default=8125)
    remote_host = Setting(str, required=True)
    remote_port = Setting(int, default=443)
    secret = Setting(str, required=False, default=None)
    prefix = Setting(str, required=False, default=None)
    flush_interval = Setting(float, default=10.0)
    
    def create_server(self) -> StatsdServer:
        """Create a StatsdServer from these settings."""
        return StatsdServer(
            listen_host=self.listen_host.get(),
            listen_port=self.listen_port.get(),
            remote_host=self.remote_host.get(),
            remote_port=self.remote_port.get(),
            secret=self.secret.get(),
            prefix=self.prefix.get(),
            flush_interval=self.flush_interval.get()
        )


def main():
    """Main entry point for the heare-stats-server command."""
    import sys
    
    logger.info("Starting heare-stats-server...")
    
    try:
        settings = StatsServerSettings.load()
        server = settings.create_server()
        server.run_forever()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
