"""
로깅 시스템 테스트
"""

import pytest
import logging
import os
import tempfile
import time
from unittest.mock import Mock, patch
from utils.logging import (
    SecureFormatter,
    setup_logging,
    get_logger,
    PerformanceLogger,
    ErrorLogger
)


class TestSecureFormatter:
    """보안 로그 포매터 테스트"""
    
    def test_mask_app_key(self):
        """앱 키 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='app_key: "my_secret_key_12345"',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "my_secret_key_12345" not in formatted
        assert "***" in formatted
    
    def test_mask_app_secret(self):
        """앱 시크릿 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='app_secret: "super_secret_value"',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "super_secret_value" not in formatted
        assert "***" in formatted
    
    def test_mask_access_token(self):
        """액세스 토큰 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in formatted
        assert "***" in formatted
    
    def test_mask_authorization_bearer(self):
        """Authorization Bearer 토큰 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Authorization: Bearer abc123def456',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "abc123def456" not in formatted
        assert "***" in formatted
    
    def test_mask_password(self):
        """비밀번호 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='password: "my_password_123"',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "my_password_123" not in formatted
        assert "***" in formatted
    
    def test_mask_credit_card(self):
        """신용카드 번호 마스킹"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='card: 1234-5678-9012-3456',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "1234-5678-9012-3456" not in formatted
        assert "****-****-****-****" in formatted
    
    def test_preserve_non_sensitive_data(self):
        """민감하지 않은 데이터 보존"""
        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='user_id: 12345, status: active',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "user_id: 12345" in formatted
        assert "status: active" in formatted


class TestLoggingSetup:
    """로깅 설정 테스트"""
    
    def test_setup_logging_creates_log_directory(self):
        """로그 디렉토리 생성"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            
            # 임시 디렉토리로 변경
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                logger = setup_logging(log_file="test.log")
                
                # logs 디렉토리가 생성되었는지 확인
                assert os.path.exists("logs")
                assert os.path.isdir("logs")
            finally:
                os.chdir(original_cwd)
    
    def test_setup_logging_creates_handlers(self):
        """핸들러 생성 확인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                logger = setup_logging(log_file="test.log")
                
                # 파일 핸들러와 콘솔 핸들러가 있는지 확인
                handlers = logger.handlers
                assert len(handlers) >= 2
                
                handler_types = [type(h).__name__ for h in handlers]
                assert 'RotatingFileHandler' in handler_types
                assert 'StreamHandler' in handler_types
            finally:
                os.chdir(original_cwd)
    
    def test_get_logger(self):
        """모듈별 로거 생성"""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert isinstance(logger, logging.Logger)


class TestPerformanceLogger:
    """성능 로거 테스트"""
    
    def test_log_execution_time(self):
        """실행 시간 로깅"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_execution_time("test_operation", 0.05, threshold=0.1)
        
        # 임계값 이하이므로 debug 로그 호출
        assert logger.debug.called
    
    def test_log_execution_time_exceeds_threshold(self):
        """임계값 초과 시 경고"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_execution_time("slow_operation", 0.5, threshold=0.1)
        
        # 임계값 초과이므로 warning 로그 호출
        assert logger.warning.called
        warning_msg = str(logger.warning.call_args)
        assert "성능 임계값 초과" in warning_msg
    
    def test_log_api_response_time(self):
        """API 응답 시간 로깅"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_api_response_time("/api/test", 0.5)
        
        # 응답 시간이 기록되었는지 확인
        assert "/api/test" in perf_logger.response_times
        assert len(perf_logger.response_times["/api/test"]) == 1
        assert perf_logger.response_times["/api/test"][0]['duration'] == 0.5
    
    def test_log_signal_generation_time(self):
        """신호 생성 시간 로깅 (요구사항 8.1: 100ms 미만)"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        # 정상 범위 (50ms)
        perf_logger.log_signal_generation_time(0.05)
        assert logger.debug.called
        
        # 임계값 초과 (150ms)
        logger.reset_mock()
        perf_logger.log_signal_generation_time(0.15)
        assert logger.warning.called
    
    def test_log_data_processing_time(self):
        """데이터 처리 시간 로깅 (요구사항 8.2: 50ms 미만)"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        # 정상 범위 (30ms)
        perf_logger.log_data_processing_time(0.03)
        assert logger.debug.called
        
        # 임계값 초과 (80ms)
        logger.reset_mock()
        perf_logger.log_data_processing_time(0.08)
        assert logger.warning.called
    
    def test_get_average_time(self):
        """평균 실행 시간 조회"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_execution_time("test_op", 0.1)
        perf_logger.log_execution_time("test_op", 0.2)
        perf_logger.log_execution_time("test_op", 0.3)
        
        avg_time = perf_logger.get_average_time("test_op")
        assert avg_time == pytest.approx(0.2, rel=0.01)
    
    def test_get_average_response_time(self):
        """평균 API 응답 시간 조회"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_api_response_time("/api/test", 0.5)
        perf_logger.log_api_response_time("/api/test", 0.7)
        perf_logger.log_api_response_time("/api/test", 0.6)
        
        avg_time = perf_logger.get_average_response_time("/api/test")
        assert avg_time == pytest.approx(0.6, rel=0.01)
    
    def test_get_performance_summary(self):
        """성능 요약 정보 조회"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_execution_time("op1", 0.1)
        perf_logger.log_execution_time("op1", 0.2)
        perf_logger.log_execution_time("op2", 0.5)
        
        summary = perf_logger.get_performance_summary()
        
        assert "op1" in summary
        assert summary["op1"]["count"] == 2
        assert summary["op1"]["min"] == 0.1
        assert summary["op1"]["max"] == 0.2
        
        assert "op2" in summary
        assert summary["op2"]["count"] == 1
    
    def test_get_response_time_summary(self):
        """API 응답 시간 요약 정보 조회"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        perf_logger.log_api_response_time("/api/test1", 0.5)
        perf_logger.log_api_response_time("/api/test1", 0.7)
        perf_logger.log_api_response_time("/api/test2", 1.0)
        
        summary = perf_logger.get_response_time_summary()
        
        assert "/api/test1" in summary
        assert summary["/api/test1"]["count"] == 2
        assert summary["/api/test1"]["min"] == 0.5
        assert summary["/api/test1"]["max"] == 0.7
        assert "last_call" in summary["/api/test1"]
        
        assert "/api/test2" in summary
        assert summary["/api/test2"]["count"] == 1
    
    def test_performance_metrics_limit(self):
        """성능 메트릭 최대 개수 제한 (100개)"""
        logger = Mock()
        perf_logger = PerformanceLogger(logger)
        
        # 150개 기록 추가
        for i in range(150):
            perf_logger.log_execution_time("test_op", 0.1)
        
        # 최근 100개만 유지되는지 확인
        assert len(perf_logger.performance_metrics["test_op"]) == 100


class TestErrorLogger:
    """오류 로거 테스트"""
    
    def test_log_error_with_code(self):
        """오류 코드와 함께 로깅"""
        logger = Mock()
        error_logger = ErrorLogger(logger)
        
        error_logger.log_error("API_AUTH_ERROR", "인증 실패")
        
        assert logger.error.called
        error_msg = str(logger.error.call_args)
        assert "API_AUTH_ERROR" in error_msg
        assert "인증 오류" in error_msg
    
    def test_log_error_with_context(self):
        """컨텍스트와 함께 오류 로깅"""
        logger = Mock()
        error_logger = ErrorLogger(logger)
        
        context = {
            "endpoint": "/api/test",
            "status_code": 401
        }
        
        error_logger.log_error("API_AUTH_ERROR", "인증 실패", context)
        
        assert logger.error.called
        error_msg = str(logger.error.call_args)
        assert "컨텍스트" in error_msg
    
    def test_sanitize_sensitive_context(self):
        """민감한 컨텍스트 정보 제거"""
        logger = Mock()
        error_logger = ErrorLogger(logger)
        
        context = {
            "app_key": "secret_key_123",
            "app_secret": "secret_value_456",
            "user_id": "12345"
        }
        
        error_logger.log_error("API_AUTH_ERROR", "인증 실패", context)
        
        error_msg = str(logger.error.call_args)
        # 민감한 정보는 마스킹되어야 함
        assert "secret_key_123" not in error_msg
        assert "secret_value_456" not in error_msg
        # 민감하지 않은 정보는 보존되어야 함
        assert "12345" in error_msg
    
    def test_log_all_error_codes(self):
        """모든 오류 코드 로깅"""
        logger = Mock()
        error_logger = ErrorLogger(logger)
        
        error_codes = [
            "API_AUTH_ERROR",
            "API_RATE_LIMIT",
            "API_NETWORK_ERROR",
            "DB_CONNECTION_ERROR",
            "DB_QUERY_ERROR",
            "DB_TRANSACTION_ERROR",
            "INSUFFICIENT_CASH",
            "POSITION_LIMIT_EXCEEDED",
            "ORDER_REJECTED",
            "INSUFFICIENT_DATA",
            "CALCULATION_ERROR",
            "DATA_PROCESSING_ERROR",
            "MEMORY_LIMIT_EXCEEDED",
            "CONFIG_ERROR",
            "WEBSOCKET_CONNECTION_LOST",
            "CIRCUIT_BREAKER_OPEN",
            "RETRY_EXHAUSTED"
        ]
        
        for error_code in error_codes:
            logger.reset_mock()
            error_logger.log_error(error_code, f"테스트 오류: {error_code}")
            assert logger.error.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
