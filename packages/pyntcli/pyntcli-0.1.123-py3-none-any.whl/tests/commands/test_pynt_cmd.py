import unittest
import argparse
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pyntcli.commands.pynt_cmd import PyntCommand, UserAbortedException
import requests


class TestIsBusinessPlanUser(unittest.TestCase):

    @patch('requests.get')
    @patch('pyntcli.saas_client.saas_client.CredStore')
    def test_is_business_plan_user_success(self, mock_requests_get, mock_cred_store):
        # Mock the CredStore context manager
        mock_store_instance = mock_cred_store.return_value.__enter__.return_value
        mock_store_instance.get_access_token.return_value = 'fake_token'
        mock_store_instance.get_token_type.return_value = 'Bearer'

        # Mock the requests.get response
        mock_response = MagicMock()
        mock_requests_get.return_value = mock_response

        # Instantiate the class and call the method
        instance = PyntCommand()
        result = instance._is_business_plan_user()

        # Assert the result
        self.assertTrue(result)

    @patch('requests.get')
    @patch('pyntcli.saas_client.saas_client.CredStore')
    def test_is_business_plan_user_failure(self,mock_cred_store, mock_requests_get):
        # Mock the CredStore context manager
        mock_store_instance = mock_cred_store.return_value.__enter__.return_value
        mock_store_instance.get_access_token.return_value = 'fake_token'
        mock_store_instance.get_token_type.return_value = 'Bearer'


        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=MagicMock(status_code=403))
        mock_requests_get.return_value = mock_response

        # Instantiate the class and call the method
        instance = PyntCommand()
        result = instance._is_business_plan_user()

        # Assert the result
        self.assertFalse(result)

    @patch('requests.get')
    @patch('pyntcli.saas_client.saas_client.CredStore')
    def test_is_business_plan_user_exception(self, mock_cred_store, mock_requests_get):
        # Mock the CredStore context manager
        mock_store_instance = mock_cred_store.return_value.__enter__.return_value
        mock_store_instance.get_access_token.return_value = 'fake_token'
        mock_store_instance.get_token_type.return_value = 'Bearer'

        # Mock the requests.get to raise an exception
        mock_requests_get.side_effect = requests.exceptions.RequestException

        # Instantiate the class and call the method
        instance = PyntCommand()
        result = instance._is_business_plan_user()

        # Assert the result
        self.assertFalse(result)

    @patch.object(PyntCommand, '_is_missing_app_id_confirmed', return_value=True)
    def test_post_login_args_validation_missing_app_id_user_confirmed(self, _):
        # Instantiate the class and call the method with valid arguments
        instance = PyntCommand()
        try:
            result = instance._post_login_args_validation(argparse.Namespace(
                application_id="", application_name="", yes=False), "non-postman-command", True)
        except Exception as e:
            self.fail(f"Unexpected exception raised {e}")

    @patch.object(PyntCommand, '_is_missing_app_id_confirmed', return_value=False)
    def test_post_login_args_validation_missing_app_id_yes_flag_used(self, _):
        # Instantiate the class and call the method with valid arguments
        instance = PyntCommand()
        try:
            result = instance._post_login_args_validation(argparse.Namespace(
                application_id="", application_name="", yes=True), "non-postman-command", True)
        except Exception as e:
            self.fail(f"Unexpected exception raised {e}")

    @patch.object(PyntCommand, '_is_missing_app_id_confirmed', return_value=False)
    def test_post_login_args_validation_missing_app_id_user_aborted(self, _):
        # Instantiate the class and call the method with valid arguments
        instance = PyntCommand()
        with self.assertRaises(UserAbortedException):
            result = instance._post_login_args_validation(argparse.Namespace(
                application_id="", application_name="", yes=False), "non-postman-command", True)

    @patch.object(PyntCommand, '_is_missing_app_id_confirmed', return_value=False)
    def test_post_login_args_validation_missing_app_id_free_tier(self, _):
        # Instantiate the class and call the method with valid arguments
        instance = PyntCommand()
        try:
            result = instance._post_login_args_validation(argparse.Namespace(
                application_id="", application_name="", yes=False), "non-postman-command", False)
        except Exception as e:
            self.fail(f"Unexpected exception raised {e}")

    @patch.object(PyntCommand, '_is_missing_app_id_confirmed', return_value=False)
    def test_post_login_args_validation_missing_app_id_not_required(self, _):
        # Instantiate the class and call the method with valid arguments
        instance = PyntCommand()
        try:
            result = instance._post_login_args_validation(
                argparse.Namespace(application_id="", application_name="", yes=False), "postman", True)
            result = instance._post_login_args_validation(
                argparse.Namespace(application_id="", application_name="", yes=False), "pynt-id", True)
        except Exception as e:
            self.fail(f"Unexpected exception raised {e}")

    @patch('pyntcli.commands.pynt_cmd.prompt.confirmation_prompt_with_timeout', return_value=True)
    @patch('pyntcli.commands.pynt_cmd.StateStore')
    def test_missing_app_id_confirmation_confirmation_expired_user_confirms(self, mock_state_store, _):
        long_time_ago = datetime.now() - timedelta(days=100)
        # Mock the CredStore context manager
        mock_store_instance = MagicMock()
        mock_store_instance.get_prompts_history.return_value = {"missing_app_id": {
            "last_confirmation": long_time_ago.strftime("%Y-%m-%d %H:%M:%S")}}
        mock_store_instance.put_prompts_history.return_value = None
        mock_state_store.return_value.__enter__.return_value = mock_store_instance

        # Instantiate the class and call the method with app_id present
        instance = PyntCommand()
        result = instance._is_missing_app_id_confirmed()

        # Assert the result
        self.assertTrue(result)

    @patch('pyntcli.commands.pynt_cmd.prompt.confirmation_prompt_with_timeout', return_value=True)
    @patch('requests.get')
    def test_is_auto_create_app_confirmed_auto_confirms(self, mock_requests_get,  _):
        mock_response = MagicMock()
        mock_requests_get.return_value = mock_response

        instance = PyntCommand()
        result = instance._is_auto_create_app_confirmed("app_name")

        # Assert the result
        self.assertTrue(result)

    @patch('pyntcli.commands.pynt_cmd.prompt.confirmation_prompt_with_timeout', return_value=False)
    @patch('pyntcli.commands.pynt_cmd.StateStore')
    def test_missing_app_id_confirmation_confirmation_expired_user_aborts(self, mock_state_store, _):
        long_time_ago = datetime.now() - timedelta(days=100)
        # Mock the CredStore context manager
        mock_store_instance = MagicMock()
        mock_store_instance.get_prompts_history.return_value = {"missing_app_id": {
            "last_confirmation": long_time_ago.strftime("%Y-%m-%d %H:%M:%S")}}
        mock_store_instance.put_prompts_history.return_value = None
        mock_state_store.return_value.__enter__.return_value = mock_store_instance

        # Instantiate the class and call the method with app_id present
        instance = PyntCommand()
        result = instance._is_missing_app_id_confirmed()

        # Assert the result
        self.assertFalse(result)

    @patch('pyntcli.commands.pynt_cmd.prompt.confirmation_prompt_with_timeout', return_value=False)
    @patch('pyntcli.commands.pynt_cmd.StateStore')
    def test_missing_app_id_confirmation_user_already_confirmed(self, mock_state_store, _):
        recently = datetime.now() - timedelta(hours=1)
        # Mock the CredStore context manager
        mock_store_instance = MagicMock()
        mock_store_instance.get_prompts_history.return_value = {"missing_app_id": {
            "last_confirmation": recently.strftime("%Y-%m-%d %H:%M:%S")}}
        mock_store_instance.put_prompts_history.return_value = None
        mock_state_store.return_value.__enter__.return_value = mock_store_instance

        # Instantiate the class and call the method with app_id present
        instance = PyntCommand()
        result = instance._is_missing_app_id_confirmed()

        # Assert the result
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
