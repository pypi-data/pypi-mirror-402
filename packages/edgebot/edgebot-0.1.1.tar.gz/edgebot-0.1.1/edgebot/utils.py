"""
Утилиты для работы с HTTP запросами в EdgeBot SDK
"""

from typing import Any, Optional
from js import fetch as js_fetch, Promise, setTimeout  # type: ignore[attr-defined]


async def sleep(ms: int) -> None:
    """
    Асинхронная задержка через JS setTimeout для Pyodide.
    Args:
        ms: Задержка в миллисекундах
    """
    def executor(resolve, reject):
        setTimeout(lambda: resolve(None), ms)
    await Promise.new(executor)


async def fetch(
    url: str,
    options: Any,
    max_retries: int = 3,
    retry_on_status: Optional[set[int]] = None,
) -> Any:
    """
    Универсальная обертка над js.fetch с ретраями.

    Автоматически повторяет запросы при временных ошибках (5xx, 429, timeouts).
    Используется во всех API вызовах EdgeBot для повышения надежности.

    Args:
        url: URL для запроса
        options: Опции для fetch (уже преобразованные через to_js)
        max_retries: Максимальное количество попыток (по умолчанию 3)
        retry_on_status: Множество HTTP статусов для retry.
                        По умолчанию: {408, 429, 500, 502, 503, 504}

    Returns:
        Response объект от js.fetch

    Raises:
        Exception: Если все попытки исчерпаны или произошла фатальная ошибка
    """
    if retry_on_status is None:
        # Ретраим временные ошибки:
        # 408 - Request Timeout
        # 429 - Too Many Requests (rate limit)
        # 500 - Internal Server Error
        # 502 - Bad Gateway
        # 503 - Service Unavailable
        # 504 - Gateway Timeout
        retry_on_status = {408, 429, 500, 502, 503, 504}

    last_error = None
    last_response = None

    for attempt in range(max_retries):
        try:
            resp = await js_fetch(url, options)
            if resp.ok:
                if attempt > 0:
                    print(f"[edgebot] request succeeded on attempt {attempt + 1}/{max_retries}: {url}")
                return resp
            # Если статус не ok и не требует retry - возвращаем сразу для обработки ошибки
            if resp.status not in retry_on_status:
                return resp

            try:
                err_text = await resp.text()
                err_preview = err_text[:200]
                print(
                    f"[edgebot] retry {attempt + 1}/{max_retries}: "
                    f"status={resp.status} url={url} body={err_preview}"
                )
            except Exception:
                print(f"[edgebot] retry {attempt + 1}/{max_retries}: status={resp.status} url={url}")
            last_response = resp

        except Exception as e:
            # Обрабатываем сетевые ошибки, timeouts и т.д. отлавливая статусы из retry_on_status
            print(f"[edgebot] retry {attempt + 1}/{max_retries}: exception={repr(e)} url={url}")
            last_error = e

        if attempt < max_retries - 1:
            if last_response and last_response.status == 429:
                await sleep(int(last_response.headers.get('Retry-After', 3)) * 1000)
            else:
                print(f"[edgebot] retrying request immediately (attempt {attempt + 2}/{max_retries})...")
    
    # Все попытки исчерпаны
    if last_response:
        print(f"[edgebot] all {max_retries} attempts failed, last status={last_response.status}")
        return last_response  # Возвращаем последний response для финальной обработки ошибки
    
    # Только исключения без response
    print(f"[edgebot] all {max_retries} attempts failed with exceptions")
    raise last_error or Exception(f"Request failed after {max_retries} attempts: {url}")
