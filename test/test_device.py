from typing import Any, Dict
import mimesis
import pytest

from NetworkCommander.device import Device


class TestDevice:
    @pytest.mark.parametrize(("device", "expected_ssh_string"), [
        (
                Device("", "Camila", "12345", "asda", "1", 123),
                "Camila@asda:123"
        ),
        (
                Device("lsdj1", "Iven", "12345", "asda", "1", 123),
                "Iven@asda:123"
        ),
        (
                Device("", "h3lp", "12345", "asda", "None", 123),
                "h3lp@asda:123"
        ),
        (
                Device("", "123", "12345", "asda", "1"),
                "123@asda"
        ),
        (
                Device("", "Camila", "12345", "asda", "1", 123),
                "Camila@asda:123"
        ),
    ]
                             )
    def test_get_ssh_string(self, device: Device, expected_ssh_string: str):
        assert device.get_ssh_string() == expected_ssh_string

    @pytest.mark.parametrize(("device", "expected_string"), [
        (
                Device("", "Camila", "12345", "asda", "1", 123),
                "(1) -> Camila@asda:123"
        ),
        (
                Device("lsdj1", "Iven", "12345", "asda", "1", 123),
                "lsdj1(1) -> Iven@asda:123"
        ),
        (
                Device("", "h3lp", "12345", "asda", "None", 123),
                "(None) -> h3lp@asda:123"
        ),
        (
                Device("hello", "123", "12345", "asda", "device"),
                "hello(device) -> 123@asda"
        ),
        (
                Device("", "Camila", "12345", "asda", "", 123),
                "Camila@asda:123"
        ),
        (
                Device("", "Camila", "12345", "asda", ""),
                "Camila@asda"
        ),
    ]
                             )
    def test_str_conversion(self, device: Device, expected_string: str):
        assert str(device) == expected_string

    @pytest.mark.parametrize(
        ("device1", "device2"),
        [
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "133", 'soijda1', "135o", "aa1")
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("123", "133", 'soijda1', "135o", "aa1", 123)
            ),
        ]
    )
    def test_eq(self, device1: Device, device2: Device):
        assert device1 == device2

    @pytest.mark.parametrize(
        ("device1", "device2"),
        [
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "133", 'soijda1', "135o", "aa"),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("123", "133", 'soijda1', "135o", "aa", 123),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "133", 'soijda1', "135", "aa1"),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("123", "133", 'soijda1', "135", "aa1", 123),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "133", 'soijda', "135o", "aa1"),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("123", "133", 'soijda', "135o", "aa1", 123),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("123", "13", 'soijda1', "135o", "aa1"),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("123", "13", 'soijda1', "135o", "aa1", 123),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1"),
                    Device("12", "133", 'soijda1', "135o", "aa1"),
            ),
            (
                    Device("123", "133", 'soijda1', "135o", "aa1", 123),
                    Device("12", "133", 'soijda1', "135o", "aa1", 123),
            )
        ]
    )
    def test_un_eq(self, device1: Device, device2: Device):
        assert device1 != device2

    @pytest.mark.parametrize(
        ("json", "expected_device"),
        [
            (
                    {
                        "name": "123",
                        "username": "133",
                        "password": 'soijda1',
                        "host": "135o",
                        "device_type": "aa1"
                    },
                    Device("123", "133", 'soijda1', "135o", "aa1"),
            ),
            (
                    {
                        "name": ";lkdfs",
                        "username": "133",
                        "password": '132okdlkf',
                        "host": "135o",
                        "device_type": "aa1",
                        "port": 123
                    },
                    Device(";lkdfs", "133", '132okdlkf', "135o", "aa1", 123),
            )
        ]
    )
    def test_dict_conversion(self, json: Dict[str, Any], expected_device: Device):
        assert Device(**json) == expected_device
