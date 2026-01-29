"""
BFK AuthSystem - Retry Handler

Implementa retry com backoff exponencial para requisicoes HTTP.
"""

import time
import random
import logging
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps

from .exceptions import NetworkError, ServerError, TimeoutError as AuthTimeoutError


logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """
    Configuracao para retry handler.

    Attributes:
        max_retries: Numero maximo de tentativas (padrao: 3)
        base_delay: Delay base em segundos (padrao: 1.0)
        max_delay: Delay maximo em segundos (padrao: 30.0)
        backoff_factor: Fator de multiplicacao do delay (padrao: 2.0)
        jitter: Adiciona variacao aleatoria ao delay (padrao: True)
        jitter_factor: Fator de variacao (0.0 a 1.0, padrao: 0.1)
        retryable_exceptions: Excecoes que devem ser retentadas
        retryable_status_codes: Status codes HTTP para retry (5xx)
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.1,
        retryable_exceptions: List[Type[Exception]] = None,
        retryable_status_codes: List[int] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.retryable_exceptions = retryable_exceptions or [
            NetworkError,
            ServerError,
            AuthTimeoutError,
            ConnectionError,
            TimeoutError,
        ]
        self.retryable_status_codes = retryable_status_codes or [
            500, 502, 503, 504, 520, 521, 522, 523, 524
        ]


class RetryHandler:
    """
    Handler para retry com backoff exponencial.

    Exemplo de uso:
        handler = RetryHandler(config)

        @handler.retry
        def fazer_requisicao():
            return requests.get(url)

        # Ou diretamente:
        result = handler.execute(fazer_requisicao)
    """

    def __init__(self, config: RetryConfig = None):
        """
        Inicializa o handler.

        Args:
            config: Configuracao de retry (usa padrao se nao fornecido)
        """
        self.config = config or RetryConfig()
        self._attempt = 0

    def calculate_delay(self, attempt: int) -> float:
        """
        Calcula o delay para uma tentativa especifica.

        Args:
            attempt: Numero da tentativa (0-based)

        Returns:
            Delay em segundos
        """
        # Backoff exponencial: base_delay * (backoff_factor ^ attempt)
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)

        # Limitar ao maximo
        delay = min(delay, self.config.max_delay)

        # Adicionar jitter para evitar thundering herd
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def should_retry(self, exception: Exception) -> bool:
        """
        Verifica se a excecao deve ser retentada.

        Args:
            exception: Excecao lancada

        Returns:
            True se deve tentar novamente
        """
        for exc_type in self.config.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True

        # Verificar status code se for um erro de requisicao
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            if exception.response.status_code in self.config.retryable_status_codes:
                return True

        return False

    def execute(
        self,
        func: Callable[[], T],
        on_retry: Callable[[int, Exception, float], None] = None
    ) -> T:
        """
        Executa uma funcao com retry.

        Args:
            func: Funcao a ser executada
            on_retry: Callback chamado antes de cada retry (attempt, exception, delay)

        Returns:
            Resultado da funcao

        Raises:
            Exception: Ultima excecao se todas as tentativas falharem
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            self._attempt = attempt

            try:
                return func()

            except Exception as e:
                last_exception = e

                # Verificar se e a ultima tentativa
                if attempt >= self.config.max_retries:
                    logger.warning(
                        f"Todas as {self.config.max_retries + 1} tentativas falharam"
                    )
                    raise

                # Verificar se a excecao deve ser retentada
                if not self.should_retry(e):
                    logger.debug(f"Excecao nao retentavel: {type(e).__name__}")
                    raise

                # Calcular delay
                delay = self.calculate_delay(attempt)

                logger.info(
                    f"Tentativa {attempt + 1}/{self.config.max_retries + 1} falhou: "
                    f"{type(e).__name__}. Retry em {delay:.2f}s"
                )

                # Callback
                if on_retry:
                    on_retry(attempt, e, delay)

                # Aguardar antes do retry
                time.sleep(delay)

        # Nao deveria chegar aqui, mas por seguranca
        if last_exception:
            raise last_exception
        raise RuntimeError("Erro inesperado no retry handler")

    def retry(self, func: Callable[..., T] = None, **kwargs) -> Callable[..., T]:
        """
        Decorador para adicionar retry a uma funcao.

        Pode ser usado com ou sem argumentos:
            @handler.retry
            def func(): ...

            @handler.retry(on_retry=callback)
            def func(): ...

        Args:
            func: Funcao a ser decorada
            **kwargs: Argumentos passados para execute()

        Returns:
            Funcao decorada
        """
        def decorator(f: Callable[..., T]) -> Callable[..., T]:
            @wraps(f)
            def wrapper(*args, **kw) -> T:
                return self.execute(lambda: f(*args, **kw), **kwargs)
            return wrapper

        if func is not None:
            # Usado como @handler.retry
            return decorator(func)

        # Usado como @handler.retry(...)
        return decorator

    @property
    def current_attempt(self) -> int:
        """Retorna a tentativa atual (0-based)."""
        return self._attempt


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: List[Type[Exception]] = None,
    on_retry: Callable[[int, Exception, float], None] = None
):
    """
    Decorador standalone para retry com backoff exponencial.

    Exemplo:
        @with_retry(max_retries=5)
        def fazer_requisicao():
            return requests.get(url)

    Args:
        max_retries: Numero maximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay maximo em segundos
        backoff_factor: Fator de multiplicacao
        jitter: Adicionar variacao aleatoria
        retryable_exceptions: Excecoes para retry
        on_retry: Callback antes de cada retry

    Returns:
        Decorador
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    handler = RetryHandler(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return handler.execute(lambda: func(*args, **kwargs), on_retry=on_retry)
        return wrapper

    return decorator
