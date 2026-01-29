"""Tests for CLI"""
import pytest
from networkdoctor.cli.parser import parse_args
from networkdoctor.cli.validator import validate_target


def test_parse_args():
    """Test argument parsing"""
    args = parse_args(["example.com"])
    assert args.targets == ["example.com"]


def test_validate_target():
    """Test target validation"""
    host, port, protocol = validate_target("example.com")
    assert host == "example.com"
    assert port == 80











