"""Tests for core modules"""
import pytest
from networkdoctor.core.scanner import NetworkScanner
from networkdoctor.core.analyzer import NetworkAnalyzer


def test_scanner_initialization():
    """Test scanner initialization"""
    scanner = NetworkScanner()
    assert scanner is not None


def test_analyzer_initialization():
    """Test analyzer initialization"""
    analyzer = NetworkAnalyzer()
    assert analyzer is not None








