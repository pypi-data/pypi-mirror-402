from __future__ import annotations

import warnings

from django.test import TestCase
from django.test import override_settings

from django_qstash.settings import DJANGO_QSTASH_WEBHOOK_PATH


class SettingsTestCase(TestCase):
    def test_default_webhook_path(self):
        """Test that default webhook path is set correctly"""
        self.assertEqual(DJANGO_QSTASH_WEBHOOK_PATH, "/qstash/webhook/")

    def test_warning_when_required_settings_missing(self):
        """Test that warning is raised when required settings are missing"""
        with override_settings(QSTASH_TOKEN=None, DJANGO_QSTASH_DOMAIN=None):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Force reload of settings to trigger warning
                from importlib import reload

                import django_qstash.settings

                reload(django_qstash.settings)

                self.assertEqual(len(w), 1)
                self.assertTrue(issubclass(w[0].category, RuntimeWarning))
                self.assertIn(
                    "QSTASH_TOKEN and DJANGO_QSTASH_DOMAIN should be set",
                    str(w[0].message),
                )

    @override_settings(QSTASH_TOKEN="test-token", DJANGO_QSTASH_DOMAIN="example.com")
    def test_no_warning_when_settings_present(self):
        """Test that no warning is raised when required settings are present"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Force reload of settings
            from importlib import reload

            import django_qstash.settings

            reload(django_qstash.settings)

            self.assertEqual(len(w), 0)

    @override_settings(DJANGO_QSTASH_WEBHOOK_PATH="/custom/webhook/path/")
    def test_custom_webhook_path(self):
        """Test that custom webhook path can be set"""
        # Force reload of settings to get new webhook path
        from importlib import reload

        import django_qstash.settings

        reload(django_qstash.settings)

        self.assertEqual(
            django_qstash.settings.DJANGO_QSTASH_WEBHOOK_PATH, "/custom/webhook/path/"
        )
