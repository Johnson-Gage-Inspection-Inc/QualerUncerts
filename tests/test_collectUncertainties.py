import unittest
from unittest.mock import patch, MagicMock
from collectUncertainties import (
    driver_get,
    getServiceCapabilities,
    getTechniquesList,
    getUncertaintyBudgets,
    main,
)
import json
import os
import tempfile
import pandas as pd


class TestCollectUncertainties(unittest.TestCase):

    @patch("collectUncertainties.driver")
    @patch("collectUncertainties.login")
    def test_driver_get_relogin(self, mock_login, mock_driver):
        # Mock the driver's current_url to simulate re-login scenario
        mock_driver.current_url = "https://jgiquality.qualer.com/login"

        # Call the function
        driver_get("https://jgiquality.qualer.com/somepage")

        # Check if login was called
        mock_login.assert_called_once()

        # Check if driver.get was called twice (initial call and after re-login)
        self.assertEqual(mock_driver.get.call_count, 2)

    @patch("collectUncertainties.driver")
    def test_driver_get_no_relogin(self, mock_driver):
        # Mock the driver's current_url to simulate no re-login needed
        mock_driver.current_url = "https://jgiquality.qualer.com/somepage"

        # Call the function
        driver_get("https://jgiquality.qualer.com/somepage")

        # Check if driver.login was not called
        mock_driver.get.assert_called_once_with(
            "https://jgiquality.qualer.com/somepage"
        )

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getServiceCapabilities(self, mock_driver, mock_driver_get):
        # Mock the data returned by the driver
        mock_driver.find_element.return_value.text = json.dumps(
            {"views": [{"key1": "value1"}, {"key2": "value2"}]}
        )

        # Call the function
        result = getServiceCapabilities()

        # Check if driver_get was called with the correct URL
        mock_driver_get.assert_called_once_with(
            "https://jgiquality.qualer.com/ServiceType/ServiceCapabilities"
        )

        # Check if the result is as expected
        self.assertEqual(result, [{"key1": "value1"}, {"key2": "value2"}])

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getServiceCapabilities_no_views(self, mock_driver, mock_driver_get):
        # Simulate a JSON response that omits 'views'
        mock_driver.find_element.return_value.text = json.dumps({"wrongKey": []})

        # We expect a KeyError when 'views' is missing
        with self.assertRaises(KeyError):
            getServiceCapabilities()

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getServiceCapabilities_invalid_json(self, mock_driver, mock_driver_get):
        # Simulate invalid JSON
        mock_driver.find_element.return_value.text = "not valid json"

        # We expect a JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            getServiceCapabilities()

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getTechniquesList(self, mock_driver, mock_driver_get):
        # Mock the data returned by the driver
        mock_driver.find_element.return_value.text = json.dumps(
            [
                {"TechniqueId": 1, "Name": "Technique1"},
                {"TechniqueId": 2, "Name": "Technique2"},
            ]
        )

        # Call the function
        result = getTechniquesList()

        # Check if driver_get was called with the correct URL
        mock_driver_get.assert_called_once_with(
            "https://jgiquality.qualer.com/ServiceGroupTechnique/TechniquesList"
        )

        # Check if the result is as expected
        self.assertEqual(
            result,
            [
                {"TechniqueId": 1, "Name": "Technique1"},
                {"TechniqueId": 2, "Name": "Technique2"},
            ],
        )

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getUncertaintyBudgets(self, mock_driver, mock_driver_get):
        # Mock the data returned by the driver
        mock_driver.find_element.return_value.text = json.dumps(
            {
                "Data": [
                    {"BudgetId": 1, "Value": "Budget1"},
                    {"BudgetId": 2, "Value": "Budget2"},
                ]
            }
        )

        # Call the function
        result = getUncertaintyBudgets(1, 1)

        # Check if driver_get was called with the correct URL
        mock_driver_get.assert_called_once_with(
            "https://jgiquality.qualer.com/ServiceGroupTechnique/UncertaintyBudgets?serviceGroupId=1&techniqueId=1"
        )

        # Check if the result is as expected
        self.assertEqual(
            result,
            [
                {"BudgetId": 1, "Value": "Budget1"},
                {"BudgetId": 2, "Value": "Budget2"},
            ],
        )

    @patch("collectUncertainties.driver_get")
    @patch("collectUncertainties.driver")
    def test_getUncertaintyBudgets_missing_data(self, mock_driver, mock_driver_get):
        # Simulate a JSON response that omits 'Data'
        mock_driver.find_element.return_value.text = json.dumps({"OtherKey": []})

        # Expect KeyError when 'Data' is missing
        with self.assertRaises(KeyError):
            getUncertaintyBudgets(1, 1)

    @patch("collectUncertainties.requests.Session")
    @patch("collectUncertainties.getServiceCapabilities")
    @patch("collectUncertainties.getTechniquesList")
    @patch("collectUncertainties.getUncertaintyBudgets")
    @patch("collectUncertainties.login")
    @patch("collectUncertainties.driver")
    def test_main(
        self,
        mock_driver,
        mock_login,
        mock_getUncertaintyBudgets,
        mock_getTechniquesList,
        mock_getServiceCapabilities,
        mock_requests_session,
    ):
        # Mock the service capabilities and techniques list
        mock_getServiceCapabilities.return_value = [{"ServiceGroupId": 1}]
        mock_getTechniquesList.return_value = [{"TechniqueId": 1}]

        # Mock the uncertainty budgets
        mock_getUncertaintyBudgets.return_value = [{"BudgetId": 1, "Value": "Budget1"}]

        # Mock the requests session
        mock_session = MagicMock()
        mock_requests_session.return_value = mock_session

        # Use a temporary directory to avoid clutter
        with tempfile.TemporaryDirectory() as tempdir:
            with patch("collectUncertainties.output_dir", tempdir):
                main()

                # Ensure files exist in tempdir
                self.assertTrue(
                    os.path.exists(os.path.join(tempdir, "ServiceCapabilities.csv"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(tempdir, "TechniquesList.csv"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(tempdir, "AllUncertaintyBudgets.csv"))
                )

                # Validate that CSVs are non-empty
                df_service = pd.read_csv(
                    os.path.join(tempdir, "ServiceCapabilities.csv")
                )
                df_techniques = pd.read_csv(os.path.join(tempdir, "TechniquesList.csv"))
                df_uncert = pd.read_csv(
                    os.path.join(tempdir, "AllUncertaintyBudgets.csv")
                )

                self.assertFalse(df_service.empty)
                self.assertFalse(df_techniques.empty)
                self.assertFalse(df_uncert.empty)


if __name__ == "__main__":
    unittest.main()
