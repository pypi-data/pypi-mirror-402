from collections import defaultdict
from typing import Union

import requests
from heare.config import SettingsDefinition, Setting
from statsd import StatsClient, TCPStatsClient
import logging


class PipelineAggregator(object):
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(int)
        self.timers = defaultdict(list)
        self.histograms = defaultdict(list)

    def incr(self, metric_name:str, value:Union[int, float] = 1):
        self.counters[metric_name] += value

    def decr(self, metric_name:str, value: Union[int, float] = 1):
        self.incr(metric_name, -value)

    def hist(self, metric_name:str, value: Union[int, float]):
        self.histograms[metric_name].append(value)

    def time(self, metric_name:str, value: Union[int, float]):
        self.timers[metric_name].append(value)

    def gauge(self, metric_name: str, value: Union[int, float]):
        self.gauges[metric_name] = value


class BaseStatsClient(object):
    def incr(self, metric_name:str, value:Union[int, float] = 1):
        raise NotImplementedError()

    def decr(self, metric_name:str, value: Union[int, float] = 1):
        self.incr(metric_name, -value)

    def hist(self, metric_name:str, value: Union[int, float]):
        raise NotImplementedError()

    def time(self, metric_name:str, value: Union[int, float]):
        raise NotImplementedError()

    def gauge(self, metric_name: str, value: Union[int, float]):
        raise NotImplementedError()

    def pipeline(self):
        raise NotImplementedError()


class UdpClient(BaseStatsClient):
    class Pipeline(PipelineAggregator):
        def __init__(self, client):
            super().__init__()
            self._client = client

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                with self._client.pipeline() as p:
                    for metric, value in self.counters.items():
                        p.incr(metric, value)
                    for metric, value in self.gauges.items():
                        p.gauge(metric, value)
                    for metric, values in self.timers.items():
                        for v in values:
                            p.time(metric, v)
                    for metric, values in self.histograms.items():
                        for v in values:
                            p.time(metric, v)
            except:
                    pass

    def __init__(self, host, port, _, prefix=None):
        self.client = StatsClient(host, port, prefix=prefix)
        self.prefix = prefix

    def pipeline(self):
        return self.client.pipeline()


class TcpClient(BaseStatsClient):
    class Pipeline(PipelineAggregator):
        def __init__(self, client):
            super().__init__()
            self._client = client

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                with self._client.pipeline() as p:
                    for metric, value in self.counters.items():
                        p.incr(metric, value)
                    for metric, value in self.gauges.items():
                        p.gauge(metric, value)
                    for metric, values in self.timers.items():
                        for v in values:
                            p.time(metric, v)
                    for metric, values in self.histograms.items():
                        for v in values:
                            p.time(metric, v)
            except:
                pass

    def __init__(self, host, port, _, prefix=None):
        self.client = TCPStatsClient(host, port, prefix=prefix)

    def incr(self, metric_name: str, value: Union[int, float] = 1):
        pass

    def hist(self, metric_name: str, value: Union[int, float]):
        pass

    def time(self, metric_name: str, value: Union[int, float]):
        pass

    def gauge(self, metric_name: str, value: Union[int, float]):
        pass

    def pipeline(self):
        return TcpClient.Pipeline(self)


class HttpClient(BaseStatsClient):
    class Pipeline(PipelineAggregator):
        def __init__(self, parent, prefix=None):
            super().__init__()
            self.session = parent.session
            self.host = parent.host
            self.port = parent.port
            self.secret = parent.secret
            self.prefix = prefix

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            payload = {
                'counters': self.counters,
                'gauges': self.gauges,
                'timers': self.timers,
                'histograms': self.histograms
            }
            if self.prefix is not None:
                tmp_payload = {
                    'counters': {},
                    'gauges': {},
                    'timers': {},
                    'histograms': {}
                }
                for group in tmp_payload.keys():
                    for k, v in payload[group].items():
                        new_key = '.'.join([self.prefix, k])
                        # handle either prefix with trailing . or without.
                        new_key = new_key.replace('..', '.')
                        tmp_payload[group][new_key] = v
                payload = tmp_payload

            to_delete = [k for k, v in payload.items() if len(v) == 0]
            for key in to_delete:
                del payload[key]

            try:
                scheme = 'https' if self.port == 443 else 'http'
                self.session.post(
                    json=payload,
                    url=f"{scheme}://{self.host}:{self.port}/http",
                    auth=(self.secret, '')
                )
            except Exception as e:
                logging.exception("Error posting to metrics host")

    def __init__(self, host, port, secret, prefix=None):
        self.host = host
        self.port = port
        self.secret = secret
        self.session = requests.Session()
        self.prefix = prefix

    def pipeline(self):
        return HttpClient.Pipeline(self, prefix=self.prefix)


class WsClient(BaseStatsClient):
    def __init__(self, host, port, secret, prefix=None):
        pass


PROTOCOLS = ['udp', 'tcp', 'http', 'ws']


def StatsProtocol(val: str) -> str:
    if val.lower() not in PROTOCOLS:
        raise ValueError(f"{val} is not valid protocol. Select from {PROTOCOLS}")

    return val.lower()


class StatsClientSettings(SettingsDefinition):
    protocol = Setting(StatsProtocol, default='http')
    dest_host = Setting(str)
    dest_port = Setting(int)
    secret = Setting(str, required=False)
    prefix = Setting(str, default=None, required=False)

    client_protocol_factories = {
        'udp': UdpClient,
        'tcp': TcpClient,
        'http': HttpClient,
        'ws': WsClient
    }

    def create_client(self) -> BaseStatsClient:
        factory = self.client_protocol_factories.get(self.protocol.get())
        if factory:
            return factory(
                self.dest_host.get(),
                self.dest_port.get(),
                self.secret.get(),
                prefix=self.prefix.get()
            )
        else:
            raise ValueError(
                f"No factory available for protocol: f{self.protocol.get()}"
            )
