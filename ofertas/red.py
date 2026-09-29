"""Cliente HTTP educado: reintentos, pausa entre peticiones y user-agent de navegador."""
from __future__ import annotations

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


class Cliente:
    def __init__(self, pausa: float = 1.5, timeout: float = 25):
        self.pausa = pausa
        self.timeout = timeout
        self._ultima = 0.0
        self.sesion = requests.Session()
        self.sesion.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9",
        })
        reintentos = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
                           allowed_methods=["GET"])
        self.sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
        self.sesion.mount("http://", HTTPAdapter(max_retries=reintentos))

    def get(self, url: str, **kwargs) -> requests.Response | None:
        espera = self.pausa - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        self._ultima = time.monotonic()
        try:
            r = self.sesion.get(url, timeout=self.timeout, **kwargs)
        except requests.RequestException as e:
            log.warning("Error de red en %s: %s", url, e)
            return None
        if r.status_code != 200:
            log.debug("HTTP %s en %s", r.status_code, url)
            return None
        return r

    def json(self, url: str, **kwargs):
        r = self.get(url, headers={"Accept": "application/json"}, **kwargs)
        if r is None:
            return None
        try:
            return r.json()
        except ValueError:
            return None
