
import unittest
from hpe_storage_flowkit.src.workflows.cpg import CPGWorkflow

class MockHTTPClient:
	def post(self, endpoint, payload):
		return {"status": "created", "payload": payload}
	def delete(self, endpoint):
		return {"status": "deleted", "endpoint": endpoint}
	def get(self, endpoint):
		if endpoint == "/cpgs":
			return {"members": ["cpg1", "cpg2"]}
		return {"status": "fetched", "endpoint": endpoint}

class TestCPGWorkflow(unittest.TestCase):
	def setUp(self):
		self.workflow = CPGWorkflow(MockHTTPClient())

	def test_create_cpg_success(self):
		result = self.workflow.create_cpg("cpg1", {"domain": "test"})
		self.assertEqual(result["status"], "created")
		self.assertEqual(result["payload"]["name"], "cpg1")

	def test_create_cpg_invalid_name(self):
		with self.assertRaises(ValueError):
			self.workflow.create_cpg("", {"domain": "test"})

	def test_delete_cpg(self):
		result = self.workflow.delete_cpg("cpg1")
		self.assertEqual(result["status"], "deleted")

	def test_get_cpg(self):
		result = self.workflow.get_cpg("cpg1")
		self.assertEqual(result["status"], "fetched")

	def test_list_cpgs(self):
		result = self.workflow.list_cpgs()
		self.assertIn("cpg1", result)
		self.assertIn("cpg2", result)

if __name__ == "__main__":
	unittest.main()
