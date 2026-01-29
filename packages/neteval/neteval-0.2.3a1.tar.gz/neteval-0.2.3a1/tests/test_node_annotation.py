#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `neteval` package."""


import unittest
from neteval.node_annotation import *


class TestNetevalrunner(unittest.TestCase):
    """Tests for `neteval` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_parse_chrm(self):
        self.assertEqual(parse_chrm('1'), 1)
        self.assertEqual(parse_chrm('reserved'), 'other')

        

if __name__ == '__main__':
    unittest.main()