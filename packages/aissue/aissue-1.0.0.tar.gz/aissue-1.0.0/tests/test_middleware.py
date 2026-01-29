import json
from unittest.mock import patch, MagicMock, call
from django.test import TestCase, RequestFactory, override_settings, Client
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.exceptions import ImproperlyConfigured
import requests

from aissue.middleware import AIssueMiddleware
from aissue.exceptions import AIssueConfigurationError


@patch('aissue.middleware.requests.post')
class TestAIssueMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a mock get_response function
        self.get_response = MagicMock()

    @override_settings(
        AISSUE_API_KEY='test-key', 
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_successful_request_no_error(self, mock_post):
        """Test that middleware passes through successful requests without logging"""
        request = self.factory.get('/test-path')
        self.get_response.return_value = HttpResponse('OK')
        
        middleware = AIssueMiddleware(self.get_response)
        response = middleware(request)
        
        self.assertEqual(response.status_code, 200)
        mock_post.assert_not_called()

    @override_settings(
        AISSUE_API_KEY='test-key', 
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_process_exception_logs_error(self, mock_post):
        """Test that process_exception logs errors when DEBUG=False"""
        request = self.factory.get('/test-path')
        request.user = self.user
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        # Call process_exception directly
        result = middleware.process_exception(request, exception)
        
        # Should return None to continue Django's error handling
        self.assertIsNone(result)
        
        # Verify the error was logged
        self.assertTrue(mock_post.called)
        
        # Get the call arguments
        args, kwargs = mock_post.call_args
        
        # Check the URL
        self.assertEqual(args[0], 'http://test.com/api/errors/')
        
        # Check the headers
        self.assertEqual(kwargs['headers'], {'X-API-Key': 'test-key'})
        
        # Check the error data
        error_data = kwargs['json']
        self.assertEqual(error_data['error_code'], 500)
        self.assertEqual(error_data['path'], '/test-path')
        self.assertEqual(error_data['method'], 'GET')
        self.assertEqual(error_data['user_email'], 'test@example.com')
        self.assertEqual(error_data['user_id'], str(self.user.id))

    @override_settings(
        AISSUE_API_KEY='test-key', 
        AISSUE_BASE_URL='http://test.com',
        DEBUG=True,
        AISSUE_LOG_IN_DEBUG=False
    )
    def test_debug_mode_no_logging(self, mock_post):
        """Test that middleware doesn't log in DEBUG mode by default"""
        request = self.factory.get('/test-path')
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        # Call process_exception
        middleware.process_exception(request, exception)
        
        # Should not log in debug mode
        mock_post.assert_not_called()

    @override_settings(
        AISSUE_API_KEY='test-key', 
        AISSUE_BASE_URL='http://test.com',
        DEBUG=True,
        AISSUE_LOG_IN_DEBUG=True
    )
    def test_debug_mode_with_log_in_debug(self, mock_post):
        """Test that middleware logs in DEBUG mode when AISSUE_LOG_IN_DEBUG=True"""
        request = self.factory.get('/test-path')
        request.user = self.user
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        # Call process_exception
        middleware.process_exception(request, exception)
        
        # Should log even in debug mode
        self.assertTrue(mock_post.called)

    @override_settings(AISSUE_API_KEY='')  # Override to empty string
    def test_missing_api_key_raises_error(self, mock_post):
        """Test that missing API key raises configuration error"""
        with self.assertRaises(AIssueConfigurationError):
            AIssueMiddleware(self.get_response)

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_ENABLED=False,
        DEBUG=False
    )
    def test_disabled_middleware(self, mock_post):
        """Test that disabled middleware doesn't log errors"""
        request = self.factory.get('/test-path')
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        # Call process_exception
        middleware.process_exception(request, exception)
        
        # Should not log when disabled
        mock_post.assert_not_called()

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_api_error_handling(self, mock_post):
        """Test that API errors are handled gracefully"""
        request = self.factory.get('/test-path')
        request.user = self.user
        
        # Simulate API error
        mock_post.side_effect = requests.RequestException('API error')
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        # Should not raise an exception
        result = middleware.process_exception(request, exception)
        self.assertIsNone(result)

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_anonymous_user_handling(self, mock_post):
        """Test that anonymous users are handled correctly"""
        request = self.factory.get('/test-path')
        request.user = MagicMock(is_authenticated=False, email=None)
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        middleware.process_exception(request, exception)
        
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        error_data = kwargs['json']
        self.assertIsNone(error_data['user_email'])
        self.assertIsNone(error_data['user_id'])

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_post_data_capture(self, mock_post):
        """Test that POST data is correctly captured"""
        request = self.factory.post('/test-path', data={'test': 'value'})
        request.user = self.user
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        middleware.process_exception(request, exception)
        
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        error_data = kwargs['json']
        self.assertEqual(error_data['request_data']['POST'], {'test': ['value']})

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_BASE_URL='http://test.com',
        DEBUG=False
    )
    def test_json_body_capture(self, mock_post):
        """Test that JSON request body is correctly captured"""
        json_data = {'test': 'value'}
        request = self.factory.post(
            '/test-path',
            data=json.dumps(json_data),
            content_type='application/json'
        )
        request.user = self.user
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        middleware.process_exception(request, exception)
        
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        error_data = kwargs['json']
        self.assertEqual(error_data['request_data']['body'], json_data)

    @override_settings(
        AISSUE_API_KEY='test-key',
        AISSUE_BASE_URL='http://test.com',
        AISSUE_TIMEOUT=10,
        DEBUG=False
    )
    def test_custom_timeout(self, mock_post):
        """Test that custom timeout is used"""
        request = self.factory.get('/test-path')
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        middleware = AIssueMiddleware(self.get_response)
        exception = ValueError('Test error')
        
        middleware.process_exception(request, exception)
        
        # Check that timeout was passed correctly
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['timeout'], 10) 