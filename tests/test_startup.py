"""Exercise startup and SDK requests without contacting Rootly or Glean."""

import copy
import importlib
import json
import unittest
from unittest.mock import patch

import httpx
from glean.api_client import Glean

from config import config_manager


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(
            config_manager,
            "_load_secrets",
            return_value={"GLEAN_API_TOKEN": "test-glean", "ROOTLY_API_TOKEN": "test-rootly"},
        ):
            cls.app = importlib.import_module("app")

    def test_retrospective_helpers_are_exported(self):
        from data_fetchers import fetch_retrospectives
        from document_mappers import retrospective_to_doc

        self.assertTrue(callable(fetch_retrospectives))
        self.assertTrue(callable(retrospective_to_doc))

    def test_datasource_registration_uses_sdk_arguments(self):
        requests = []

        def handle(request):
            requests.append(request)
            return httpx.Response(200, json={})

        with (
            httpx.Client(transport=httpx.MockTransport(handle)) as http_client,
            Glean(api_token="test-glean", server_url="https://glean.invalid", client=http_client) as client,
        ):
            self.app.ensure_datasource(client)

        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(str(request.url), "https://glean.invalid/api/index/v1/adddatasource")
        payload = json.loads(request.content)
        self.assertEqual(payload["name"], self.app.config.glean.datasource_name)
        self.assertEqual(payload["displayName"], self.app.config.glean.display_name)
        self.assertEqual(payload["datasourceCategory"], "TICKETS")
        self.assertEqual(payload["aliases"], ["rootly"])
        self.assertEqual(
            {definition["name"] for definition in payload["objectDefinitions"]},
            {"Incident", "Alert", "Schedule", "EscalationPolicy", "Retrospective"},
        )

    def test_retrospective_reaches_indexing_payload(self):
        from processors import SyncCoordinator

        coordinator = SyncCoordinator()
        fixture = {"id": "retro-1", "attributes": {"title": "Test retrospective", "summary": "What we learned"}}
        for name, settings in coordinator.data_type_configs.items():
            settings["fetcher"] = lambda **kwargs: []
            settings["config"] = copy.copy(settings["config"])
            settings["config"].enabled = name == "retrospectives"
        coordinator.data_type_configs["retrospectives"]["fetcher"] = lambda **kwargs: [fixture]
        results, documents = coordinator.sync_all_data_types()
        self.assertEqual(results["retrospectives"]["status"], "success")
        self.assertEqual(results["summary"]["total_documents"], 1)

        requests = []

        def handle(request):
            requests.append(request)
            return httpx.Response(200, json={})

        with (
            httpx.Client(transport=httpx.MockTransport(handle)) as http_client,
            Glean(api_token="test-glean", server_url="https://glean.invalid", client=http_client) as client,
        ):
            client.indexing.documents.index(datasource=self.app.config.glean.datasource_name, documents=documents)

        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(str(request.url), "https://glean.invalid/api/index/v1/indexdocuments")
        document = json.loads(request.content)["documents"][0]
        self.assertEqual(document["id"], "retro-1")
        self.assertEqual(document["objectType"], "Retrospective")
        self.assertIn("What we learned", document["body"]["textContent"])


if __name__ == "__main__":
    unittest.main()
