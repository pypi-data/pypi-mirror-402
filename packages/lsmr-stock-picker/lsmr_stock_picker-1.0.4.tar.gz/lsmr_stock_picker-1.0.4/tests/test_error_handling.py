"""
오류 처리 시스템 테스트
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from utils.error_handling import (
    LSMRError,
    APIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    AnalysisError,
    InsufficientDataError,
    CalculationError,
    TradingError,
    InsufficientCashError,
    PositionLimitError,
    OrderRejectedError,
    SystemError,
    MemoryLimitError,
    ConfigurationError,
    WebSocketConnectionError,
    retry_with_backoff,
    handle_api_errors,
    handle_database_errors,
    handle_trading_errors,
    CircuitBreaker,
    GracefulDegradation,
    monitor_performance,
    with_fallback,
    SystemMonitor,
    graceful_degradation,
    system_monitor
)


class TestErrorClasses:
    """오류 클래스 테스트"""
    
    def test_lsmr_error_basic(self):
        """기본 LSMR 오류 생성"""
        error = LSMRError("테스트 오류", "TEST_ERROR", {"key": "value"})
        assert str(error) == "테스트 오류"
        assert error.error_code == "TEST_ERROR"
        assert error.context == {"key": "value"}
    
    def test_api_error_hierarchy(self):
        """API 오류 계층 구조"""
        auth_error = AuthenticationError("인증 실패", "API_AUTH_ERROR")
        assert isinstance(auth_error, APIError)
        assert isinstance(auth_error, LSMRError)
        assert auth_error.error_code == "API_AUTH_ERROR"
        
        rate_error = RateLimitError("속도 제한", "API_RATE_LIMIT")
        assert isinstance(rate_error, APIError)
        
        network_error = NetworkError("네트워크 오류", "API_NETWORK_ERROR")
        assert isinstance(network_error, APIError)
    
    def test_database_error_hierarchy(self):
        """데이터베이스 오류 계층 구조"""
        conn_error = DatabaseConnectionError("연결 실패", "DB_CONNECTION_ERROR")
        assert isinstance(conn_error, DatabaseError)
        assert isinstance(conn_error, LSMRError)
        
        query_error = DatabaseQueryError("쿼리 실패", "DB_QUERY_ERROR")
        assert isinstance(query_error, DatabaseError)
        
        trans_error = DatabaseTransactionError("트랜잭션 실패", "DB_TRANSACTION_ERROR")
        assert isinstance(trans_error, DatabaseError)
    
    def test_trading_error_hierarchy(self):
        """거래 오류 계층 구조"""
        cash_error = InsufficientCashError("자금 부족", "INSUFFICIENT_CASH")
        assert isinstance(cash_error, TradingError)
        
        limit_error = PositionLimitError("한도 초과", "POSITION_LIMIT_EXCEEDED")
        assert isinstance(limit_error, TradingError)
        
        reject_error = OrderRejectedError("주문 거부", "ORDER_REJECTED")
        assert isinstance(reject_error, TradingError)
    
    def test_analysis_error_hierarchy(self):
        """분석 오류 계층 구조"""
        data_error = InsufficientDataError("데이터 부족", "INSUFFICIENT_DATA")
        assert isinstance(data_error, AnalysisError)
        
        calc_error = CalculationError("계산 오류", "CALCULATION_ERROR")
        assert isinstance(calc_error, AnalysisError)
    
    def test_system_error_hierarchy(self):
        """시스템 오류 계층 구조"""
        mem_error = MemoryLimitError("메모리 초과", "MEMORY_LIMIT_EXCEEDED")
        assert isinstance(mem_error, SystemError)
        
        config_error = ConfigurationError("구성 오류", "CONFIG_ERROR")
        assert isinstance(config_error, SystemError)
        
        ws_error = WebSocketConnectionError("WebSocket 오류", "WEBSOCKET_CONNECTION_LOST")
        assert isinstance(ws_error, SystemError)


class TestRetryWithBackoff:
    """재시도 메커니즘 테스트"""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """첫 시도에서 성공"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """실패 후 재시도하여 성공"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def eventually_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("일시적 오류")
            return "success"
        
        result = await eventually_successful_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """최대 재시도 횟수 초과"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("지속적 오류")
        
        with pytest.raises(Exception, match="지속적 오류"):
            await always_failing_func()
        
        assert call_count == 3  # 초기 시도 + 2번 재시도
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """지수 백오프 타이밍 검증"""
        call_times = []
        
        @retry_with_backoff(max_retries=3, base_delay=0.1, exponential_base=2.0)
        async def timing_test_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("재시도 필요")
            return "success"
        
        await timing_test_func()
        
        # 첫 번째와 두 번째 호출 사이 간격 확인 (약 0.1초)
        assert call_times[1] - call_times[0] >= 0.1
        
        # 두 번째와 세 번째 호출 사이 간격 확인 (약 0.2초)
        assert call_times[2] - call_times[1] >= 0.2


class TestAPIErrorHandling:
    """API 오류 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_handle_authentication_error(self):
        """인증 오류 처리"""
        @handle_api_errors
        async def api_call_with_auth_error():
            raise Exception("unauthorized access")
        
        with pytest.raises(AuthenticationError) as exc_info:
            await api_call_with_auth_error()
        
        assert exc_info.value.error_code == "API_AUTH_ERROR"
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(self):
        """속도 제한 오류 처리"""
        @handle_api_errors
        async def api_call_with_rate_limit():
            raise Exception("rate limit exceeded")
        
        with pytest.raises(RateLimitError) as exc_info:
            await api_call_with_rate_limit()
        
        assert exc_info.value.error_code == "API_RATE_LIMIT"
    
    @pytest.mark.asyncio
    async def test_handle_network_error(self):
        """네트워크 오류 처리"""
        @handle_api_errors
        async def api_call_with_network_error():
            raise Exception("network connection failed")
        
        with pytest.raises(NetworkError) as exc_info:
            await api_call_with_network_error()
        
        assert exc_info.value.error_code == "API_NETWORK_ERROR"


class TestDatabaseErrorHandling:
    """데이터베이스 오류 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_handle_connection_error(self):
        """연결 오류 처리"""
        @handle_database_errors
        async def db_operation_with_connection_error():
            raise Exception("connection refused")
        
        with pytest.raises(DatabaseConnectionError) as exc_info:
            await db_operation_with_connection_error()
        
        assert exc_info.value.error_code == "DB_CONNECTION_ERROR"
    
    @pytest.mark.asyncio
    async def test_handle_query_error(self):
        """쿼리 오류 처리"""
        @handle_database_errors
        async def db_operation_with_query_error():
            raise Exception("syntax error in query")
        
        with pytest.raises(DatabaseQueryError) as exc_info:
            await db_operation_with_query_error()
        
        assert exc_info.value.error_code == "DB_QUERY_ERROR"
    
    @pytest.mark.asyncio
    async def test_handle_transaction_error(self):
        """트랜잭션 오류 처리"""
        @handle_database_errors
        async def db_operation_with_transaction_error():
            raise Exception("transaction rollback")
        
        with pytest.raises(DatabaseTransactionError) as exc_info:
            await db_operation_with_transaction_error()
        
        assert exc_info.value.error_code == "DB_TRANSACTION_ERROR"


class TestTradingErrorHandling:
    """거래 오류 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_handle_insufficient_cash_error(self):
        """자금 부족 오류 처리"""
        @handle_trading_errors
        async def trade_with_insufficient_cash():
            raise Exception("insufficient cash")
        
        with pytest.raises(InsufficientCashError) as exc_info:
            await trade_with_insufficient_cash()
        
        assert exc_info.value.error_code == "INSUFFICIENT_CASH"
    
    @pytest.mark.asyncio
    async def test_handle_position_limit_error(self):
        """포지션 한도 오류 처리"""
        @handle_trading_errors
        async def trade_with_limit_exceeded():
            raise Exception("position limit exceeded")
        
        with pytest.raises(PositionLimitError) as exc_info:
            await trade_with_limit_exceeded()
        
        assert exc_info.value.error_code == "POSITION_LIMIT_EXCEEDED"
    
    @pytest.mark.asyncio
    async def test_handle_order_rejected_error(self):
        """주문 거부 오류 처리"""
        @handle_trading_errors
        async def trade_with_rejected_order():
            raise Exception("order rejected")
        
        with pytest.raises(OrderRejectedError) as exc_info:
            await trade_with_rejected_order()
        
        assert exc_info.value.error_code == "ORDER_REJECTED"


class TestCircuitBreaker:
    """회로 차단기 테스트"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """회로 차단기 닫힘 상태"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        @breaker
        async def successful_operation():
            return "success"
        
        result = await successful_operation()
        assert result == "success"
        assert breaker.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """임계값 초과 후 회로 차단기 열림"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        @breaker
        async def failing_operation():
            raise Exception("오류 발생")
        
        # 3번 실패하여 회로 차단기 열림
        for _ in range(3):
            with pytest.raises(Exception):
                await failing_operation()
        
        assert breaker.state == "OPEN"
        
        # 회로 차단기가 열린 상태에서 호출 시 즉시 실패
        with pytest.raises(SystemError, match="회로 차단기 열림"):
            await failing_operation()


class TestGracefulDegradation:
    """우아한 성능 저하 테스트"""
    
    def test_mark_service_degraded(self):
        """서비스 성능 저하 표시"""
        degradation = GracefulDegradation()
        
        degradation.mark_service_degraded("test_service", {"fallback": "data"})
        
        assert degradation.is_service_degraded("test_service")
        assert degradation.get_fallback_data("test_service") == {"fallback": "data"}
    
    def test_restore_service(self):
        """서비스 복구"""
        degradation = GracefulDegradation()
        
        degradation.mark_service_degraded("test_service")
        assert degradation.is_service_degraded("test_service")
        
        degradation.restore_service("test_service")
        assert not degradation.is_service_degraded("test_service")
    
    @pytest.mark.asyncio
    async def test_with_fallback_decorator(self):
        """대체 값 데코레이터"""
        @with_fallback("test_service", fallback_value="fallback_result")
        async def operation_with_fallback():
            raise Exception("서비스 오류")
        
        result = await operation_with_fallback()
        assert result == "fallback_result"
        assert graceful_degradation.is_service_degraded("test_service")


class TestPerformanceMonitoring:
    """성능 모니터링 테스트"""
    
    @pytest.mark.asyncio
    async def test_monitor_performance_decorator(self):
        """성능 모니터링 데코레이터"""
        @monitor_performance(operation_name="test_operation", threshold=0.1)
        async def monitored_operation():
            await asyncio.sleep(0.05)
            return "result"
        
        result = await monitored_operation()
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_performance_threshold_warning(self):
        """성능 임계값 초과 경고"""
        with patch('utils.error_handling.logger') as mock_logger:
            @monitor_performance(operation_name="slow_operation", threshold=0.01)
            async def slow_operation():
                await asyncio.sleep(0.02)
                return "result"
            
            await slow_operation()
            
            # 경고 로그 호출 확인
            assert any('성능 임계값 초과' in str(call) for call in mock_logger.warning.call_args_list)


class TestSystemMonitor:
    """시스템 모니터 테스트"""
    
    def test_record_error(self):
        """오류 기록"""
        monitor = SystemMonitor()
        
        monitor.record_error("API_AUTH_ERROR")
        monitor.record_error("API_AUTH_ERROR")
        monitor.record_error("DB_CONNECTION_ERROR")
        
        summary = monitor.get_error_summary()
        assert summary["API_AUTH_ERROR"] == 2
        assert summary["DB_CONNECTION_ERROR"] == 1
    
    def test_add_performance_alert(self):
        """성능 경고 추가"""
        monitor = SystemMonitor()
        
        monitor.add_performance_alert("operation1", 0.5, 0.1)
        monitor.add_performance_alert("operation2", 1.0, 0.5)
        
        alerts = monitor.get_recent_performance_alerts(10)
        assert len(alerts) == 2
        assert alerts[0]['operation'] == "operation1"
        assert alerts[0]['duration'] == 0.5
    
    def test_system_health_check(self):
        """시스템 건강 상태 확인"""
        monitor = SystemMonitor()
        
        # 정상 상태
        assert monitor.is_system_healthy()
        
        # 치명적 오류 발생
        monitor.record_error("MEMORY_LIMIT_EXCEEDED")
        assert not monitor.is_system_healthy()
    
    def test_get_uptime(self):
        """가동 시간 조회"""
        monitor = SystemMonitor()
        time.sleep(0.1)
        
        uptime = monitor.get_uptime()
        assert uptime >= 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
