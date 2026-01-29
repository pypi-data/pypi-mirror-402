import requests
import uuid


class TorSession(requests.Session):
    """
    requests.Session ثابتة
    + Tor proxy
    + تغيير IP لكل كارت أو كل N كارت
    """

    def __init__(
        self,
        tor_host="127.0.0.1",
        tor_port=9050,
        timeout=25,
        rotate_every=1  # DEFAULT فقط
    ):
        super().__init__()

        self.tor_host = tor_host
        self.tor_port = tor_port
        self.timeout = timeout
        self.rotate_every = rotate_every

        self._auth = uuid.uuid4().hex
        self._card_index = 0

    def next_card(self):
        """
        تناديها مرة واحدة لكل كارت
        """
        self._card_index += 1
        if (self._card_index - 1) % self.rotate_every == 0:
            self._auth = uuid.uuid4().hex

    def _proxies(self):
        proxy = f"socks5h://{self._auth}:x@{self.tor_host}:{self.tor_port}"
        return {
            "http": proxy,
            "https": proxy,
        }

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("proxies", self._proxies())
        return super().request(method, url, **kwargs)
