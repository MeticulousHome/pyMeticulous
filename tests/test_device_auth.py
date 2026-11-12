"""Unit tests for device authorization.

Covers the optional bearer token on HTTP and Socket.IO, the /auth helpers,
the onUnauthorized callback and how a machine without device authorization
(404) or a refused device (401 / connect_error "unauthorized") shows up.
"""

import json
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import socketio
from requests.models import PreparedRequest, Response

from meticulous import Api, APIError
from meticulous.api import ApiOptions, UnauthorizedError
from meticulous.api_types import (
    AccessRequestResponse,
    AccessRequestState,
    AccessRequestStatus,
    ActionType,
    AuthErrorCode,
    Settings,
    TokenResponse,
    TokenValidation,
)
from .mock_responses import MOCK_SETTINGS_RESPONSE

TOKEN = "header.payload.signature"
UNAUTHORIZED_BODY = {
    "status": "error",
    "error": "This device is not authorized",
    "data": {"code": "UNAUTHORIZED"},
}


def make_response(
    status_code: int,
    body: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    text: Optional[str] = None,
) -> Response:
    response = Response()
    response.status_code = status_code
    response.reason = "Reason"
    if text is not None:
        response._content = text.encode()
    else:
        response._content = json.dumps(body).encode()
    response.headers.update(headers or {})
    return response


def error_body(code: str, error: str = "error") -> Dict[str, Any]:
    return {"status": "error", "error": error, "data": {"code": code}}


class TestToken(unittest.TestCase):
    """The token is optional and only sent when set."""

    def test_no_token_sends_no_header(self) -> None:
        api = Api(base_url="http://localhost:8080/")
        self.assertIsNone(api.token)
        self.assertNotIn("Authorization", api.session.headers)

    def test_token_sets_bearer_header(self) -> None:
        api = Api(base_url="http://localhost:8080/", token=TOKEN)
        self.assertEqual(api.token, TOKEN)
        self.assertEqual(api.session.headers["Authorization"], f"Bearer {TOKEN}")

    def test_clearing_token_removes_header(self) -> None:
        api = Api(base_url="http://localhost:8080/", token=TOKEN)
        api.token = None
        self.assertIsNone(api.token)
        self.assertNotIn("Authorization", api.session.headers)

        api.token = TOKEN
        api.token = ""
        self.assertIsNone(api.token)
        self.assertNotIn("Authorization", api.session.headers)

    @patch("requests.adapters.HTTPAdapter.send")
    def test_header_reaches_the_wire(self, mock_send: Mock) -> None:
        """The Authorization header is on the prepared request only with a token."""
        sent: list = []

        def send(request: PreparedRequest, **kwargs: object) -> Response:
            sent.append(request)
            response = make_response(200, MOCK_SETTINGS_RESPONSE)
            response.url = request.url or ""
            return response

        mock_send.side_effect = send

        Api(base_url="http://localhost:8080", token=TOKEN).get_settings()
        Api(base_url="http://localhost:8080").get_settings()

        self.assertEqual(sent[0].headers["Authorization"], f"Bearer {TOKEN}")
        self.assertNotIn("Authorization", sent[1].headers)

    def test_settings_require_authorization(self) -> None:
        settings = Settings(**MOCK_SETTINGS_RESPONSE)
        self.assertIsNone(settings.require_authorization)

        settings = Settings(**{**MOCK_SETTINGS_RESPONSE, "require_authorization": True})
        self.assertTrue(settings.require_authorization)


class TestAccessRequest(unittest.TestCase):
    """POST /auth/request and GET /auth/request/<id>."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080")

    @patch("requests.Session.post")
    def test_request_access(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(
            202, {"id": "3f2c9a1e-request", "expires_in": 60}
        )

        result = self.api.request_access("Home Assistant")

        self.assertIsInstance(result, AccessRequestResponse)
        assert isinstance(result, AccessRequestResponse)
        self.assertEqual(result.id, "3f2c9a1e-request")
        self.assertEqual(result.expires_in, 60)
        mock_post.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/request",
            json={"name": "Home Assistant"},
        )

    @patch("requests.Session.post")
    def test_request_access_pending(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(409, error_body("REQUEST_PENDING"))

        result = self.api.request_access("Home Assistant")

        self.assertIsInstance(result, APIError)
        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.REQUEST_PENDING)
        self.assertEqual(result.http_status, 409)

    @patch("requests.Session.post")
    def test_request_access_throttled(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(
            429, error_body("TOO_MANY_ATTEMPTS"), headers={"Retry-After": "42"}
        )

        result = self.api.request_access("Home Assistant")

        assert isinstance(result, APIError)
        self.assertEqual(result.code, "TOO_MANY_ATTEMPTS")
        self.assertEqual(result.http_status, 429)
        self.assertEqual(result.retry_after, 42)

    @patch("requests.Session.post")
    def test_request_access_old_backend(self, mock_post: Mock) -> None:
        """A backend without device authorization answers 404."""
        mock_post.return_value = make_response(404, text="<html>Not Found</html>")

        result = self.api.request_access("Home Assistant")

        assert isinstance(result, APIError)
        self.assertEqual(result.http_status, 404)
        self.assertIsNone(result.code)

    @patch("requests.Session.get")
    def test_get_access_request_pending(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(200, {"status": "pending"})

        result = self.api.get_access_request("3f2c9a1e-request")

        assert isinstance(result, AccessRequestStatus)
        self.assertEqual(result.status, AccessRequestState.PENDING)
        self.assertIsNone(result.code)
        mock_get.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/request/3f2c9a1e-request"
        )

    @patch("requests.Session.get")
    def test_get_access_request_approved(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(
            200, {"status": "approved", "code": "ABCDEFGH", "expires_in": 600}
        )

        result = self.api.get_access_request("3f2c9a1e-request")

        assert isinstance(result, AccessRequestStatus)
        self.assertEqual(result.status, AccessRequestState.APPROVED)
        self.assertEqual(result.code, "ABCDEFGH")
        self.assertEqual(result.expires_in, 600)
        self.assertNotIn("ABCDEFGH", repr(result))

    @patch("requests.Session.get")
    def test_get_access_request_escapes_id(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(200, {"status": "denied"})

        self.api.get_access_request("../machine")

        mock_get.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/request/..%2Fmachine"
        )

    @patch("requests.Session.get")
    def test_get_access_request_unknown(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(404, error_body("NOT_FOUND"))

        result = self.api.get_access_request("gone")

        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.NOT_FOUND)
        self.assertEqual(result.http_status, 404)


class TestTokenExchange(unittest.TestCase):
    """POST /auth/token."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080")

    @patch("requests.Session.post")
    def test_exchange_pairing_code(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(
            200, {"token": TOKEN, "device": {"id": "dev-1", "name": "Home Assistant"}}
        )

        result = self.api.exchange_pairing_code("ABCD-EFGH", "Home Assistant")

        assert isinstance(result, TokenResponse)
        self.assertEqual(result.token, TOKEN)
        self.assertEqual(result.device.id, "dev-1")
        self.assertEqual(result.device.name, "Home Assistant")
        mock_post.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/token",
            json={"code": "ABCD-EFGH", "name": "Home Assistant"},
        )
        # The caller decides where to keep the token
        self.assertIsNone(self.api.token)
        self.assertNotIn(TOKEN, repr(result))
        self.assertNotIn(TOKEN, str(result))

    @patch("requests.Session.post")
    def test_exchange_without_name(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(
            200, {"token": TOKEN, "device": {"id": "dev-1", "name": "Unnamed device"}}
        )

        self.api.exchange_pairing_code("ABCDEFGH")

        mock_post.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/token", json={"code": "ABCDEFGH"}
        )

    @patch("requests.Session.post")
    def test_exchange_invalid_code(self, mock_post: Mock) -> None:
        mock_post.return_value = make_response(401, error_body("INVALID_CODE"))

        result = self.api.exchange_pairing_code("ABCDEFGH")

        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.INVALID_CODE)
        self.assertEqual(result.http_status, 401)


class TestValidateToken(unittest.TestCase):
    """GET /auth/validate."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080", token=TOKEN)

    @patch("requests.Session.get")
    def test_validate_token(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(
            200,
            {
                "required": True,
                "local": False,
                "token_valid": True,
                "device": {"id": "dev-1", "name": "Home Assistant"},
            },
        )

        result = self.api.validate_token()

        assert isinstance(result, TokenValidation)
        self.assertTrue(result.token_valid)
        self.assertFalse(result.local)
        assert result.device is not None
        self.assertEqual(result.device.name, "Home Assistant")
        # The stored token goes through the session header
        mock_get.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/validate", headers=None
        )

    @patch("requests.Session.get")
    def test_validate_given_token(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(
            200,
            {"required": False, "local": False, "token_valid": False, "device": None},
        )

        result = self.api.validate_token("other.token.value")

        assert isinstance(result, TokenValidation)
        self.assertIsNone(result.device)
        mock_get.assert_called_once_with(
            "http://localhost:8080/api/v1/auth/validate",
            headers={"Authorization": "Bearer other.token.value"},
        )

    @patch("requests.Session.get")
    def test_validate_unauthorized(self, mock_get: Mock) -> None:
        mock_get.return_value = make_response(
            401, {**UNAUTHORIZED_BODY, "required": True}
        )

        result = self.api.validate_token()

        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.UNAUTHORIZED)
        self.assertEqual(result.http_status, 401)


class TestUnauthorizedCallback(unittest.TestCase):
    """onUnauthorized fires on a 401 UNAUTHORIZED outside /auth."""

    def make_api(self, handler: Mock) -> Api:
        return Api(
            base_url="http://localhost:8080/",
            options=ApiOptions(onUnauthorized=handler),
        )

    def serve(self, mock_send: Mock, response: Response) -> None:
        def send(request: PreparedRequest, **kwargs: object) -> Response:
            response.url = request.url or ""
            return response

        mock_send.side_effect = send

    @patch("requests.adapters.HTTPAdapter.send")
    def test_called_on_unauthorized(self, mock_send: Mock) -> None:
        handler = Mock()
        self.serve(mock_send, make_response(401, UNAUTHORIZED_BODY))

        result = self.make_api(handler).list_profiles()

        handler.assert_called_once_with()
        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.UNAUTHORIZED)

    @patch("requests.adapters.HTTPAdapter.send")
    def test_not_called_for_auth_routes(self, mock_send: Mock) -> None:
        handler = Mock()
        self.serve(mock_send, make_response(401, UNAUTHORIZED_BODY))

        self.make_api(handler).validate_token()

        handler.assert_not_called()

    @patch("requests.adapters.HTTPAdapter.send")
    def test_not_called_for_other_errors(self, mock_send: Mock) -> None:
        handler = Mock()
        api = self.make_api(handler)

        self.serve(mock_send, make_response(401, error_body("SOMETHING_ELSE")))
        api.list_profiles()
        self.serve(mock_send, make_response(401, text="Unauthorized"))
        api.list_profiles()
        self.serve(mock_send, make_response(403, error_body("UNAUTHORIZED")))
        api.list_profiles()

        handler.assert_not_called()

    @patch("requests.adapters.HTTPAdapter.send")
    def test_handler_error_does_not_break_the_call(self, mock_send: Mock) -> None:
        handler = Mock(side_effect=RuntimeError("boom"))
        self.serve(mock_send, make_response(401, UNAUTHORIZED_BODY))

        with self.assertLogs("meticulous.api", level="ERROR"):
            result = self.make_api(handler).list_profiles()

        self.assertIsInstance(result, APIError)

    @patch("requests.Session.get")
    def test_execute_action_unauthorized(self, mock_get: Mock) -> None:
        """A 401 is not read as an ActionResponse."""
        mock_get.return_value = make_response(401, UNAUTHORIZED_BODY)

        result = Api(base_url="http://localhost:8080").execute_action(ActionType.START)

        assert isinstance(result, APIError)
        self.assertEqual(result.code, AuthErrorCode.UNAUTHORIZED)

    def test_option_is_not_a_socket_event(self) -> None:
        sio = MagicMock()
        ApiOptions(onUnauthorized=Mock()).register_handlers(sio)
        sio.on.assert_not_called()


class TestSocketAuth(unittest.TestCase):
    """Socket.IO handshake auth and the "unauthorized" refusal."""

    @patch("socketio.Client")
    def test_connect_sends_token(self, mock_client_class: Mock) -> None:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        api = Api(base_url="http://localhost:8080/", token=TOKEN)

        api.connect_to_socket()

        args, kwargs = mock_client.connect.call_args
        self.assertEqual(args, ("http://localhost:8080/",))
        # A callable, so reconnects pick up the current token
        auth = kwargs["auth"]
        self.assertEqual(auth(), {"token": TOKEN})
        api.token = None
        self.assertIsNone(auth())

    @patch("socketio.Client")
    def test_connect_without_token(self, mock_client_class: Mock) -> None:
        """No token sends no auth data, like before device authorization."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        api = Api(base_url="http://localhost:8080/")

        api.connect_to_socket()

        self.assertIsNone(mock_client.connect.call_args.kwargs["auth"]())

    @patch("socketio.Client")
    def test_connect_error_handler_registered(self, mock_client_class: Mock) -> None:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        api = Api(base_url="http://localhost:8080/")

        mock_client.on.assert_any_call("connect_error", api._on_connect_error)

    @patch("socketio.Client")
    @patch("time.sleep")
    def test_refusal_raises_without_retry(
        self, mock_sleep: Mock, mock_client_class: Mock
    ) -> None:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        handler = Mock()
        api = Api(
            base_url="http://localhost:8080/",
            options=ApiOptions(onUnauthorized=handler),
        )

        def refuse(*args: object, **kwargs: object) -> None:
            # python-socketio calls the connect_error handler before raising
            api._on_connect_error({"message": "unauthorized"})
            raise socketio.exceptions.ConnectionError(
                "One or more namespaces failed to connect: /"
            )

        mock_client.connect.side_effect = refuse

        with self.assertRaises(UnauthorizedError) as ctx:
            api.connect_to_socket(retries=3)

        self.assertIsInstance(ctx.exception, socketio.exceptions.ConnectionError)
        self.assertEqual(mock_client.connect.call_count, 1)
        mock_sleep.assert_not_called()
        handler.assert_called_once_with()

    @patch("socketio.Client")
    @patch("time.sleep")
    def test_other_refusals_still_retry(
        self, mock_sleep: Mock, mock_client_class: Mock
    ) -> None:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        api = Api(base_url="http://localhost:8080/")
        attempts: list = []

        def refuse(*args: object, **kwargs: object) -> None:
            attempts.append(1)
            if len(attempts) == 1:
                api._on_connect_error("Connection refused by the server")
                raise socketio.exceptions.ConnectionError("refused")

        mock_client.connect.side_effect = refuse

        api.connect_to_socket(retries=1)

        self.assertEqual(mock_client.connect.call_count, 2)

    @patch("socketio.Client")
    def test_background_refusals_notify_once(self, mock_client_class: Mock) -> None:
        """Reconnect attempts refused again do not repeat the callback."""
        mock_client_class.return_value = MagicMock()
        handler = Mock()
        api = Api(
            base_url="http://localhost:8080/",
            options=ApiOptions(onUnauthorized=handler),
        )

        api._on_connect_error({"message": "unauthorized"})
        api._on_connect_error({"message": "unauthorized"})
        self.assertEqual(handler.call_count, 1)

        # A new token resets it
        api.token = TOKEN
        api._on_connect_error({"message": "unauthorized"})
        self.assertEqual(handler.call_count, 2)


if __name__ == "__main__":
    unittest.main()
