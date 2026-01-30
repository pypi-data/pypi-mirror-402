#!/usr/bin/env python3

"""Unit tests for skilleter_readable.readable."""

import io
import sys
import types
import unittest

import skilleter_readable.readable as readable


class _StubTidy:
	"""Lightweight stand-in for tidy helpers used in tests."""

	@staticmethod
	def debug_format(text):
		return text

	@staticmethod
	def convert_ansi(text, _light):
		return text

	@staticmethod
	def remove_ansi(text):
		return text

	@staticmethod
	def remove_sha256(text):
		return text

	@staticmethod
	def remove_sha1(text):
		return text

	@staticmethod
	def remove_times(text):
		return text

	@staticmethod
	def remove_speeds(text):
		return text

	@staticmethod
	def remove_aws_ids(text):
		return text

	@staticmethod
	def regex_replace(text, _replacements):
		return text


class CleanfileTests(unittest.TestCase):
	def setUp(self):
		self._orig_tidy = readable.tidy
		readable.tidy = _StubTidy()

	def tearDown(self):
		readable.tidy = self._orig_tidy

	def test_collection_flushes_at_eof(self):
		args = types.SimpleNamespace(
			debug=False,
			light=False,
			dark=False,
			none=False,
			tidy=False,
			aws=False,
			replace=False,
			regex_replace=[],
			minimal=True,
			terraform=True,
			strip_blank=False,
		)

		src = io.StringIO('Fetching tool 1.0\n')
		dst = io.StringIO()

		readable.cleanfile(args, src, dst)

		self.assertEqual(dst.getvalue(), 'Fetching tool 1.0\n')


class ParseCommandLineTests(unittest.TestCase):
	def _run_with_argv(self, argv):
		old_argv = sys.argv
		try:
			sys.argv = argv
			return readable.parse_command_line()
		finally:
			sys.argv = old_argv

	def test_replace_allows_equals_in_replacement(self):
		args = self._run_with_argv(['prog', '--replace', 'foo=bar=baz'])
		self.assertEqual(args.regex_replace[0]['replace'], 'bar=baz')

	def test_minimal_implies_terraform(self):
		args = self._run_with_argv(['prog', '--minimal'])
		self.assertTrue(args.terraform)


if __name__ == '__main__':
	unittest.main()
