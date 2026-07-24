import json
import re
import sys
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView


BASE_URL = "https://assessoriavip.com.br"


class AssessoriaContext(QObject):
    context_ready = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.context = {
            "token": None,
            "event_id": None,
            "referrer_path": None,
            "user_raw": None,
            "current_url": None,
        }

    def set_context(
        self,
        token: Optional[str],
        event_id: Optional[int],
        referrer_path: Optional[str],
        user_raw: Optional[str],
        current_url: Optional[str],
    ):
        self.context["token"] = token
        self.context["event_id"] = event_id
        self.context["referrer_path"] = referrer_path
        self.context["user_raw"] = user_raw
        self.context["current_url"] = current_url

        if token and event_id:
            self.context_ready.emit(self.context)


class AssessoriaLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conectar Assessoria VIP")
        self.resize(1200, 800)

        self.ctx = AssessoriaContext()

        self._capturado = False
        self._polling = False
        self._tentando_autoir_mapping = False
        self._ultima_url = ""
        self._ultimo_event_id = None

        self.status_label = QLabel(
            "Faça login no Assessoria VIP. Depois do login, o sistema tentará localizar o evento e abrir o mapeamento automaticamente."
        )

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(BASE_URL))

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.browser)
        self.setLayout(layout)

        self.browser.urlChanged.connect(self.on_url_changed)
        self.ctx.status_changed.connect(self.status_label.setText)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1800)
        self.poll_timer.timeout.connect(self.poll_context)

    def on_url_changed(self, url: QUrl):
        url_str = url.toString()
        self._ultima_url = url_str

        if self._capturado:
            return

        self.status_label.setText(f"URL atual: {url_str}")

        if "/mapping" in url_str and "invitationManagement" in url_str:
            self.status_label.setText("Tela de mapeamento detectada. Capturando conexão...")
            QTimer.singleShot(800, self.capture_context)
            return

        if not self._polling:
            self._polling = True
            self.poll_timer.start()

    def poll_context(self):
        if self._capturado:
            self.poll_timer.stop()
            return

        js = """
        (() => {
            const userRaw = localStorage.getItem("user");
            const referrerPath = localStorage.getItem("apollo-cache-persist-referrer-path");
            const href = window.location.href;

            let token = null;
            let eventId = null;

            if (userRaw) {
                try {
                    const user = JSON.parse(userRaw);
                    token = user?.token || null;
                } catch (e) {}
            }

            const candidates = new Set();

            const tryExtract = (txt) => {
                if (!txt) return;
                const patterns = [
                    /invitationManagement\\/(\\d+)\\/mapping/i,
                    /invitationManagement\\/(\\d+)/i,
                    /event(?:o)?[\\/_:-]?(\\d{3,})/i
                ];
                for (const p of patterns) {
                    const m = String(txt).match(p);
                    if (m && m[1]) candidates.add(m[1]);
                }
            };

            tryExtract(href);
            tryExtract(referrerPath);

            const links = Array.from(document.querySelectorAll("a[href], button, [role='button']"))
                .map(el => {
                    const href = el.getAttribute("href") || "";
                    const text = (el.innerText || el.textContent || "").trim();
                    return { href, text };
                });

            for (const item of links) {
                tryExtract(item.href);
                tryExtract(item.text);
            }

            if (candidates.size > 0) {
                eventId = parseInt(Array.from(candidates)[0], 10);
            }

            return JSON.stringify({
                token,
                event_id: eventId,
                referrer_path: referrerPath,
                current_url: href,
                user_raw: userRaw,
                links
            });
        })();
        """
        self.browser.page().runJavaScript(js, self._handle_poll_result)

    def _handle_poll_result(self, result):
        if self._capturado or not result:
            return

        try:
            data = json.loads(result)
        except Exception:
            self.status_label.setText("Erro ao interpretar os dados da página.")
            return

        token = data.get("token")
        event_id = data.get("event_id")
        current_url = data.get("current_url")
        referrer_path = data.get("referrer_path")
        user_raw = data.get("user_raw")
        links = data.get("links") or []

        if not token:
            self.status_label.setText("Aguardando login no Assessoria VIP...")
            return

        if event_id and "/mapping" in str(current_url):
            self.status_label.setText("Conexão identificada. Finalizando captura...")
            self._finalizar(token, event_id, referrer_path, user_raw, current_url)
            return

        if event_id and not self._tentando_autoir_mapping:
            self._ultimo_event_id = event_id
            self._tentando_autoir_mapping = True
            mapping_url = f"{BASE_URL}/invitationManagement/{event_id}/mapping"
            self.status_label.setText(f"Evento identificado ({event_id}). Abrindo mapeamento automaticamente...")
            self.browser.setUrl(QUrl(mapping_url))
            QTimer.singleShot(1400, self.capture_context)
            return

        if not event_id:
            mapping_link = self._buscar_link_mapping(links)
            if mapping_link and not self._tentando_autoir_mapping:
                self._tentando_autoir_mapping = True
                self.status_label.setText("Link de mapeamento encontrado. Abrindo automaticamente...")
                self.browser.setUrl(QUrl(self._absolutizar_url(mapping_link)))
                QTimer.singleShot(1400, self.capture_context)
                return

            event_link = self._buscar_link_evento(links)
            if event_link and not self._tentando_autoir_mapping:
                self._tentando_autoir_mapping = True
                self.status_label.setText("Evento encontrado. Entrando automaticamente...")
                self.browser.setUrl(QUrl(self._absolutizar_url(event_link)))
                QTimer.singleShot(1600, self._liberar_nova_tentativa)
                return

        self.status_label.setText("Login detectado. Procurando evento automaticamente...")

    def _liberar_nova_tentativa(self):
        self._tentando_autoir_mapping = False

    def _buscar_link_mapping(self, links: list[dict]) -> Optional[str]:
        for item in links:
            href = str(item.get("href") or "")
            text = str(item.get("text") or "").lower()
            if "mapping" in href.lower():
                return href
            if "mapeamento" in text:
                return href if href else None
        return None

    def _buscar_link_evento(self, links: list[dict]) -> Optional[str]:
        for item in links:
            href = str(item.get("href") or "")
            low = href.lower()
            if "invitationmanagement/" in low and "mapping" not in low:
                return href
        return None

    def _absolutizar_url(self, href: str) -> str:
        if href.startswith("http://") or href.startswith("https://"):
            return href
        if href.startswith("/"):
            return f"{BASE_URL}{href}"
        return f"{BASE_URL}/{href}"

    def capture_context(self):
        js = """
        (() => {
            const userRaw = localStorage.getItem("user");
            const referrerPath = localStorage.getItem("apollo-cache-persist-referrer-path");
            const href = window.location.href;

            let token = null;
            let eventId = null;

            if (userRaw) {
                try {
                    const user = JSON.parse(userRaw);
                    token = user?.token || null;
                } catch (e) {}
            }

            const patterns = [
                /invitationManagement\\/(\\d+)\\/mapping/i,
                /invitationManagement\\/(\\d+)/i
            ];

            for (const p of patterns) {
                const m1 = String(href || "").match(p);
                if (m1 && m1[1]) {
                    eventId = parseInt(m1[1], 10);
                    break;
                }

                const m2 = String(referrerPath || "").match(p);
                if (m2 && m2[1]) {
                    eventId = parseInt(m2[1], 10);
                    break;
                }
            }

            return JSON.stringify({
                token,
                event_id: eventId,
                referrer_path: referrerPath,
                current_url: href,
                user_raw: userRaw
            });
        })();
        """
        self.browser.page().runJavaScript(js, self._handle_capture_result)

    def _handle_capture_result(self, result):
        self._tentando_autoir_mapping = False

        if not result:
            self.status_label.setText("Não foi possível capturar os dados da conexão.")
            return

        try:
            data = json.loads(result)
        except Exception:
            self.status_label.setText("Erro ao ler os dados capturados.")
            return

        token = data.get("token")
        event_id = data.get("event_id")
        referrer_path = data.get("referrer_path")
        current_url = data.get("current_url")
        user_raw = data.get("user_raw")

        if not token:
            self.status_label.setText("Login ainda não detectado. Continue o login normalmente.")
            return

        if not event_id:
            self.status_label.setText("Login detectado, mas o evento ainda não foi identificado. Procurando automaticamente...")
            return

        self._finalizar(token, event_id, referrer_path, user_raw, current_url)

    def _finalizar(self, token, event_id, referrer_path, user_raw, current_url):
        if self._capturado:
            return

        self._capturado = True
        self.poll_timer.stop()

        self.ctx.set_context(
            token=token,
            event_id=event_id,
            referrer_path=referrer_path,
            user_raw=user_raw,
            current_url=current_url,
        )
        self.status_label.setText(f"Assessoria VIP conectado com sucesso. Evento: {event_id}")
        QTimer.singleShot(900, self.close)


def abrir_login_assessoria():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = AssessoriaLoginWindow()
    resultado = {}

    def on_ready(ctx: dict):
        nonlocal resultado
        resultado = ctx

    window.ctx.context_ready.connect(on_ready)
    window.show()
    app.exec()

    return resultado