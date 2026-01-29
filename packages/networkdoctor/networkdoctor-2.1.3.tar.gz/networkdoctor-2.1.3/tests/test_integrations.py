"""Tests for integrations"""
import pytest


def test_prometheus_exporter():
    """Test Prometheus exporter"""
    from networkdoctor.integrations.prometheus_exporter import PrometheusExporter
    exporter = PrometheusExporter()
    assert exporter is not None








