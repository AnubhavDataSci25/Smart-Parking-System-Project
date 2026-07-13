"""
Unit tests for the input validation rules. Run with:
  python3 -m unittest discover -s backend/tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validation import validate_vehicle_number, validate_owner_name, validate_vehicle_type, validate_entry_payload


class TestValidateVehicleNumber(unittest.TestCase):
    def test_valid_plate_accepted(self):
        ok, _ = validate_vehicle_number("PB08AB1234")
        self.assertTrue(ok)

    def test_empty_rejected(self):
        ok, msg = validate_vehicle_number("")
        self.assertFalse(ok)
        self.assertIn("required", msg)

    def test_too_short_rejected(self):
        ok, _ = validate_vehicle_number("AB1")
        self.assertFalse(ok)

    def test_special_characters_rejected(self):
        ok, _ = validate_vehicle_number("PB08-AB@1234")
        self.assertFalse(ok)

    def test_lowercase_input_normalized_and_accepted(self):
        # validate_vehicle_number normalizes case internally (defense in
        # depth), so lowercase input is still accepted.
        ok, _ = validate_vehicle_number("pb08ab1234")
        self.assertTrue(ok)


class TestValidateOwnerName(unittest.TestCase):
    def test_valid_name_accepted(self):
        ok, _ = validate_owner_name("Aman Sharma")
        self.assertTrue(ok)

    def test_hyphenated_name_accepted(self):
        ok, _ = validate_owner_name("Anne-Marie O'Brien")
        self.assertTrue(ok)

    def test_empty_rejected(self):
        ok, _ = validate_owner_name("")
        self.assertFalse(ok)

    def test_digits_rejected(self):
        ok, _ = validate_owner_name("Owner123")
        self.assertFalse(ok)

    def test_single_character_rejected(self):
        ok, _ = validate_owner_name("A")
        self.assertFalse(ok)


class TestValidateVehicleType(unittest.TestCase):
    def test_all_known_types_accepted(self):
        for t in ("Car", "Bike", "Truck", "Other"):
            ok, _ = validate_vehicle_type(t)
            self.assertTrue(ok, f"{t} should be valid")

    def test_unknown_type_rejected(self):
        ok, _ = validate_vehicle_type("Spaceship")
        self.assertFalse(ok)

    def test_wrong_case_rejected(self):
        ok, _ = validate_vehicle_type("car")  # must be title-case "Car"
        self.assertFalse(ok)


class TestValidateEntryPayload(unittest.TestCase):
    def test_all_valid_passes(self):
        ok, _ = validate_entry_payload("PB08AB1234", "Aman Sharma", "Car")
        self.assertTrue(ok)

    def test_first_invalid_field_reported(self):
        ok, msg = validate_entry_payload("", "Aman Sharma", "Car")
        self.assertFalse(ok)
        self.assertIn("Vehicle number", msg)


if __name__ == "__main__":
    unittest.main()
