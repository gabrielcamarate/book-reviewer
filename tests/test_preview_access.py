from __future__ import annotations

import unittest

from editorial_core.preview_access import (
    ensure_preview_access_configuration,
    is_preview_request_authorized,
)


class PreviewAccessTest(unittest.TestCase):
    def test_ensure_preview_access_configuration_allows_localhost_without_token(self) -> None:
        ensure_preview_access_configuration(host="127.0.0.1", preview_token=None)

    def test_ensure_preview_access_configuration_requires_token_for_non_local_bind(self) -> None:
        with self.assertRaises(ValueError):
            ensure_preview_access_configuration(host="0.0.0.0", preview_token=None)

    def test_is_preview_request_authorized_allows_loopback_without_token(self) -> None:
        self.assertTrue(
            is_preview_request_authorized(
                client_host="127.0.0.1",
                authorization_header=None,
                preview_token=None,
                path="/",
            )
        )

    def test_is_preview_request_authorized_requires_matching_token_for_remote_client(self) -> None:
        self.assertFalse(
            is_preview_request_authorized(
                client_host="203.0.113.10",
                authorization_header=None,
                preview_token="segredo-preview",
                path="/",
            )
        )
        self.assertTrue(
            is_preview_request_authorized(
                client_host="203.0.113.10",
                authorization_header="Bearer segredo-preview",
                preview_token="segredo-preview",
                path="/",
            )
        )

    def test_is_preview_request_authorized_keeps_healthz_open_for_remote_probe(self) -> None:
        self.assertTrue(
            is_preview_request_authorized(
                client_host="203.0.113.10",
                authorization_header=None,
                preview_token="segredo-preview",
                path="/healthz",
            )
        )
