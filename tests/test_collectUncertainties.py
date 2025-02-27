import unittest
from unittest.mock import patch
from collectUncertainties import driver_get
from collectUncertainties import getServiceCapabilities
import json
from unittest.mock import MagicMock
import os

from collectUncertainties import (
    getTechniquesList,
    getUncertaintyBudgets,
    main,
)


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

        # Check if login was not called
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
            [{"BudgetId": 1, "Value": "Budget1"}, {"BudgetId": 2, "Value": "Budget2"}],
        )

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

        # Call the main function
        main()

        # Check if the CSV files were created
        self.assertTrue(os.path.exists("csv/ServiceCapabilities.csv"))
        self.assertTrue(os.path.exists("csv/TechniquesList.csv"))
        self.assertTrue(os.path.exists("csv/AllUncertaintyBudgets.csv"))

        # Clean up the created files
        os.remove("csv/ServiceCapabilities.csv")
        os.remove("csv/TechniquesList.csv")
        os.remove("csv/AllUncertaintyBudgets.csv")


if __name__ == "__main__":
    unittest.main()
