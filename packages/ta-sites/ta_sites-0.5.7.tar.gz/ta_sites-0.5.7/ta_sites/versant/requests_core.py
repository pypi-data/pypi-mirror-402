import json
import os
import time
from datetime import timedelta
from threading import Event, Thread

import logging

import requests
from RPA.Browser.Playwright import Playwright
from Browser.utils import SelectAttribute
from Browser.utils.data_types import ElementState, PageLoadStates
from retry import retry
from fake_useragent import UserAgent
from .exceptions import VersantError, BadRequestError, WrongCredentialsError, BrowserError


def retry_if_bad_request(func):
    attempt = 1
    tries = 3

    @retry(exceptions=BadRequestError, tries=tries, delay=1, backoff=2)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadRequestError as ex:
            nonlocal attempt
            print(f"Bad request Attempt {attempt}...", "WARN")
            attempt = attempt + 1 if attempt < tries else 1
            raise ex

    return wrapper


class VersantRequestsCore:
    def __init__(
        self,
        login: str,
        password: str,
        url: str = "https://ecp.versanthealth.com/prelogin/login",
        validation_fields: dict = None,
    ):
        """
        VersantSuperiorRequestsCore object. Please Inheritance it.

        :param login: login for CentralReach site.
        :param password: password for CentralReach site.
        """
        self.session = requests.session()
        # usable user-agent
        self.user_agent = UserAgent().chrome
        # Login data
        self.__login = login
        self.__password = password
        self.__url = url
        self.__validation_fields = validation_fields

        self.output_folder = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output")

        self._transaction_id = ""  # Get from login response
        self._user_id = login

        # Get from local storage
        self._tax_id = ""
        self._bearer_token = ""
        self._bearer_token_type = ""
        self._bearer_token_expired_in = ""  # TODO implement refresh
        self._bearer_refresh_token = ""  # TODO implement refresh

        self._login_to_versant(self.__login, self.__password, self.__url, self.__validation_fields)

    @staticmethod
    def __setup_browser(open_as_headless=True):
        """
        Open new browser and apply settings
        """
        from Browser import SupportedBrowsers

        browser = Playwright()
        browser.set_browser_timeout(timedelta(seconds=100))
        browser.new_browser(SupportedBrowsers.chromium, headless=open_as_headless, timeout=timedelta(seconds=120))
        browser.new_context(userAgent=UserAgent().chrome)
        browser.new_page()
        return browser

    @staticmethod
    def _is_json_response(response) -> bool:
        try:
            response.json()
            return True
        except json.decoder.JSONDecodeError:
            return False

    def check_response(
        self,
        response,
        mandatory_json: bool = False,
        exc_message: str = "",
        re_authorize: bool = True,
        check_resp_obj: bool = False,
    ) -> None:
        """
        This method check response and raise exception 'BadRequestError'
        If status code is 401 (unauthorized) then it will try login again
        :param response: response from request
        :param mandatory_json: bool, if True - it will check is response contain json data
        :param exc_message: text message which will be raise if response wrong
        :param re_authorize: bool, if True then it will try login again if status code is 401
        """
        if re_authorize and response.status_code == 401:
            self._login_to_versant(self.__login, self.__password, self.__url, self.__validation_fields)
            raise BadRequestError(
                f"{exc_message}Status Code: {response.status_code} (Unauthorized request), "
                f"Json content: {response.json()}, Headers: {response.headers}"
            )

        if response.status_code != 200 or (mandatory_json and not self._is_json_response(response)):
            exc_message = exc_message + "\n" if exc_message else ""
            if self._is_json_response(response):
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, "
                    f"Json content: {response.json()}, Headers: {response.headers}"
                )
            else:
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, " f"Headers: {response.headers}"
                )
        if check_resp_obj:
            response_json = response.json()
            if "body" not in response_json:
                raise VersantError("Response doesn't contain body")

            if "responseObject" not in response_json["body"]:
                if "messages" in response_json["body"] and response_json["body"]["messages"]:
                    messages = []
                    for message in response_json["body"]["messages"]:
                        messages.append(
                            f"{message['errorIdentifier'] if 'errorIdentifier' in message else '-'}: "
                            f"{message['description']}"
                        )
                    messages_str = "\n".join(messages)
                    raise VersantError(
                        "Response doesn't contain 'responseObject', " f"error messages: \n{messages_str}"
                    )
                else:
                    raise VersantError("Response doesn't contain 'responseObject'")

    def _fill_and_submit_validation_form(self, browser: Playwright, validation_fields: dict):
        """Fill and submit the provider validation form."""
        try:
            browser.fill_text('//input[@name="officeNumber"]', validation_fields["officeNumber"])
            browser.fill_text('//input[@name="officeName"]', validation_fields["officeName"])
            browser.fill_text('//input[@name="officeStreet"]', validation_fields["officeStreet"])
            browser.fill_text('//input[@name="officeSuite"]', validation_fields["officeSuite"])
            browser.fill_text('//input[@name="officeCity"]', validation_fields["officeCity"])
            browser.select_options_by(
                "//select[@name='officeState']", SelectAttribute.value, f"{validation_fields['officeState']}"
            )
            browser.fill_text('//input[@name="officeZip"]', validation_fields["officeZip"])
            browser.fill_text('//input[@name="phoneNumber"]', validation_fields["phoneNumber"])

            browser.click('//*[@id="viewSummary"]')
            browser.wait_for_elements_state('//*[@id="submitRequest"]', timeout=timedelta(seconds=120))
            browser.click('//*[@id="submitRequest"]')
        except Exception as ex:
            logging.error(f"Error filling and submitting validation form: {ex}")
            raise ex

    def _is_validation_page_present(self, browser: Playwright) -> bool:
        """Check if the validation page is currently displayed."""
        try:
            logging.info("Checking if validation page is present...")
            browser.wait_for_elements_state(
                '//*[text()="Help with provider portal access"]',
                state=ElementState.visible,
                timeout=timedelta(seconds=5),
            )
            return True
        except Exception:
            logging.debug("Validation page not found.")
            return False

    def _check_for_blocked_page(self, browser: Playwright) -> None:
        """Check if we've been blocked by Cloudflare and take a screenshot if so."""
        try:
            browser.wait_for_elements_state(
                '//*[@id="cf-error-details"]', state=ElementState.visible, timeout=timedelta(seconds=5)
            )
            # If we get here, we found the blocked page
            logging.error("Blocked by Cloudflare - taking screenshot")
            screenshot_path = os.path.join(self.output_folder, f"blocked_page_{int(time.time())}.png")
            browser.take_screenshot(screenshot_path)
            raise VersantError(f"Access blocked by Cloudflare. Screenshot saved to: {screenshot_path}")
        except VersantError:
            raise  # Re-raise our custom error
        except Exception:
            # Element not found (timeout) means we're not blocked - this is expected
            pass

    def _handle_validation_page(self, browser: Playwright, url: str, validation_fields: dict) -> None:
        """
        Handle the validation page flow: submit form, wait, and refresh the page.

        Keeps the same browser instance to preserve cookies and session data.
        """
        logging.info("Versant validation page found")

        if not validation_fields:
            raise VersantError("Validation fields are required but not provided")

        self._fill_and_submit_validation_form(browser, validation_fields)

        # Wait 5 minutes before refreshing (keep browser open to preserve cookies)
        WAIT_TIME_IN_SECONDS = 300
        logging.info(f"Validation form submitted. Waiting {WAIT_TIME_IN_SECONDS} seconds before refreshing...")
        time.sleep(WAIT_TIME_IN_SECONDS)

        # Refresh the page by navigating to the URL again
        logging.info("Refreshing page after validation form submission...")
        browser.go_to(url=url, timeout=timedelta(seconds=180), wait_until=PageLoadStates.domcontentloaded)

        # Check if we've been blocked
        self._check_for_blocked_page(browser)

        # Check if validation page appears again
        if self._is_validation_page_present(browser):
            raise VersantError(
                "Validation page appeared again after form submission. "
                "The validation request may not have been processed correctly."
            )

    def _submit_credentials_and_capture_response(self, browser: Playwright, login: str, password: str) -> dict:
        """Submit login credentials and capture the login API response."""
        browser.wait_for_elements_state('//*[@id="username"]', timeout=timedelta(seconds=120))
        browser.fill_text('//*[@id="username"]', login)
        browser.click('//button[@type="submit"]')

        browser.wait_for_elements_state('//*[@id="password"]', timeout=timedelta(seconds=120))
        browser.fill_text('//*[@id="password"]', password)

        # Capture the login response using a background thread
        response = {}

        def wait_for_response(ev: Event):
            nonlocal response
            login_url = "https://api.versanthealth.com/AccessManagementSecured/api/AccessManagement/Login"
            response = browser.wait_for_response(login_url, timeout=timedelta(seconds=60))
            ev.set()

        event = Event()
        t1 = Thread(target=wait_for_response, args=(event,))
        t1.start()

        time.sleep(1)
        browser.click('//button[@type="submit"]')  # Click the Login button
        is_event_succ = event.wait(600.0)

        if not is_event_succ:
            raise BrowserError("Timeout of 600 seconds reached on login.")

        return response

    def _validate_login_response(self, response: dict) -> None:
        """Validate the login response and raise appropriate errors."""
        response_body = response["body"]["body"]
        if response_body["statuscode"] != "OK":
            if response_body["messages"]:
                error_message: dict = response_body["messages"][0]
                if error_message["code"] == "11.01.05":
                    raise WrongCredentialsError(
                        "Versant login attempt failed due to incorrect credentials. "
                        f"Details: {error_message['description']}"
                    )
            raise VersantError("Can't login to Versant")

    def _extract_tokens_from_browser(self, browser: Playwright, response: dict) -> None:
        """Extract authentication tokens from browser local storage and response."""
        self._transaction_id = response["body"]["header"]["transactionid"]
        self._tax_id = json.loads(browser.local_storage_get_item("userDetails"))["taxId"]

        bearer_token_data = json.loads(browser.local_storage_get_item("bearerToken"))
        self._bearer_token = bearer_token_data["access_token"]
        self._bearer_token_type = bearer_token_data["token_type"]
        self._bearer_token_expired_in = bearer_token_data["expires_in"]
        self._bearer_refresh_token = bearer_token_data["refresh_token"]

        if not self._bearer_token:
            raise BadRequestError(
                "Session doesn't contain the required cookie 'bearer-token' after logging into Versant"
            )

    @retry(BrowserError, tries=2)
    def _login_to_versant(self, login: str, password: str, url: str, validation_fields: dict = None):
        """Perform the complete Versant login flow."""
        browser = None
        try:
            try:
                browser = self.__setup_browser()
                browser.go_to(url=url, timeout=timedelta(seconds=180), wait_until=PageLoadStates.domcontentloaded)

                # Check if we've been blocked
                self._check_for_blocked_page(browser)

                # Handle validation page if present
                if self._is_validation_page_present(browser):
                    self._handle_validation_page(browser, url, validation_fields)

                # Submit credentials and get response
                response = self._submit_credentials_and_capture_response(browser, login, password)

            except Exception as ex:
                raise BrowserError(f"Can't login to Versant. Exception: {ex}") from ex

            # Validate response and extract tokens
            self._validate_login_response(response)
            self._extract_tokens_from_browser(browser, response)

            # Verify authorization works
            try:
                self.get_office_locations_by_tax_id()
            except BadRequestError:
                raise BadRequestError("Session is unauthorized after login to Versant")
        finally:
            if browser is not None:
                browser.close_browser("CURRENT")

    @retry_if_bad_request
    def get_office_locations_by_tax_id(self):
        url = "https://api.versanthealth.com/ProviderService/GetOfficeLocationsByTaxId"
        response = self.session.post(url, headers=self.get_headers(), json=self.get_payload())

        exception_message = "Problems with getting office by tax id."
        self.check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()

    def get_payload(self, body_payload: dict = {}) -> dict:
        return {
            "header": {"transactionId": self._transaction_id, "userId": self._user_id, "taxId": self._tax_id},
            "body": body_payload,
        }

    def get_headers(self, is_json=True, put_token=True, add_headers: dict = None) -> dict:
        """
        Prepare header object for request.

        :param is_json (bool): True if content-type should be json, else False.
        :param put_token (bool): True if 'csrf-token' should be added to headers, else False.
        :param add_headers (dict): dictionary with key-values that should be added to headers.
        """
        headers = {}
        if is_json:
            headers["Content-Type"] = "application/json"

        if put_token:
            headers["Authorization"] = f"{self._bearer_token_type} {self._bearer_token}"

        if add_headers:
            for key, value in add_headers.items():
                headers[key] = value
        return headers
