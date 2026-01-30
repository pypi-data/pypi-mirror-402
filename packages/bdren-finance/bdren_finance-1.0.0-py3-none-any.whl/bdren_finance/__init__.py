import json
import logging
from typing import Dict, Any, Optional, Union

import requests
from django.conf import settings

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logger = logging.getLogger(__name__)

BASE_URL = settings.BDREN_FINANCE_URL


class BdRENFinanceAPIError(Exception):
    """Base exception for BdREN Finance API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class BdRENFinanceAuthError(BdRENFinanceAPIError):
    """Exception raised when authentication fails"""
    pass


class BdRENFinanceConnectionError(BdRENFinanceAPIError):
    """Exception raised when connection fails"""
    pass


class BdRENFinanceValidationError(BdRENFinanceAPIError):
    """Exception raised when validation fails"""
    pass


def finance_login_session() -> requests.Session:
    """
    Create an authenticated session with BdREN Finance API.

    Returns:
        requests.Session: Authenticated session object

    Raises:
        BdRENFinanceConnectionError: If connection to the API fails
        BdRENFinanceAuthError: If authentication fails
    """
    session = requests.Session()

    try:
        # Get CSRF token - disable SSL verification
        res = session.get(
            BASE_URL + 'csrf/',
            verify=False,
            timeout=30
        )
        res.raise_for_status()

        csrf_data = res.json()
        csrf_token = csrf_data.get('csrf_token')

        if not csrf_token:
            raise BdRENFinanceAuthError('CSRF token not found in response')

        login_data = {
            'email': settings.BDREN_FINANCE_AUTH_EMAIL,
            'password': settings.BDREN_FINANCE_AUTH_PASSWORD,
            'csrfmiddlewaretoken': csrf_token
        }

        headers = {
            'Referer': BASE_URL + 'login/',
            'X-CSRFToken': session.cookies.get('csrftoken', csrf_token)
        }

        # Perform login - disable SSL verification
        login = session.post(
            BASE_URL + 'login/',
            data=login_data,
            headers=headers,
            verify=False,
            timeout=30
        )

        if login.status_code != 200:
            raise BdRENFinanceAuthError(
                'Login failed to BdREN Finance',
                status_code=login.status_code,
                response_data=login.text
            )

        logger.info('Successfully authenticated with BdREN Finance API')
        return session

    except requests.exceptions.Timeout as e:
        logger.error(f'Timeout while connecting to BdREN Finance API: {e}')
        raise BdRENFinanceConnectionError(f'Connection timeout: {str(e)}')
    except requests.exceptions.ConnectionError as e:
        logger.error(f'Connection error to BdREN Finance API: {e}')
        raise BdRENFinanceConnectionError(f'Connection failed: {str(e)}')
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error to BdREN Finance API: {e}')
        raise BdRENFinanceConnectionError(f'Request failed: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error during authentication: {e}')
        raise BdRENFinanceAuthError(f'Authentication error: {str(e)}')


def get_accounts(query: str, _type: str = "all", field: str = "no") -> Dict[str, Any]:
    """
    Get accounts from BdREN Finance API.

    Args:
        query (str): Query string to search for accounts
        _type (str, optional): Account type filter. Options: "all", "parent", "sub". Defaults to "all".
        field (str, optional): Field to search in. Options: "no", "name". Defaults to "no".

    Returns:
        Dict[str, Any]: JSON response containing account information

    Raises:
        BdRENFinanceAPIError: If the API request fails
        BdRENFinanceValidationError: If parameters are invalid

    Example:
        >>> accounts = get_accounts("1234", _type="sub", field="no")
        >>> print(accounts)
    """
    # Validate input parameters
    valid_types = ["all", "parent", "sub"]
    valid_fields = ["no", "name"]

    if _type not in valid_types:
        raise BdRENFinanceValidationError(
            f'Invalid type: {_type}. Must be one of {valid_types}'
        )

    if field not in valid_fields:
        raise BdRENFinanceValidationError(
            f'Invalid field: {field}. Must be one of {valid_fields}'
        )

    session = None
    try:
        session = finance_login_session()

        url = f'{BASE_URL}account/search/?q={query}&type={_type}&field={field}'

        logger.debug(f'Fetching accounts with query: {query}, type: {_type}, field: {field}')

        res = session.get(url, verify=False, timeout=30)
        res.raise_for_status()

        response_data = res.json()
        logger.info(f'Successfully retrieved accounts for query: {query}')

        return response_data

    except requests.exceptions.Timeout as e:
        logger.error(f'Timeout while fetching accounts: {e}')
        raise BdRENFinanceAPIError(f'Request timeout: {str(e)}')
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error while fetching accounts: {e}')
        raise BdRENFinanceAPIError(
            f'HTTP error: {str(e)}',
            status_code=e.response.status_code if e.response else None
        )
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error while fetching accounts: {e}')
        raise BdRENFinanceAPIError(f'Request failed: {str(e)}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse JSON response: {e}')
        raise BdRENFinanceAPIError(f'Invalid JSON response: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error while fetching accounts: {e}')
        raise BdRENFinanceAPIError(f'Unexpected error: {str(e)}')
    finally:
        if session:
            session.close()
            logger.debug('Session closed')


def create_entry(payload: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Create entry in BdREN Finance API.

    Args:
        payload (Union[Dict[str, Any], str]): Entry data as dictionary or JSON string

    Returns:
        Dict[str, Any]: JSON response containing created entry information

    Raises:
        BdRENFinanceAPIError: If the API request fails
        BdRENFinanceValidationError: If payload is invalid

    Example:
        >>> payload = {
        ...     "transNo": "",
        ...     "transDate": "2026-01-22",
        ...     "generalParticular": "This is general Particular",
        ...     "vouchers": [
        ...         {
        ...             "accountNo": 15600005,
        ...             "drAmount": 100,
        ...             "crAmount": 0,
        ...             "particular": "Bank will be debited",
        ...             "type": "dr"
        ...         },
        ...         {
        ...             "accountNo": 16600114,
        ...             "drAmount": 0,
        ...             "crAmount": 100,
        ...             "particular": "The university will be credited",
        ...             "type": "cr"
        ...         }
        ...     ]
        ... }
        >>> result = create_entry(payload)
        >>> print(result)
    """
    session = None
    try:
        # Validate payload
        if isinstance(payload, dict):
            if 'vouchers' not in payload:
                raise BdRENFinanceValidationError('Payload must contain "vouchers" field')

            if not isinstance(payload['vouchers'], list) or len(payload['vouchers']) == 0:
                raise BdRENFinanceValidationError('Vouchers must be a non-empty list')

            # Validate voucher structure
            for idx, voucher in enumerate(payload['vouchers']):
                required_fields = ['accountNo', 'drAmount', 'crAmount', 'particular', 'type']
                for field in required_fields:
                    if field not in voucher:
                        raise BdRENFinanceValidationError(
                            f'Voucher at index {idx} is missing required field: {field}'
                        )

        session = finance_login_session()

        headers = {
            'Referer': BASE_URL + 'entry/create/',
            'X-CSRFToken': session.cookies['csrftoken'],
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }

        if isinstance(payload, str):
            json_payload = payload
        else:
            json_payload = json.dumps(payload)

        logger.debug(f'Creating entry with payload: {json_payload[:200]}...')

        response = session.post(
            BASE_URL + 'entry/create/',
            data=json_payload,
            headers=headers,
            verify=False,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        logger.info(f'Successfully created entry')

        return response_data

    except requests.exceptions.Timeout as e:
        logger.error(f'Timeout while creating entry: {e}')
        raise BdRENFinanceAPIError(f'Request timeout: {str(e)}')
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error while creating entry: {e}')
        raise BdRENFinanceAPIError(
            f'HTTP error: {str(e)}',
            status_code=e.response.status_code if e.response else None,
            response_data=e.response.text if e.response else None
        )
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error while creating entry: {e}')
        raise BdRENFinanceAPIError(f'Request failed: {str(e)}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse JSON response: {e}')
        raise BdRENFinanceAPIError(f'Invalid JSON response: {str(e)}')
    except BdRENFinanceValidationError:
        raise
    except Exception as e:
        logger.error(f'Unexpected error while creating entry: {e}')
        raise BdRENFinanceAPIError(f'Unexpected error: {str(e)}')
    finally:
        if session:
            session.close()
            logger.debug('Session closed')


def get_entry(entry_id: int) -> Dict[str, Any]:
    """
    Get entry from BdREN Finance API.

    Args:
        entry_id (int): Entry ID to retrieve

    Returns:
        Dict[str, Any]: JSON response containing entry information

    Raises:
        BdRENFinanceAPIError: If the API request fails
        BdRENFinanceValidationError: If entry_id is invalid

    Example:
        >>> entry = get_entry(12345)
        >>> print(entry)
    """
    # Validate input
    if not isinstance(entry_id, int) or entry_id <= 0:
        raise BdRENFinanceValidationError(f'Invalid entry_id: {entry_id}. Must be a positive integer.')

    session = None
    try:
        session = finance_login_session()

        url = f'{BASE_URL}entry/{entry_id}/'

        logger.debug(f'Fetching entry with ID: {entry_id}')

        res = session.get(url, verify=False, timeout=30)
        res.raise_for_status()

        response_data = res.json()
        logger.info(f'Successfully retrieved entry with ID: {entry_id}')

        return response_data

    except requests.exceptions.Timeout as e:
        logger.error(f'Timeout while fetching entry {entry_id}: {e}')
        raise BdRENFinanceAPIError(f'Request timeout: {str(e)}')
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error while fetching entry {entry_id}: {e}')
        if e.response and e.response.status_code == 404:
            raise BdRENFinanceAPIError(
                f'Entry with ID {entry_id} not found',
                status_code=404
            )
        raise BdRENFinanceAPIError(
            f'HTTP error: {str(e)}',
            status_code=e.response.status_code if e.response else None
        )
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error while fetching entry {entry_id}: {e}')
        raise BdRENFinanceAPIError(f'Request failed: {str(e)}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse JSON response: {e}')
        raise BdRENFinanceAPIError(f'Invalid JSON response: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error while fetching entry {entry_id}: {e}')
        raise BdRENFinanceAPIError(f'Unexpected error: {str(e)}')
    finally:
        if session:
            session.close()
            logger.debug('Session closed')


def update_entry(trans_id: int, payload: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Update entry in BdREN Finance API.

    Args:
        trans_id (int): Transaction/Entry ID to update
        payload (Union[Dict[str, Any], str]): Entry data as dictionary or JSON string

    Returns:
        Dict[str, Any]: JSON response containing updated entry information

    Raises:
        BdRENFinanceAPIError: If the API request fails
        BdRENFinanceValidationError: If trans_id or payload is invalid

    Example:
        >>> payload = {
        ...     "transNo": "TR-12345",
        ...     "transDate": "2026-01-22",
        ...     "generalParticular": "Updated general Particular",
        ...     "vouchers": [
        ...         {
        ...             "accountNo": 15600005,
        ...             "drAmount": 150,
        ...             "crAmount": 0,
        ...             "particular": "Updated debit entry",
        ...             "type": "dr"
        ...         },
        ...         {
        ...             "accountNo": 16600114,
        ...             "drAmount": 0,
        ...             "crAmount": 150,
        ...             "particular": "Updated credit entry",
        ...             "type": "cr"
        ...         }
        ...     ]
        ... }
        >>> result = update_entry(12345, payload)
        >>> print(result)
    """
    # Validate input
    if not isinstance(trans_id, int) or trans_id <= 0:
        raise BdRENFinanceValidationError(f'Invalid trans_id: {trans_id}. Must be a positive integer.')

    session = None
    try:
        # Validate payload
        if isinstance(payload, dict):
            if 'vouchers' not in payload:
                raise BdRENFinanceValidationError('Payload must contain "vouchers" field')

            if not isinstance(payload['vouchers'], list) or len(payload['vouchers']) == 0:
                raise BdRENFinanceValidationError('Vouchers must be a non-empty list')

            # Validate voucher structure
            for idx, voucher in enumerate(payload['vouchers']):
                required_fields = ['accountNo', 'drAmount', 'crAmount', 'particular', 'type']
                for field in required_fields:
                    if field not in voucher:
                        raise BdRENFinanceValidationError(
                            f'Voucher at index {idx} is missing required field: {field}'
                        )

        session = finance_login_session()

        headers = {
            'Referer': f'{BASE_URL}entry/edit/{trans_id}/',
            'X-CSRFToken': session.cookies['csrftoken'],
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }

        if isinstance(payload, str):
            json_payload = payload
        else:
            json_payload = json.dumps(payload)

        logger.debug(f'Updating entry {trans_id} with payload: {json_payload[:200]}...')

        response = session.post(
            f'{BASE_URL}entry/edit/{trans_id}/',
            data=json_payload,
            headers=headers,
            verify=False,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        logger.info(f'Successfully updated entry with ID: {trans_id}')

        return response_data

    except requests.exceptions.Timeout as e:
        logger.error(f'Timeout while updating entry {trans_id}: {e}')
        raise BdRENFinanceAPIError(f'Request timeout: {str(e)}')
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error while updating entry {trans_id}: {e}')
        if e.response and e.response.status_code == 404:
            raise BdRENFinanceAPIError(
                f'Entry with ID {trans_id} not found',
                status_code=404
            )
        raise BdRENFinanceAPIError(
            f'HTTP error: {str(e)}',
            status_code=e.response.status_code if e.response else None,
            response_data=e.response.text if e.response else None
        )
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error while updating entry {trans_id}: {e}')
        raise BdRENFinanceAPIError(f'Request failed: {str(e)}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse JSON response: {e}')
        raise BdRENFinanceAPIError(f'Invalid JSON response: {str(e)}')
    except BdRENFinanceValidationError:
        raise
    except Exception as e:
        logger.error(f'Unexpected error while updating entry {trans_id}: {e}')
        raise BdRENFinanceAPIError(f'Unexpected error: {str(e)}')
    finally:
        if session:
            session.close()
            logger.debug('Session closed')
