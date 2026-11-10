"""Proteções da versão pública (demonstração online).

- Limite de envios por pessoa: no máximo N cadastros/pedidos por IP a cada 10 minutos.
- Tamanho máximo do corpo da requisição.
- Cabeçalhos de segurança: o navegador só executa scripts do próprio Enjoy.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https://tile.openstreetmap.org; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)


class ProtecoesDaDemonstracao(BaseHTTPMiddleware):
    def __init__(self, app, max_envios: int = 30, janela_s: int = 600, max_bytes: int = 16_000):
        super().__init__(app)
        self.max_envios, self.janela_s, self.max_bytes = max_envios, janela_s, max_bytes
        self.envios: dict[str, deque] = defaultdict(deque)

    def _ip(self, req: Request) -> str:
        encaminhado = req.headers.get("x-forwarded-for", "")
        return encaminhado.split(",")[0].strip() or (req.client.host if req.client else "?")

    async def dispatch(self, req: Request, call_next):
        if req.method in ("POST", "PUT", "PATCH", "DELETE"):
            tamanho = req.headers.get("content-length")
            if tamanho is None or not tamanho.isdigit() or int(tamanho) > self.max_bytes:
                return JSONResponse({"erro": "Envio muito grande."}, status_code=413)
            agora, fila = time.monotonic(), self.envios[self._ip(req)]
            while fila and agora - fila[0] > self.janela_s:
                fila.popleft()
            if len(fila) >= self.max_envios:
                return JSONResponse(
                    {"erro": "Muitos envios em pouco tempo. Esta é uma demonstração: tente de novo em alguns minutos."},
                    status_code=429,
                )
            fila.append(agora)

        resposta = await call_next(req)
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["X-Frame-Options"] = "DENY"
        if not req.url.path.startswith(("/docs", "/redoc")):  # a página /docs usa scripts próprios
            resposta.headers["Content-Security-Policy"] = CSP
        return resposta
