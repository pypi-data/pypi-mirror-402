"""
오류 처리 및 복구 메커니즘
시스템 안정성을 위한 포괄적인 오류 처리
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, Type, Union, List, Dict
import logging


logger = logging.getLogger(__name__)


class LSMRError(Exception):
    """LSMR 시스템 기본 예외"""
    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.context = context or {}


class APIError(LSMRError):
    """API 관련 오류"""
    pass


class KISAPIError(APIError):
    """KIS API 관련 오류"""
    pass


class AuthenticationError(APIError):
    """인증 오류"""
    pass


class RateLimitError(APIError):
    """속도 제한 오류"""
    pass


class NetworkError(APIError):
    """네트워크 오류"""
    pass


class DataProcessingError(LSMRError):
    """데이터 처리 오류"""
    pass


class DatabaseError(LSMRError):
    """데이터베이스 관련 오류"""
    pass


class DatabaseConnectionError(DatabaseError):
    """데이터베이스 연결 오류"""
    pass


class DatabaseQueryError(DatabaseError):
    """데이터베이스 쿼리 오류"""
    pass


class DatabaseTransactionError(DatabaseError):
    """데이터베이스 트랜잭션 오류"""
    pass


class AnalysisError(LSMRError):
    """분석 관련 오류"""
    pass


class InsufficientDataError(AnalysisError):
    """분석에 필요한 데이터 부족"""
    pass


class CalculationError(AnalysisError):
    """계산 오류"""
    pass


class TradingError(LSMRError):
    """거래 관련 오류"""
    pass


class InsufficientCashError(TradingError):
    """매수 자금 부족"""
    pass


class PositionLimitError(TradingError):
    """포지션 한도 초과"""
    pass


class OrderRejectedError(TradingError):
    """주문 거부"""
    pass


class SystemError(LSMRError):
    """시스템 관련 오류"""
    pass


class MemoryLimitError(SystemError):
    """메모리 한도 초과"""
    pass


class ConfigurationError(SystemError):
    """구성 오류"""
    pass


class WebSocketConnectionError(SystemError):
    """WebSocket 연결 오류"""
    pass


class ErrorCategory:
    """오류 카테고리 상수"""
    API = "API"
    DATABASE = "DATABASE"
    ANALYSIS = "ANALYSIS"
    TRADING = "TRADING"
    SYSTEM = "SYSTEM"


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """지수 백오프를 사용한 재시도 데코레이터"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"최대 재시도 횟수 초과: {func.__name__} - "
                            f"시도 {attempt + 1}회, 오류: {str(e)}"
                        )
                        raise
                    
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"재시도 {attempt + 1}/{max_retries}: {func.__name__} - "
                        f"{str(e)} (다음 시도까지 {delay:.1f}초 대기)"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"최대 재시도 횟수 초과: {func.__name__} - "
                            f"시도 {attempt + 1}회, 오류: {str(e)}"
                        )
                        raise
                    
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"재시도 {attempt + 1}/{max_retries}: {func.__name__} - "
                        f"{str(e)} (다음 시도까지 {delay:.1f}초 대기)"
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def handle_api_errors(func: Callable) -> Callable:
    """API 오류 처리 데코레이터"""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_code = 'API_NETWORK_ERROR'
            
            # 오류 유형별 분류
            if 'auth' in str(e).lower() or 'unauthorized' in str(e).lower():
                error_code = 'API_AUTH_ERROR'
                raise AuthenticationError(str(e), error_code, {'function': func.__name__})
            elif 'rate limit' in str(e).lower() or '429' in str(e):
                error_code = 'API_RATE_LIMIT'
                raise RateLimitError(str(e), error_code, {'function': func.__name__})
            elif 'network' in str(e).lower() or 'connection' in str(e).lower():
                error_code = 'API_NETWORK_ERROR'
                raise NetworkError(str(e), error_code, {'function': func.__name__})
            
            logger.error(
                f"[{error_code}] API 호출 실패: {func.__name__} - {str(e)}"
            )
            
            raise APIError(str(e), error_code, {'function': func.__name__})
    
    return wrapper


def handle_error_with_retry(
    error_category: str,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """오류 처리 및 재시도 데코레이터"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"[{error_category}] 최대 재시도 횟수 초과: {func.__name__} - "
                            f"시도 {attempt + 1}회, 오류: {str(e)}"
                        )
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"[{error_category}] 재시도 {attempt + 1}/{max_retries}: {func.__name__} - "
                        f"{str(e)} (다음 시도까지 {delay:.1f}초 대기)"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    
    return decorator


def handle_trading_errors(func: Callable) -> Callable:
    """거래 오류 처리 데코레이터"""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_code = 'ORDER_REJECTED'
            
            # 거래 오류 유형별 분류
            if 'insufficient' in str(e).lower() or 'cash' in str(e).lower():
                error_code = 'INSUFFICIENT_CASH'
                raise InsufficientCashError(str(e), error_code, {'function': func.__name__})
            elif 'limit' in str(e).lower() or 'exceed' in str(e).lower():
                error_code = 'POSITION_LIMIT_EXCEEDED'
                raise PositionLimitError(str(e), error_code, {'function': func.__name__})
            elif 'reject' in str(e).lower():
                error_code = 'ORDER_REJECTED'
                raise OrderRejectedError(str(e), error_code, {'function': func.__name__})
            
            logger.error(
                f"[{error_code}] 거래 실행 실패: {func.__name__} - {str(e)}"
            )
            
            raise TradingError(str(e), error_code, {'function': func.__name__})
    
    return wrapper


def handle_database_errors(func: Callable) -> Callable:
    """데이터베이스 오류 처리 데코레이터"""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_code = 'DB_QUERY_ERROR'
            
            # 데이터베이스 오류 유형별 분류
            if 'connection' in str(e).lower() or 'connect' in str(e).lower():
                error_code = 'DB_CONNECTION_ERROR'
                raise DatabaseConnectionError(str(e), error_code, {'function': func.__name__})
            elif 'transaction' in str(e).lower() or 'rollback' in str(e).lower():
                error_code = 'DB_TRANSACTION_ERROR'
                raise DatabaseTransactionError(str(e), error_code, {'function': func.__name__})
            elif 'query' in str(e).lower() or 'syntax' in str(e).lower():
                error_code = 'DB_QUERY_ERROR'
                raise DatabaseQueryError(str(e), error_code, {'function': func.__name__})
            
            logger.error(
                f"[{error_code}] 데이터베이스 작업 실패: {func.__name__} - {str(e)}"
            )
            
            raise DatabaseError(str(e), error_code, {'function': func.__name__})
    
    return wrapper


class CircuitBreaker:
    """회로 차단기 패턴 구현"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise SystemError(
                        "회로 차단기 열림 상태",
                        'CIRCUIT_BREAKER_OPEN',
                        {'function': func.__name__}
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """재시도 가능 여부 확인"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """성공 시 상태 리셋"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """실패 시 상태 업데이트"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f"회로 차단기 열림: 실패 횟수 {self.failure_count}회 "
                f"(임계값: {self.failure_threshold}회)"
            )


class GracefulDegradation:
    """우아한 성능 저하 관리"""
    
    def __init__(self):
        self.degraded_services = set()
        self.fallback_data = {}
    
    def mark_service_degraded(self, service_name: str, fallback_data: Any = None):
        """서비스를 성능 저하 상태로 표시"""
        self.degraded_services.add(service_name)
        if fallback_data is not None:
            self.fallback_data[service_name] = fallback_data
        
        logger.warning(f"서비스 성능 저하 모드 진입: {service_name}")
    
    def restore_service(self, service_name: str):
        """서비스 정상 상태로 복구"""
        self.degraded_services.discard(service_name)
        self.fallback_data.pop(service_name, None)
        
        logger.info(f"서비스 정상 상태 복구: {service_name}")
    
    def is_service_degraded(self, service_name: str) -> bool:
        """서비스 성능 저하 상태 확인"""
        return service_name in self.degraded_services
    
    def get_fallback_data(self, service_name: str) -> Any:
        """대체 데이터 조회"""
        return self.fallback_data.get(service_name)


# 전역 성능 저하 관리자
graceful_degradation = GracefulDegradation()


def monitor_performance(operation_name: str = None, threshold: float = None):
    """성능 모니터링 데코레이터"""
    
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if threshold and duration > threshold:
                    logger.warning(
                        f"성능 임계값 초과: {op_name} - {duration:.3f}초 (임계값: {threshold:.3f}초)"
                    )
                else:
                    logger.debug(f"실행 완료: {op_name} - {duration:.3f}초")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{op_name} 실패 ({duration:.3f}초): {str(e)}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if threshold and duration > threshold:
                    logger.warning(
                        f"성능 임계값 초과: {op_name} - {duration:.3f}초 (임계값: {threshold:.3f}초)"
                    )
                else:
                    logger.debug(f"실행 완료: {op_name} - {duration:.3f}초")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{op_name} 실패 ({duration:.3f}초): {str(e)}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def with_fallback(service_name: str, fallback_value: Any = None):
    """대체 값을 사용한 우아한 성능 저하 데코레이터"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # 성공 시 서비스 복구
                if graceful_degradation.is_service_degraded(service_name):
                    graceful_degradation.restore_service(service_name)
                
                return result
                
            except Exception as e:
                logger.warning(f"서비스 오류, 대체 모드 사용: {service_name} - {e}")
                
                # 서비스를 성능 저하 상태로 표시
                graceful_degradation.mark_service_degraded(service_name, fallback_value)
                
                # 대체 값 반환
                fallback = graceful_degradation.get_fallback_data(service_name)
                if fallback is not None:
                    return fallback
                
                # 대체 값이 없으면 예외 재발생
                raise
        
        return wrapper
    
    return decorator


class SystemMonitor:
    """시스템 상태 모니터링"""
    
    def __init__(self):
        self.start_time = time.time()
        self.error_counts = {}
        self.performance_alerts = []
    
    def record_error(self, error_code: str):
        """오류 발생 기록"""
        if error_code not in self.error_counts:
            self.error_counts[error_code] = 0
        self.error_counts[error_code] += 1
    
    def add_performance_alert(self, operation: str, duration: float, threshold: float):
        """성능 경고 추가"""
        alert = {
            'timestamp': time.time(),
            'operation': operation,
            'duration': duration,
            'threshold': threshold
        }
        self.performance_alerts.append(alert)
        
        # 최근 100개 경고만 유지
        if len(self.performance_alerts) > 100:
            self.performance_alerts = self.performance_alerts[-100:]
    
    def get_uptime(self) -> float:
        """시스템 가동 시간 조회"""
        return time.time() - self.start_time
    
    def get_error_summary(self) -> Dict[str, int]:
        """오류 요약 정보 조회"""
        return self.error_counts.copy()
    
    def get_recent_performance_alerts(self, minutes: int = 10) -> List[Dict]:
        """최근 성능 경고 조회"""
        cutoff_time = time.time() - (minutes * 60)
        return [alert for alert in self.performance_alerts if alert['timestamp'] > cutoff_time]
    
    def is_system_healthy(self) -> bool:
        """시스템 건강 상태 확인"""
        # 최근 5분간 성능 경고가 10개 이상이면 비정상
        recent_alerts = self.get_recent_performance_alerts(5)
        if len(recent_alerts) >= 10:
            return False
        
        # 치명적 오류가 있으면 비정상
        critical_errors = ['MEMORY_LIMIT_EXCEEDED', 'WEBSOCKET_CONNECTION_LOST']
        for error_code in critical_errors:
            if self.error_counts.get(error_code, 0) > 0:
                return False
        
        return True


# 전역 시스템 모니터
system_monitor = SystemMonitor()
