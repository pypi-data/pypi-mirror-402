import time, random, re
import requests
import logging
from typing import Any, Dict
from .exceptions import MondayAPIError


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def monday_request(
    url: str,
    headers: dict,
    query: str,
    timeout: float | None = None,
    variables: dict | None = None,
    max_retries: int = 5,
    retry_delay: int = 3,
    retry_on_unauth_notfound: bool = True,
    max_unauth_notfound_retries: int = 2,
    ) -> Dict[str, Any]:

    """
    Ejecuta una petición GraphQL contra Monday (POST /v2) con reintentos inteligentes.

    Reintenta por defecto: 5xx, 403, 429, y errores GraphQL de complejidad.
    Opcionalmente reintenta 401/404 (útil si ves fallos transitorios por propagación).
    """

    def _sleep_with_backoff(attempt: int, base_delay: float, hint_seconds: float | None = None) -> None:
        if hint_seconds is not None and hint_seconds > 0:
            time.sleep(hint_seconds); return
        base = base_delay * (2 ** (attempt - 1))
        jitter = base * (0.3 * (2 * random.random() - 1))
        time.sleep(max(0.0, base + jitter))

    unauth_notfound_tries = 0

    for attempt in range(1, max_retries + 1):
        try:
            t0 = time.time()

            if variables is not None:
                payload = {'query':query, 'variables':variables}
            else:
                payload = {'query':query}

            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            dt = (time.time() - t0) * 1000

            req_id = r.headers.get("X-Request-Id")
            rl_remaining = r.headers.get("X-RateLimit-Remaining")
            logger.debug("Monday request_id=%s status=%d time=%.1fms remain=%s",
                        req_id, r.status_code, dt, rl_remaining)

            # 429 Too Many Requests
            if r.status_code == 429:
                body = r.text
                retry_after = r.headers.get("Retry-After")
                wait_secs = None
                try:
                    if retry_after is not None:
                        wait_secs = float(retry_after)
                except ValueError:
                    pass
                logger.warning("HTTP 429 — retry %d/%d (wait=%s)", attempt, max_retries, wait_secs)
                if attempt < max_retries:
                    _sleep_with_backoff(attempt, retry_delay, hint_seconds=wait_secs)
                    continue
                raise MondayAPIError(error_code=r.status_code, query=query, error_message=body)

            # 401/404 — reintentos acotados (opt-in)
            if r.status_code in (401, 404) and retry_on_unauth_notfound:
                unauth_notfound_tries += 1
                # Heurística: si la respuesta sugiere token inválido definitivo, no reintentes.
                body = r.text
                fatal_token = any(
                    s in body.lower()
                    for s in ("invalid token", "invalid api key", "unauthorized client")
                )
                if fatal_token:
                    logger.error("HTTP %d (fatal auth) — %s", r.status_code, body)
                    raise MondayAPIError(error_code=r.status_code, query=query, error_message=body)

                if unauth_notfound_tries <= max_unauth_notfound_retries and attempt < max_retries:
                    logger.warning("HTTP %d — transient? retry %d/%d (sub-unauth %d/%d)",
                                r.status_code, attempt, max_retries,
                                unauth_notfound_tries, max_unauth_notfound_retries)
                    # backoff más corto para 401/404
                    _sleep_with_backoff(unauth_notfound_tries, max(1, retry_delay // 2))
                    continue
                # Agotado presupuesto especial → fallar
                logger.error("HTTP %d — agotado presupuesto de reintentos 401/404", r.status_code)
                raise MondayAPIError(error_code=r.status_code, query=query, error_message=body)

            # 403 — a veces transitorio (WAF/permiso en propagación)
            if r.status_code == 403:
                body = r.text
                logger.warning("HTTP 403 — retry %d/%d", attempt, max_retries)
                if attempt < max_retries:
                    _sleep_with_backoff(attempt, retry_delay)
                    continue
                raise MondayAPIError(error_code=r.status_code, query=query, error_message=body)

            # 5xx — transitorio
            if 500 <= r.status_code < 600:
                body = r.text
                logger.warning("HTTP %d — retry %d/%d", r.status_code, attempt, max_retries)
                if attempt < max_retries:
                    _sleep_with_backoff(attempt, retry_delay)
                    continue
                raise MondayAPIError(error_code=r.status_code, query=query, error_message=body)

            # Parseo JSON
            try:
                resp = r.json()
            except ValueError:
                logger.error("Respuesta no JSON. status=%d body=%s", r.status_code, r.text[:500])
                if attempt < max_retries:
                    _sleep_with_backoff(attempt, retry_delay)
                    continue
                raise MondayAPIError(error_code=r.status_code, query=query, error_message='La respuesta no es un JSON')

            # Errores GraphQL
            if resp.get("errors"):
                errs = resp["errors"]
                first = errs[0] or {}
                ext = first.get("extensions") or {}
                code = ext.get("code")
                path = ".".join(map(str, (first.get("path") or []))) or None

                # Complejidad/presupuesto → reintento
                if code in ("ComplexityException", "COMPLEXITY_BUDGET_EXHAUSTED"):
                    wait_secs = None
                    if "retry_in_seconds" in ext:
                        try: wait_secs = float(ext["retry_in_seconds"])
                        except Exception: pass
                    if wait_secs is None:
                        msg = first.get("message") or ""
                        m = re.findall(r"(\d+(?:\.\d+)?)\s*seconds?", msg)
                        if m:
                            try: wait_secs = float(m[-1])
                            except Exception: pass

                    logger.info("%s path=%s — waiting %ss (retry %d/%d)",
                                code, path, wait_secs, attempt, max_retries)
                    
                    if attempt < max_retries:
                        if wait_secs is None:
                            _sleep_with_backoff(attempt, retry_delay)
                            continue
                        else: 
                            _sleep_with_backoff(attempt, retry_delay, hint_seconds=wait_secs+1)
                        continue

                    raise MondayAPIError(
                        error_code=code,
                        error_message=first.get("message") or "Complexity budget exhausted",
                        query=query
                    )

                # Otros errores GraphQL → falla
                detail = {
                    "message": first.get("message") or "GraphQL error",
                    "code": code,
                    "path": path,
                    "request_id": req_id,
                }
                logger.error("GraphQL error: %s", detail)
                raise MondayAPIError(error_code=code, error_message= detail['message'], query=query)

            return resp

        except requests.RequestException as e:
            logger.warning("RequestException: %s — retry %d/%d", e, attempt, max_retries)
            if attempt < max_retries:
                _sleep_with_backoff(attempt, retry_delay)
                continue
            raise MondayAPIError(error_code= 400, error_message=str(e), query=query)

    raise MondayAPIError(error_code=400, error_message='Max retries reached', query=query)
