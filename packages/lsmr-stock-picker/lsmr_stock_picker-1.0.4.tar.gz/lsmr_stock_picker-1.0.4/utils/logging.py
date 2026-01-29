"""
로깅 설정 및 유틸리티
보안 요구사항을 준수하는 로깅 시스템
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime
from typing import Any, Dict


class SecureFormatter(logging.Formatter):
    """보안 로그 포매터 - 민감한 정보 제거"""
    
    # 민감한 정보 패턴
    SENSITIVE_PATTERNS = [
        (re.compile(r'(app_?key["\s]*[:=]["\s]*)([^"\s,}]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(app_?secret["\s]*[:=]["\s]*)([^"\s,}]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(access_?token["\s]*[:=]["\s]*)([^"\s,}]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(authorization["\s]*[:=]["\s]*bearer\s+)([^"\s,}]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(password["\s]*[:=]["\s]*)([^"\s,}]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(\d{4}-?\d{4}-?\d{4}-?\d{4})', re.IGNORECASE), r'****-****-****-****'),
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 메시지 포맷팅 및 민감한 정보 제거"""
        # 기본 포맷팅
        formatted = super().format(record)
        
        # 민감한 정보 마스킹
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "lsmr_stock_picker.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """로깅 시스템 설정"""
    
    # 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)
    
    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 포매터 설정
    formatter = SecureFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (로테이션)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 생성"""
    return logging.getLogger(name)


class PerformanceLogger:
    """성능 모니터링 로거"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.performance_metrics = {}
        self.response_times = {}  # API 응답 시간 추적
    
    def log_execution_time(self, operation: str, duration: float, threshold: float = 0.1):
        """실행 시간 로깅"""
        # 성능 메트릭 저장
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        self.performance_metrics[operation].append(duration)
        
        # 최근 100개 기록만 유지
        if len(self.performance_metrics[operation]) > 100:
            self.performance_metrics[operation] = self.performance_metrics[operation][-100:]
        
        if duration > threshold:
            self.logger.warning(
                f"성능 임계값 초과: {operation} - {duration:.3f}초 (임계값: {threshold:.3f}초)"
            )
            
            # 시스템 모니터에 성능 경고 기록 (순환 import 방지)
            try:
                from utils.error_handling import system_monitor
                system_monitor.add_performance_alert(operation, duration, threshold)
            except ImportError:
                pass  # 모듈이 아직 로드되지 않은 경우 무시
        else:
            self.logger.debug(f"실행 완료: {operation} - {duration:.3f}초")
    
    def log_api_response_time(self, endpoint: str, duration: float):
        """API 응답 시간 로깅"""
        # 응답 시간 추적
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
        
        # 최근 100개 기록만 유지
        if len(self.response_times[endpoint]) > 100:
            self.response_times[endpoint] = self.response_times[endpoint][-100:]
        
        self.log_execution_time(f"API 호출 [{endpoint}]", duration, threshold=1.0)
    
    def log_signal_generation_time(self, duration: float):
        """신호 생성 시간 로깅 (요구사항 8.1: 100ms 미만)"""
        self.log_execution_time("신호 생성", duration, threshold=0.1)
    
    def log_data_processing_time(self, duration: float):
        """데이터 처리 시간 로깅 (요구사항 8.2: 50ms 미만)"""
        self.log_execution_time("데이터 처리", duration, threshold=0.05)
    
    def get_average_time(self, operation: str) -> float:
        """특정 작업의 평균 실행 시간 조회"""
        if operation not in self.performance_metrics or not self.performance_metrics[operation]:
            return 0.0
        return sum(self.performance_metrics[operation]) / len(self.performance_metrics[operation])
    
    def get_average_response_time(self, endpoint: str) -> float:
        """특정 API 엔드포인트의 평균 응답 시간 조회"""
        if endpoint not in self.response_times or not self.response_times[endpoint]:
            return 0.0
        durations = [record['duration'] for record in self.response_times[endpoint]]
        return sum(durations) / len(durations)
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """성능 요약 정보 조회"""
        summary = {}
        for operation, times in self.performance_metrics.items():
            if times:
                summary[operation] = {
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        return summary
    
    def get_response_time_summary(self) -> Dict[str, Dict[str, float]]:
        """API 응답 시간 요약 정보 조회"""
        summary = {}
        for endpoint, records in self.response_times.items():
            if records:
                durations = [record['duration'] for record in records]
                summary[endpoint] = {
                    'average': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'count': len(durations),
                    'last_call': records[-1]['timestamp']
                }
        return summary


class ErrorLogger:
    """오류 분류 및 로깅"""
    
    ERROR_CODES = {
        # API 오류
        'API_AUTH_ERROR': '인증 오류',
        'API_RATE_LIMIT': '요청 제한 초과',
        'API_NETWORK_ERROR': '네트워크 오류',
        
        # 데이터베이스 오류
        'DB_CONNECTION_ERROR': '데이터베이스 연결 실패',
        'DB_QUERY_ERROR': '쿼리 실행 실패',
        'DB_TRANSACTION_ERROR': '트랜잭션 롤백',
        
        # 거래 오류
        'INSUFFICIENT_CASH': '매수 자금 부족',
        'POSITION_LIMIT_EXCEEDED': '포지션 한도 초과',
        'ORDER_REJECTED': '주문 거부',
        
        # 분석 오류
        'INSUFFICIENT_DATA': '분석에 필요한 데이터 부족',
        'CALCULATION_ERROR': '계산 오류',
        'DATA_PROCESSING_ERROR': '데이터 처리 오류',
        
        # 시스템 오류
        'MEMORY_LIMIT_EXCEEDED': '메모리 한도 초과',
        'CONFIG_ERROR': '구성 오류',
        'WEBSOCKET_CONNECTION_LOST': 'WebSocket 연결 끊김',
        'CIRCUIT_BREAKER_OPEN': '회로 차단기 열림',
        'RETRY_EXHAUSTED': '재시도 횟수 초과'
    }
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_error(self, error_code: str, details: str, context: Dict[str, Any] = None):
        """분류된 오류 로깅"""
        error_desc = self.ERROR_CODES.get(error_code, '알 수 없는 오류')
        
        log_msg = f"[{error_code}] {error_desc}: {details}"
        
        if context:
            # 민감한 정보 제거된 컨텍스트 추가
            safe_context = self._sanitize_context(context)
            log_msg += f" | 컨텍스트: {safe_context}"
        
        self.logger.error(log_msg)
        
        # 시스템 모니터에 오류 기록 (순환 import 방지)
        try:
            from utils.error_handling import system_monitor
            system_monitor.record_error(error_code)
        except ImportError:
            pass  # 모듈이 아직 로드되지 않은 경우 무시
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """컨텍스트에서 민감한 정보 제거"""
        safe_context = {}
        sensitive_keys = {'app_key', 'app_secret', 'access_token', 'password', 'authorization'}
        
        for key, value in context.items():
            if key.lower() in sensitive_keys:
                safe_context[key] = '***'
            else:
                safe_context[key] = value
        
        return safe_context