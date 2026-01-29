"""
시스템 설정 관리
KIS API 자격 증명 및 시스템 매개변수 관리
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class Environment(Enum):
    """환경 설정"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class ConfigurationError(Exception):
    """설정 오류"""
    pass


@dataclass
class KISConfig:
    """KIS API 설정"""
    app_key: str
    app_secret: str
    base_url: str
    account_number: str
    environment: Environment = Environment.DEVELOPMENT
    
    @classmethod
    def from_env(cls, validate: bool = True) -> 'KISConfig':
        """환경 변수에서 KIS 설정 로드"""
        try:
            config = cls(
                app_key=os.getenv('KIS_APP_KEY', ''),
                app_secret=os.getenv('KIS_APP_SECRET', ''),
                base_url=os.getenv('KIS_BASE_URL', 'https://openapi.koreainvestment.com:9443'),
                account_number=os.getenv('KIS_ACCOUNT_NUMBER', ''),
                environment=Environment(os.getenv('ENVIRONMENT', 'development'))
            )
            
            # 검증 옵션이 활성화된 경우에만 검증 수행
            if validate:
                validation_errors = config.validate_detailed()
                if validation_errors:
                    raise ConfigurationError(f"KIS 설정 오류: {', '.join(validation_errors)}")
            
            return config
            
        except ValueError as e:
            if "Environment" in str(e):
                raise ConfigurationError(f"잘못된 환경 설정: {os.getenv('ENVIRONMENT')}. 'development', 'production', 'testing' 중 하나여야 합니다.")
            raise ConfigurationError(f"KIS 설정 로드 오류: {e}")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"KIS 설정 로드 중 예상치 못한 오류: {e}")
    
    def validate(self) -> bool:
        """설정 유효성 검사 (간단)"""
        return bool(self.app_key and self.app_secret and self.account_number)
    
    def validate_detailed(self) -> List[str]:
        """상세 설정 유효성 검사 - 요구사항 7.1, 7.2"""
        errors = []
        
        if not self.app_key:
            errors.append("KIS_APP_KEY 환경 변수가 설정되지 않았습니다")
        elif len(self.app_key) < 10:
            errors.append("KIS_APP_KEY가 너무 짧습니다 (최소 10자)")
        
        if not self.app_secret:
            errors.append("KIS_APP_SECRET 환경 변수가 설정되지 않았습니다")
        elif len(self.app_secret) < 10:
            errors.append("KIS_APP_SECRET이 너무 짧습니다 (최소 10자)")
        
        if not self.account_number:
            errors.append("KIS_ACCOUNT_NUMBER 환경 변수가 설정되지 않았습니다")
        else:
            # 하이픈 제거 후 검증 (예: 46496414-01 -> 4649641401)
            account_no_clean = self.account_number.replace('-', '')
            if len(account_no_clean) != 10:
                errors.append(f"KIS_ACCOUNT_NUMBER는 하이픈 제외 10자리여야 합니다 (현재: {len(account_no_clean)}자리)")
        
        if not self.base_url:
            errors.append("KIS_BASE_URL이 설정되지 않았습니다")
        elif not self.base_url.startswith('https://'):
            errors.append("KIS_BASE_URL은 HTTPS로 시작해야 합니다")
        
        return errors


@dataclass
class RiskConfig:
    """리스크 관리 설정"""
    max_stocks_per_sector: int = 3
    max_total_holdings: int = 10
    default_take_profit: float = 3.0  # %
    default_stop_loss: float = 2.5    # %
    daily_loss_limit: float = 5.0     # %
    emergency_stop_timeout: float = 0.5  # seconds


@dataclass
class TradingConfig:
    """거래 설정"""
    z_score_threshold: float = -2.0
    disparity_threshold: float = 92.0  # %
    volume_confirmation_required: bool = True
    signal_generation_timeout: float = 0.1  # seconds
    data_processing_timeout: float = 0.05   # seconds


@dataclass
class SystemConfig:
    """전체 시스템 설정"""
    kis: KISConfig
    risk: RiskConfig
    trading: TradingConfig
    database_url: str
    log_level: str = "INFO"
    health_broadcast_interval: int = 5  # seconds
    host: str = "0.0.0.0"
    port: int = 8000
    
    @classmethod
    def load(cls, validate: bool = True) -> 'SystemConfig':
        """시스템 설정 로드"""
        try:
            config = cls(
                kis=KISConfig.from_env(validate=validate),
                risk=RiskConfig(),
                trading=TradingConfig(),
                database_url=os.getenv('DATABASE_URL', 'postgresql://lsmr_user:lsmr_password@localhost:5432/lsmr_db'),
                log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                health_broadcast_interval=int(os.getenv('HEALTH_BROADCAST_INTERVAL', '5')),
                host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', '8000'))
            )
            
            # 검증 옵션이 활성화된 경우에만 전체 설정 검증
            if validate:
                validation_errors = config.validate_detailed()
                if validation_errors:
                    raise ConfigurationError(f"시스템 설정 오류: {', '.join(validation_errors)}")
            
            return config
            
        except ValueError as e:
            raise ConfigurationError(f"설정 값 변환 오류: {e}")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"시스템 설정 로드 중 예상치 못한 오류: {e}")
    
    def validate(self) -> bool:
        """전체 설정 유효성 검사 (간단)"""
        return self.kis.validate()
    
    def validate_detailed(self) -> List[str]:
        """상세 시스템 설정 유효성 검사"""
        errors = []
        
        # KIS 설정 검증
        errors.extend(self.kis.validate_detailed())
        
        # 데이터베이스 URL 검증
        if not self.database_url:
            errors.append("DATABASE_URL 환경 변수가 설정되지 않았습니다")
        elif not self.database_url.startswith('postgresql://'):
            errors.append("DATABASE_URL은 postgresql://로 시작해야 합니다")
        
        # 로그 레벨 검증
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            errors.append(f"LOG_LEVEL은 {valid_log_levels} 중 하나여야 합니다")
        
        # 서버 설정 검증
        if self.port < 1 or self.port > 65535:
            errors.append("PORT는 1-65535 사이여야 합니다")
        
        # 건강 상태 브로드캐스트 간격 검증
        if self.health_broadcast_interval < 1 or self.health_broadcast_interval > 60:
            errors.append("HEALTH_BROADCAST_INTERVAL은 1-60초 사이여야 합니다")
        
        # 리스크 설정 검증
        if self.risk.max_stocks_per_sector < 1 or self.risk.max_stocks_per_sector > 10:
            errors.append("max_stocks_per_sector는 1-10 사이여야 합니다")
        
        if self.risk.max_total_holdings < 1 or self.risk.max_total_holdings > 50:
            errors.append("max_total_holdings는 1-50 사이여야 합니다")
        
        if self.risk.emergency_stop_timeout <= 0 or self.risk.emergency_stop_timeout > 5:
            errors.append("emergency_stop_timeout은 0-5초 사이여야 합니다")
        
        # 거래 설정 검증
        if self.trading.z_score_threshold > 0:
            errors.append("z_score_threshold는 음수여야 합니다")
        
        if self.trading.disparity_threshold < 50 or self.trading.disparity_threshold > 100:
            errors.append("disparity_threshold는 50-100% 사이여야 합니다")
        
        if self.trading.signal_generation_timeout <= 0 or self.trading.signal_generation_timeout > 1:
            errors.append("signal_generation_timeout은 0-1초 사이여야 합니다")
        
        if self.trading.data_processing_timeout <= 0 or self.trading.data_processing_timeout > 0.5:
            errors.append("data_processing_timeout은 0-0.5초 사이여야 합니다")
        
        return errors