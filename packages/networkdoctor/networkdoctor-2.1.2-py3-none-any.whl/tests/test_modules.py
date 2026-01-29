"""Tests for doctor modules"""
import pytest


def test_dns_doctor():
    """Test DNS doctor"""
    from networkdoctor.modules.dns_doctor import DNSDoctor
    doctor = DNSDoctor()
    assert doctor is not None


def test_firewall_detector():
    """Test firewall detector"""
    from networkdoctor.modules.firewall_detector import FirewallDetector
    detector = FirewallDetector()
    assert detector is not None







