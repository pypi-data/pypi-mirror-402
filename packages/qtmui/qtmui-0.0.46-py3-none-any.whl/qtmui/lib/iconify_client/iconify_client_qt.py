from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from qtmui.lib.iconify_client.iconify_cache import svg_cache, cache_key


ICONIFY_ROOT = "https://api.iconify.design"


class IconifyClientQt(QObject):

    apiFinished = Signal(str, object)
    apiError = Signal(str, str)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = IconifyClientQt()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.memory_cache: dict[str, Any] = {}

    # ---------------------------------------------------------
    def _make_url(self, path: str, params: dict = None) -> QUrl:
        url = QUrl(f"{ICONIFY_ROOT}/{path}")
        if params:
            q = QUrlQuery()
            for k, v in params.items():
                if v is not None:
                    q.addQueryItem(k, str(v))
            url.setQuery(q)
        return url

    # ---------------------------------------------------------
    def svg(self, prefix: str, name: str, **kwargs):
        args = (prefix, name)
        cache_id = cache_key(args, kwargs, "0")

        disk = svg_cache()
        if cache_id in disk:
            self.apiFinished.emit(f"svg:{cache_id}", disk[cache_id])
            return

        url = self._make_url(f"{prefix}/{name}.svg", kwargs)
        reply = self.manager.get(QNetworkRequest(url))

        def done():
            if reply.error() != QNetworkReply.NoError:
                self.apiError.emit(f"svg:{cache_id}", reply.errorString())
                reply.deleteLater()
                return

            raw = bytes(reply.readAll())
            disk[cache_id] = raw
            self.apiFinished.emit(f"svg:{cache_id}", raw)

            reply.deleteLater()

        reply.finished.connect(done)


def iconify_client():
    return IconifyClientQt.instance()
