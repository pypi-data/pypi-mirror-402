import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the parent directory of linkgo to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from linkgo.linkgo.linkgo import run_link_finder # Import the function to be tested

class TestLinkGo(unittest.TestCase):

    def setUp(self):
        self.mock_ddgs_text_patch = patch('linkgo.linkgo.linkgo.DDGS')
        self.mock_ddgs_class = self.mock_ddgs_text_patch.start()
        self.mock_ddgs_instance = self.mock_ddgs_class.return_value.__enter__.return_value
        self.mock_ddgs_text = self.mock_ddgs_instance.text

        # No aiohttp.ClientSession patching here, we'll patch 'fetch' directly
        # self.mock_aiohttp_session_patch = patch('linkgo.linkgo.linkgo.aiohttp.ClientSession')
        # self.mock_aiohttp_session_class = self.mock_aiohttp_session_patch.start()
        # self.mock_aiohttp_session_instance = AsyncMock()
        # self.mock_aiohttp_session_class.return_value.__aenter__.return_value = self.mock_aiohttp_session_instance
        # self.mock_aiohttp_session_class.return_value.__aexit__.return_value = None


    def tearDown(self):
        self.mock_ddgs_text_patch.stop()
        # self.mock_aiohttp_session_patch.stop() # Removed
        # Clean up the output file if it exists
        output_file = "test_output.txt"
        if os.path.exists(output_file):
            os.remove(output_file)

    async def _run_test_case(self, ddgs_return_value, expected_search_results, expected_num_links):
        self.mock_ddgs_text.return_value = ddgs_return_value

        # Patch the fetch function directly
        with patch('linkgo.linkgo.linkgo.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "<html><body><a href='http://example.com/found'>Found Link</a></body></html>"

            # Use a temporary file for output
            output_file = "test_output.txt"
            if os.path.exists(output_file):
                os.remove(output_file)

            await run_link_finder("test query", output_file)

            # Verify calls to fetch
            if expected_search_results:
                expected_calls = [unittest.mock.call(unittest.mock.ANY, url) for url in expected_search_results]
                mock_fetch.assert_has_calls(expected_calls, any_order=True)
                self.assertEqual(mock_fetch.call_count, len(expected_search_results))
            else:
                mock_fetch.assert_not_called()

            # Verify the output file content
            if expected_num_links > 0:
                self.assertTrue(os.path.exists(output_file))
                with open(output_file, 'r') as f:
                    content = f.read()
                    self.assertIn("http://example.com/found", content)
            else:
                self.assertTrue(os.path.exists(output_file))
                with open(output_file, 'r') as f:
                    self.assertEqual(f.read(), "")

    def test_ddgs_returns_empty_list(self):
        asyncio.run(self._run_test_case([], [], 0))

    def test_ddgs_returns_single_result(self):
        ddgs_return = [{'href': 'http://single.com/result', 'title': 'Single'}]
        expected_search_results = ['http://single.com/result']
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 1))

    def test_ddgs_returns_multiple_results(self):
        ddgs_return = [
            {'href': 'http://multi1.com/result', 'title': 'Multi1'},
            {'href': 'http://multi2.com/result', 'title': 'Multi2'}
        ]
        expected_search_results = ['http://multi1.com/result', 'http://multi2.com/result']
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 2)) # Changed from 1 to 2

    def test_ddgs_returns_results_with_missing_href(self):
        ddgs_return = [
            {'href': 'http://valid.com', 'title': 'Valid'},
            {'title': 'NoHref'}, # Missing href
            {'href': 'http://another.com', 'title': 'Another'}
        ]
        expected_search_results = ['http://valid.com', 'http://another.com']
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 2)) # Changed from 1 to 2

    def test_ddgs_returns_results_with_none_href(self):
        ddgs_return = [
            {'href': 'http://valid.com', 'title': 'Valid'},
            {'href': None, 'title': 'NoneHref'}, # None href
            {'href': 'http://another.com', 'title': 'Another'}
        ]
        expected_search_results = ['http://valid.com', 'http://another.com']
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 2)) # Changed from 1 to 2

    def test_ddgs_returns_malformed_items(self):
        ddgs_return = [
            {'href': 'http://valid.com', 'title': 'Valid'},
            None, # Malformed item
            {'href': 'http://another.com', 'title': 'Another'}
        ]
        expected_search_results = ['http://valid.com', 'http://another.com']
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 2)) # Changed from 1 to 2

    def test_ddgs_returns_non_list_type(self):
        # This case is unlikely based on docs but tests robustness
        ddgs_return = MagicMock() # Mock it as a non-list
        ddgs_return.__iter__.return_value = [{'href': 'http://mocked.com'}]
        expected_search_results = [] # Should be empty because isinstance(raw_search_results, list) will be false
        asyncio.run(self._run_test_case(ddgs_return, expected_search_results, 0))


if __name__ == '__main__':
    unittest.main()