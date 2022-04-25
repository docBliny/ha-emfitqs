""" Emfit QS local API access """
import datetime
from decimal import Decimal
import re
import requests
from threading import Lock
import time

import threading
import time

class RepeatedTimer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False

class EmfitQS:
    DEFAULT_UPDATE_RATE = 10
    DISABLE_AUTO_UPDATE = "Disable"

    #################################################
    # Constructors
    #################################################
    def __init__(self, host: str, update_rate=None):
        self._host = host
        self._serial_number = None
        self._timestamp = None
        self._current_datetime = None
        self._uptime = None
        self._presence = None
        self._heart_rate = None
        self._heart_rate_dm = None
        self._respiratory_rate = None
        self._respiratory_rate_dm = None
        self._activity = None
        self._activity_dm = None
        self._firmware_version = None
        self._end = None

        self._last_update = None
        self._session = requests.session()
        self._mutex = Lock()
        self._callback_message = []

        # Control the update rate
        if update_rate is None:
            self._update_rate = datetime.timedelta(seconds=self.DEFAULT_UPDATE_RATE)
        elif update_rate == self.DISABLE_AUTO_UPDATE:
            self._update_rate = self.DISABLE_AUTO_UPDATE
        else:
            self._update_rate = datetime.timedelta(seconds=update_rate)

        if self._update_rate != self.DISABLE_AUTO_UPDATE:
            self.update()
            rt = RepeatedTimer(self._update_rate.total_seconds(), self.update)

    #################################################
    # Public properties
    #################################################
    @property
    def activity(self) -> int:
        return self._activity

    @property
    def activity_dm(self) -> int:
        return self._activity_dm

    @property
    def callback_message(self):
        """Return callback functions when message are received."""
        return self._callback_message

    @property
    def current_datetime(self) -> datetime.datetime:
        return self._current_datetime

    @property
    def end(self) -> bool:
        return self._end

    @property
    def firmware_version(self) -> str:
        return self._firmware_version

    @property
    def heart_rate(self) -> int:
        return self._heart_rate

    @property
    def heart_rate_dm(self) -> int:
        return self._heart_rate_dm

    @property
    def host(self) -> str:
        return self._host

    @property
    def last_update(self) -> datetime:
        return self._last_update

    @property
    def presence(self) -> bool:
        return self._presence

    @property
    def respiratory_rate(self) -> Decimal:
        return self._respiratory_rate

    @property
    def respiratory_rate_dm(self) -> int:
        return self._respiratory_rate_dm

    @property
    def serial_number(self) -> str:
        return self._serial_number

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def update_rate(self):
        return self._update_rate

    @property
    def uptime(self) -> int:
        return self._uptime

    #################################################
    # Public methods
    #################################################
    def add_message_listener(self, callback_message):
        """Add message listener."""
        self._callback_message.append(callback_message)

    def remove_message_listener(self, callback_message):
        """Remove a message listener."""
        if callback_message in self._callback_message:
            self.callback_message.remove(callback_message)

    def clear_message_listener(self):
        """Clear all message listener."""
        self.callback_message.clear()

    def update(self):
        """
        Forces a status update
        :return: None
        """
        self._get_device_data(force_update=True)

    #################################################
    # Private methods
    #################################################
    def _needs_update(self):
        """
        Returns True if an update is needed
        :return: bool
        """
        if self.update_rate == self.DISABLE_AUTO_UPDATE:
            return False
        if self.last_update is None:
            return True
        return datetime.datetime.now() - self.last_update > self.update_rate

    def _get_device_data(self, force_update=False) -> bool:
        """
        Updates device state if a refresh is due or forced.
        :param force_update: bool - Forces an update
        :return: bool
        """
        with self._mutex:
            result = False
            if self._needs_update() or force_update is True:
                request = self._get_url("http://" + self.host + "/dvmstatus.htm")
                if request and request.status_code == 200:
                    result = self._parse_device_data(request.text)
                    if result:
                        self._last_update = datetime.datetime.now()

                        # Notify listeners
                        for function in self.callback_message:
                            function(self)
                    else:
                        raise Exception("No data received")
                else:
                    self._check_response(
                        "Failed to get device status page", request)

            return result

    @staticmethod
    def _check_response(error_text, request):
        """
        Checks the request response, throws exception with the description text
        :param error_text: str
        :param request: response
        :return: None
        """
        if request is None or request.status_code != 200:
            if request is not None:
                response = ""
                for key in request.__attrs__:
                    response += f"  {key}: {getattr(request, key)}\n"
                raise Exception(f"{error_text}\n{response}")
            raise Exception(f"No response from device. {error_text}")

    def _get_url(self, request_url):
        """
        Returns the full session.get from the URL (ROOT_URL + url)
        :param request_url: str
        :return: response
        """
        # Let the code throw the exception
        # try:
        #     r = self._session.get(request_url, allow_redirects=False)
        # except requests.RequestException as e:
        #     print("Error getting url", str(e))
        #     return None
        request = self._session.get(request_url, allow_redirects=False)

        self._check_response("Failed to GET url", request)
        return request

    def _parse_device_data(self, data):
        result = False
        pattern = re.compile(r'([A-Z_]+)=(.*)(?:\r\n)*<br>')

        for match in re.finditer(pattern, data):
            if match.group(1) == "SER":
                result = True
                # Serial number
                self._serial_number = match.group(2)
            elif match.group(1) == "TS":
                result = True
                # Timestamp
                self._timestamp = match.group(2)
                if match.group(2) != "0":
                    # Time hasn't synced yet if its zero
                    self._current_datetime = datetime.datetime.utcfromtimestamp(int(match.group(2)))
            elif match.group(1) == "TS_R":
                result = True
                # Timestamp relative to power on
                self._uptime = match.group(2)
            elif match.group(1) == "PRES":
                # Presence
                if match.group(2) == "0":
                    result = True
                    self._presence = "off"
                elif match.group(2) == "1":
                    result = True
                    self._presence = "on"
            elif match.group(1) == "HR":
                result = True
                # Heartrate BPM
                self._heart_rate = int(match.group(2))
            elif match.group(1) == "HR_DM":
                result = True
                # Unknown
                self._heart_rate_dm = int(match.group(2))
            elif match.group(1) == "RR":
                result = True
                # Respiratory rate, per minute
                self._respiratory_rate = Decimal(match.group(2))
            elif match.group(1) == "RR_DM":
                result = True
                # Unknown
                self._respiratory_rate_dm = int(match.group(2))
            elif match.group(1) == "ACT":
                result = True
                # Activity
                self._activity = int(match.group(2))
            elif match.group(1) == "ACT_DM":
                result = True
                # Unknown
                self._activity_dm = int(match.group(2))
            elif match.group(1) == "FW":
                result = True
                # Firmware version
                self._firmware_version = match.group(2)
            elif match.group(1) == "END":
                # Unknown (session end?)
                if match.group(2) == "0":
                    result = True
                    self._end = "off"
                elif match.group(2) == "1":
                    result = True
                    self._end = "on"

        return result
