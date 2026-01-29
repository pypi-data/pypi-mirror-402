"""
Adaptive-K Observability Module

Provides production-ready monitoring, metrics, and debugging tools.

Components:
- MetricsCollector: Prometheus-compatible metrics
- AdaptiveKLogger: Structured JSON logging
- AdaptiveKTracer: Inference tracing with detailed layer metrics
- AdaptiveKDebugger: Debug visualization tools

Usage:
    from adaptive_k.observability import get_metrics, get_logger, get_tracer

    # Metrics
    metrics = get_metrics()
    metrics.record_inference(trace)
    metrics.start_http_server(9090)  # Prometheus endpoint

    # Logging
    logger = get_logger("my_service")
    logger.log_inference(trace)

    # Tracing
    tracer = get_tracer()
    @tracer.trace_inference
    def my_inference():
        pass
"""

import time
import json
import logging
from functools import wraps
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import threading

# Optional dependencies
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


@dataclass
class InferenceTrace:
    """Single inference trace record"""
    request_id: str
    timestamp: float
    latency_ms: float
    avg_k: float
    compute_saved_pct: float
    k_distribution: Dict[int, int] = field(default_factory=dict)
    layer_entropies: List[float] = field(default_factory=list)
    used_fallback: bool = False
    error: Optional[str] = None


@dataclass
class LayerTrace:
    """Per-layer trace"""
    layer_idx: int
    entropy_mean: float
    entropy_std: float
    k_selected: int
    experts_used: int
    latency_ms: float


class MetricsCollector:
    """
    Thread-safe metrics collector with optional Prometheus export.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        
        self._counters: Dict[str, int] = defaultdict(int)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}
        
        self._prom_metrics = {}
        if HAS_PROMETHEUS:
            self._init_prometheus()
    
    def _init_prometheus(self):
        self._prom_metrics['inferences_total'] = Counter(
            'adaptive_k_inferences_total', 'Total inferences', ['mode']
        )
        self._prom_metrics['latency'] = Histogram(
            'adaptive_k_latency_seconds', 'Inference latency',
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
        )
        self._prom_metrics['avg_k'] = Histogram(
            'adaptive_k_avg_k', 'Average K per inference',
            buckets=[1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8]
        )
        self._prom_metrics['compute_saved'] = Histogram(
            'adaptive_k_compute_saved_ratio', 'Compute saved (0-1)',
            buckets=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        )
        self._prom_metrics['fallback_total'] = Counter(
            'adaptive_k_fallback_total', 'Fallbacks to full-K'
        )
    
    def record_inference(self, trace: InferenceTrace):
        """Record inference metrics"""
        mode = 'fallback' if trace.used_fallback else 'adaptive'
        
        with self._lock:
            self._counters[f'inferences_{mode}'] += 1
            self._histograms['latency'].append(trace.latency_ms / 1000)
            self._histograms['avg_k'].append(trace.avg_k)
            self._histograms['compute_saved'].append(trace.compute_saved_pct / 100)
            
            if trace.used_fallback:
                self._counters['fallback'] += 1
        
        if HAS_PROMETHEUS:
            self._prom_metrics['inferences_total'].labels(mode=mode).inc()
            self._prom_metrics['latency'].observe(trace.latency_ms / 1000)
            self._prom_metrics['avg_k'].observe(trace.avg_k)
            self._prom_metrics['compute_saved'].observe(trace.compute_saved_pct / 100)
            if trace.used_fallback:
                self._prom_metrics['fallback_total'].inc()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        with self._lock:
            latencies = self._histograms.get('latency', [])
            total = sum(v for k, v in self._counters.items() if k.startswith('inferences_'))
            
            return {
                'total_inferences': total,
                'latency': {
                    'mean': sum(latencies) / len(latencies) if latencies else 0,
                    'p50': sorted(latencies)[len(latencies)//2] if latencies else 0,
                    'p99': sorted(latencies)[int(len(latencies)*0.99)] if len(latencies) > 1 else (latencies[0] if latencies else 0),
                },
                'avg_k': {'mean': sum(self._histograms.get('avg_k', [0])) / max(1, len(self._histograms.get('avg_k', [1])))},
                'compute_saved': {'mean': sum(self._histograms.get('compute_saved', [0])) / max(1, len(self._histograms.get('compute_saved', [1])))},
                'fallback_rate': self._counters.get('fallback', 0) / max(1, total)
            }
    
    def start_http_server(self, port: int = 9090):
        """Start Prometheus metrics endpoint"""
        if HAS_PROMETHEUS:
            start_http_server(port)
            logging.info(f"Prometheus metrics on port {port}")
        else:
            logging.warning("prometheus_client not installed")
    
    def reset(self):
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()


class AdaptiveKLogger:
    """Structured JSON logger"""
    
    def __init__(self, component: str = "adaptive_k", json_format: bool = True):
        self.component = component
        self.json_format = json_format
        self._configure()
    
    def _configure(self):
        handler = logging.StreamHandler()
        if self.json_format:
            fmt = '{"ts": "%(asctime)s", "level": "%(levelname)s", "component": "%(name)s", "msg": "%(message)s"}'
        else:
            fmt = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        handler.setFormatter(logging.Formatter(fmt))
        
        self.logger = logging.getLogger(self.component)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _log(self, level: str, event: str, **kwargs):
        msg = f"{event} | {json.dumps(kwargs)}" if kwargs else event
        getattr(self.logger, level)(msg)
    
    def info(self, event: str, **kwargs): self._log('info', event, **kwargs)
    def debug(self, event: str, **kwargs): self._log('debug', event, **kwargs)
    def warning(self, event: str, **kwargs): self._log('warning', event, **kwargs)
    def error(self, event: str, **kwargs): self._log('error', event, **kwargs)
    
    def log_inference(self, trace: InferenceTrace):
        self.info("inference_completed",
                  request_id=trace.request_id,
                  latency_ms=trace.latency_ms,
                  avg_k=trace.avg_k,
                  compute_saved_pct=trace.compute_saved_pct)


class AdaptiveKTracer:
    """Inference tracing decorator"""
    
    def __init__(self, enable_detailed: bool = False):
        self.enable_detailed = enable_detailed
        self.metrics = MetricsCollector()
        self.logger = AdaptiveKLogger()
    
    def trace_inference(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import uuid
            request_id = str(uuid.uuid4())[:8]
            start = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                latency = (time.perf_counter() - start) * 1000
                
                avg_k = result.get('avg_k', 0) if isinstance(result, dict) else 0
                compute_saved = result.get('compute_saved', 0) if isinstance(result, dict) else 0
                
                trace = InferenceTrace(
                    request_id=request_id,
                    timestamp=time.time(),
                    latency_ms=latency,
                    avg_k=avg_k,
                    compute_saved_pct=compute_saved,
                    k_distribution={}
                )
                self.metrics.record_inference(trace)
                self.logger.log_inference(trace)
                return result
            except Exception as e:
                self.logger.error("inference_failed", request_id=request_id, error=str(e))
                raise
        return wrapper


class AdaptiveKDebugger:
    """Debug visualization tools"""
    
    def __init__(self):
        self.trace_history: List[Dict] = []
        self.verbose = False
    
    def enable_verbose(self):
        self.verbose = True
        logging.getLogger("adaptive_k").setLevel(logging.DEBUG)
    
    def trace_k_selection(self, entropies: List[float], thresholds: List[float], 
                          k_values: List[int]) -> Dict:
        k_selections = []
        for h in entropies:
            k = k_values[-1]
            for i, t in enumerate(thresholds):
                if h < t:
                    k = k_values[i]
                    break
            k_selections.append(k)
        
        import statistics
        trace = {
            'avg_k': statistics.mean(k_selections) if k_selections else 0,
            'k_distribution': {k: k_selections.count(k) for k in set(k_selections)},
            'entropy_stats': {
                'min': min(entropies) if entropies else 0,
                'max': max(entropies) if entropies else 0,
                'mean': statistics.mean(entropies) if entropies else 0
            }
        }
        self.trace_history.append(trace)
        
        if self.verbose:
            print(f"K Selection: avg={trace['avg_k']:.2f}, dist={trace['k_distribution']}")
        
        return trace
    
    def visualize_layers(self, layer_traces: List[LayerTrace]):
        print("=" * 50)
        print("LAYER TRACE")
        print("=" * 50)
        for lt in layer_traces:
            bar = "█" * int(lt.entropy_mean * 15)
            print(f"L{lt.layer_idx:2d} | H={lt.entropy_mean:.3f} {bar:15s} | K={lt.k_selected}")
        print("=" * 50)


# Factory functions
def get_metrics() -> MetricsCollector:
    return MetricsCollector()

def get_logger(component: str = "adaptive_k") -> AdaptiveKLogger:
    return AdaptiveKLogger(component)

def get_tracer(enable_detailed: bool = False) -> AdaptiveKTracer:
    return AdaptiveKTracer(enable_detailed)

def get_debugger() -> AdaptiveKDebugger:
    return AdaptiveKDebugger()


__all__ = [
    'InferenceTrace',
    'LayerTrace', 
    'MetricsCollector',
    'AdaptiveKLogger',
    'AdaptiveKTracer',
    'AdaptiveKDebugger',
    'get_metrics',
    'get_logger',
    'get_tracer',
    'get_debugger',
]
