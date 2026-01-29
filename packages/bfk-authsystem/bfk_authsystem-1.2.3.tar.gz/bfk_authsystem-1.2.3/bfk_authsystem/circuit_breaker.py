"""
BFK AuthSystem - Circuit Breaker

Implementa o padrao Circuit Breaker para proteger contra falhas em cascata.
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps
from dataclasses import dataclass, field

from .exceptions import CircuitBreakerOpenError, NetworkError, ServerError


logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Estados do circuit breaker."""
    CLOSED = "closed"      # Normal, permitindo requisicoes
    OPEN = "open"          # Bloqueando requisicoes
    HALF_OPEN = "half_open"  # Testando se o servico voltou


@dataclass
class CircuitBreakerConfig:
    """
    Configuracao do circuit breaker.

    Attributes:
        failure_threshold: Numero de falhas para abrir o circuito (padrao: 5)
        success_threshold: Numero de sucessos em half-open para fechar (padrao: 2)
        recovery_timeout: Segundos para tentar novamente apos abrir (padrao: 60)
        half_open_max_calls: Max requisicoes em half-open (padrao: 3)
        monitored_exceptions: Excecoes que contam como falha
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    monitored_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        NetworkError,
        ServerError,
        ConnectionError,
        TimeoutError,
    ])


class CircuitBreaker:
    """
    Implementacao do padrao Circuit Breaker.

    O circuit breaker protege o sistema contra falhas em cascata,
    bloqueando requisicoes quando o servico esta indisponivel.

    Estados:
    - CLOSED: Normal, todas as requisicoes sao permitidas
    - OPEN: Circuito aberto, requisicoes sao bloqueadas
    - HALF_OPEN: Testando, algumas requisicoes sao permitidas

    Exemplo:
        cb = CircuitBreaker()

        @cb.protect
        def fazer_requisicao():
            return requests.get(url)

        # Ou diretamente:
        result = cb.call(fazer_requisicao)
    """

    def __init__(self, name: str = "default", config: CircuitBreakerConfig = None):
        """
        Inicializa o circuit breaker.

        Args:
            name: Nome identificador do circuit breaker
            config: Configuracao (usa padrao se nao fornecido)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """Retorna o estado atual do circuit breaker."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def is_closed(self) -> bool:
        """Verifica se o circuito esta fechado (operacao normal)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Verifica se o circuito esta aberto (bloqueando)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Verifica se o circuito esta semi-aberto (testando)."""
        return self.state == CircuitState.HALF_OPEN

    @property
    def failure_count(self) -> int:
        """Retorna o contador de falhas."""
        return self._failure_count

    @property
    def time_until_retry(self) -> float:
        """
        Retorna segundos ate a proxima tentativa.

        Returns:
            Segundos restantes, ou 0 se pode tentar agora
        """
        with self._lock:
            if self._state != CircuitState.OPEN:
                return 0

            if self._last_failure_time is None:
                return 0

            elapsed = time.time() - self._last_failure_time
            remaining = self.config.recovery_timeout - elapsed
            return max(0, remaining)

    def _check_state_transition(self):
        """Verifica e realiza transicoes de estado automaticas."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    logger.info(
                        f"[{self.name}] Circuit breaker: OPEN -> HALF_OPEN "
                        f"(recovery timeout de {self.config.recovery_timeout}s atingido)"
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0

    def _record_success(self):
        """Registra uma operacao bem-sucedida."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"[{self.name}] Sucesso em HALF_OPEN: "
                    f"{self._success_count}/{self.config.success_threshold}"
                )
                if self._success_count >= self.config.success_threshold:
                    logger.info(
                        f"[{self.name}] Circuit breaker: HALF_OPEN -> CLOSED "
                        f"({self._success_count} sucessos consecutivos)"
                    )
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                # Resetar contador de falhas em caso de sucesso
                if self._failure_count > 0:
                    logger.debug(f"[{self.name}] Sucesso, resetando contador de falhas")
                    self._failure_count = 0

    def _record_failure(self, exception: Exception):
        """Registra uma falha."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            logger.debug(
                f"[{self.name}] Falha #{self._failure_count}: {type(exception).__name__}"
            )

            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    f"[{self.name}] Circuit breaker: HALF_OPEN -> OPEN "
                    f"(falha durante teste)"
                )
                self._state = CircuitState.OPEN
                self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    logger.warning(
                        f"[{self.name}] Circuit breaker: CLOSED -> OPEN "
                        f"({self._failure_count} falhas atingido threshold)"
                    )
                    self._state = CircuitState.OPEN

    def _should_monitor_exception(self, exception: Exception) -> bool:
        """Verifica se a excecao deve ser monitorada."""
        for exc_type in self.config.monitored_exceptions:
            if isinstance(exception, exc_type):
                return True
        return False

    def _can_execute(self) -> bool:
        """
        Verifica se uma requisicao pode ser executada.

        Returns:
            True se pode executar

        Raises:
            CircuitBreakerOpenError: Se o circuito esta aberto
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                retry_after = int(self.time_until_retry)
                raise CircuitBreakerOpenError(
                    message=f"Servico temporariamente indisponivel. Tente novamente em {retry_after}s",
                    retry_after=retry_after
                )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        message="Limite de requisicoes em teste atingido",
                        retry_after=1
                    )
                self._half_open_calls += 1
                return True

            return False

    def call(self, func: Callable[[], T]) -> T:
        """
        Executa uma funcao protegida pelo circuit breaker.

        Args:
            func: Funcao a ser executada

        Returns:
            Resultado da funcao

        Raises:
            CircuitBreakerOpenError: Se o circuito esta aberto
            Exception: Qualquer excecao da funcao
        """
        self._can_execute()

        try:
            result = func()
            self._record_success()
            return result

        except Exception as e:
            if self._should_monitor_exception(e):
                self._record_failure(e)
            raise

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorador para proteger uma funcao com circuit breaker.

        Exemplo:
            @cb.protect
            def fazer_requisicao():
                return requests.get(url)

        Args:
            func: Funcao a ser protegida

        Returns:
            Funcao decorada
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self.call(lambda: func(*args, **kwargs))
        return wrapper

    def reset(self):
        """Reseta o circuit breaker para o estado inicial (CLOSED)."""
        with self._lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = None
            logger.info(f"[{self.name}] Circuit breaker resetado: {old_state.value} -> CLOSED")

    def force_open(self):
        """Forca o circuit breaker para o estado OPEN."""
        with self._lock:
            old_state = self._state
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()
            logger.info(f"[{self.name}] Circuit breaker forcado: {old_state.value} -> OPEN")

    def get_stats(self) -> dict:
        """
        Retorna estatisticas do circuit breaker.

        Returns:
            Dict com estado, contadores e tempos
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "half_open_calls": self._half_open_calls,
                "time_until_retry": self.time_until_retry,
                "last_failure_time": self._last_failure_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                }
            }


# Circuit breaker global para a API
_default_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker(name: str = "api") -> CircuitBreaker:
    """
    Obtem ou cria um circuit breaker.

    Args:
        name: Nome do circuit breaker

    Returns:
        Instancia do circuit breaker
    """
    global _default_circuit_breaker

    if _default_circuit_breaker is None or _default_circuit_breaker.name != name:
        _default_circuit_breaker = CircuitBreaker(name=name)

    return _default_circuit_breaker


def circuit_protected(name: str = "api"):
    """
    Decorador para proteger uma funcao com o circuit breaker global.

    Exemplo:
        @circuit_protected("api")
        def fazer_requisicao():
            return requests.get(url)

    Args:
        name: Nome do circuit breaker

    Returns:
        Decorador
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cb = get_circuit_breaker(name)
            return cb.call(lambda: func(*args, **kwargs))
        return wrapper
    return decorator
