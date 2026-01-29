import json
import sys
import traceback
from functools import partial, wraps

from requests.exceptions import InvalidURL
from sifflet_sdk.client import ApiException
from sifflet_sdk.configure.service import ConfigureService
from sifflet_sdk.logger import logger
from urllib3.exceptions import HTTPError, LocationParseError


class SiffletConfigError(Exception):
    """Raised when missing an environment variable"""


class SiffletRuntimeError(Exception):
    """Raised on error sifflet SDK"""


class SiffletRunRuleFail(Exception):
    """Raised when a rule is on fail"""


def exception_handler(func):
    if not func:
        return partial(exception_handler)

    @wraps(func)
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (InvalidURL, LocationParseError) as err:
            logger.debug(traceback.format_exc())
            logger.error(f"Unable to parse url, please check the configuration of your tenant name. Error='{err}'")
            sys.exit(1)
        except HTTPError as err:
            logger.debug(traceback.format_exc())
            logger.error(f'Unable to call Sifflet API, please check configuration. Error="{err}"')
            sys.exit(1)
        except ApiException as err:
            logger.debug(traceback.format_exc())
            if err.body:
                error_body = json.loads(err.body)
                logger.error(
                    f"{err.status} - {error_body['title'] if 'title' in error_body else ''} -"
                    f" {error_body['detail'] if 'detail' in error_body else ''}",
                    extra={"markup": False},
                )
            else:
                logger.error(err, extra={"markup": False})
            sys.exit(1)
        except SiffletRuntimeError as err:
            logger.debug(traceback.format_exc())
            logger.error(err, extra={"markup": False})
            sys.exit(1)
        except SiffletRunRuleFail as err:
            logger.debug(traceback.format_exc())
            logger.error(err, extra={"markup": False})
            sys.exit(1)
        except Exception as err:  # pylint: disable=W0703
            logger.debug(traceback.format_exc())
            logger.error(err, extra={"markup": False})
            sys.exit(1)

    return inner_function


def config_needed_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        sifflet_config = args[1]
        if not ConfigureService().validate(sifflet_config):
            sys.exit(1)

        return func(*args, **kwargs)

    return wrapper
