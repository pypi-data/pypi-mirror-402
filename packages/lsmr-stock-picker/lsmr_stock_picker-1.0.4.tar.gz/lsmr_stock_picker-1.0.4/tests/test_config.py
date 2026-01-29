"""
설정 관리 테스트
"""

import os
import pytest
from unittest.mock import patch

from lsmr_stock_picker.config.settings import (
    KISConfig, 
    SystemConfig, 
    Environment,
    RiskConfig,
    TradingConfig
)


class TestKISConfig:
    """KIS 설정 테스트"""
    
    def test_from_env_with_valid_values(self):
        """유효한 환경 변수로 설정 생성"""
        with patch.dict(os.environ, {
            'KIS_APP_KEY': 'test_key_1234567890',  # 10자 이상
            'KIS_APP_SECRET': 'test_secret_1234567890',  # 10자 이상
            'KIS_BASE_URL': 'https://test.api.com',
            'KIS_ACCOUNT_NUMBER': '1234567890',  # 정확히 10자
            'ENVIRONMENT': 'production'
        }):
            config = KISConfig.from_env(validate=False)  # 테스트에서는 검증 비활성화
            
            assert config.app_key == 'test_key_1234567890'
            assert config.app_secret == 'test_secret_1234567890'
            assert config.base_url == 'https://test.api.com'
            assert config.account_number == '1234567890'
            assert config.environment == Environment.PRODUCTION
    
    def test_from_env_with_defaults(self):
        """기본값으로 설정 생성"""
        with patch.dict(os.environ, {}, clear=True):
            config = KISConfig.from_env(validate=False)  # 테스트에서는 검증 비활성화
            
            assert config.app_key == ''
            assert config.app_secret == ''
            assert config.base_url == 'https://openapi.koreainvestment.com:9443'
            assert config.account_number == ''
            assert config.environment == Environment.DEVELOPMENT
    
    def test_validate_with_valid_config(self):
        """유효한 설정 검증"""
        config = KISConfig(
            app_key='test_key',
            app_secret='test_secret',
            base_url='https://test.api.com',
            account_number='12345678-01'
        )
        
        assert config.validate() is True
    
    def test_validate_with_missing_values(self):
        """누락된 값이 있는 설정 검증"""
        config = KISConfig(
            app_key='',
            app_secret='test_secret',
            base_url='https://test.api.com',
            account_number='12345678-01'
        )
        
        assert config.validate() is False


class TestSystemConfig:
    """시스템 설정 테스트"""
    
    def test_load_with_valid_env(self):
        """유효한 환경 변수로 시스템 설정 로드"""
        with patch.dict(os.environ, {
            'KIS_APP_KEY': 'test_key_1234567890',  # 10자 이상
            'KIS_APP_SECRET': 'test_secret_1234567890',  # 10자 이상
            'KIS_ACCOUNT_NUMBER': '1234567890'  # 정확히 10자
        }):
            config = SystemConfig.load(validate=False)  # 테스트에서는 검증 비활성화
            
            assert isinstance(config.kis, KISConfig)
            assert isinstance(config.risk, RiskConfig)
            assert isinstance(config.trading, TradingConfig)
            assert config.log_level == "INFO"
    
    def test_validate_with_valid_config(self, mock_system_config):
        """유효한 시스템 설정 검증"""
        assert mock_system_config.validate() is True
    
    def test_validate_with_invalid_kis_config(self):
        """유효하지 않은 KIS 설정으로 시스템 설정 검증"""
        invalid_kis_config = KISConfig(
            app_key='',
            app_secret='',
            base_url='',
            account_number=''
        )
        
        config = SystemConfig(
            kis=invalid_kis_config,
            risk=RiskConfig(),
            trading=TradingConfig()
        )
        
        assert config.validate() is False


class TestRiskConfig:
    """리스크 설정 테스트"""
    
    def test_default_values(self):
        """기본값 확인"""
        config = RiskConfig()
        
        assert config.max_stocks_per_sector == 3
        assert config.max_total_holdings == 10
        assert config.default_take_profit == 3.0
        assert config.default_stop_loss == 2.5
        assert config.daily_loss_limit == 5.0
        assert config.emergency_stop_timeout == 0.5


class TestTradingConfig:
    """거래 설정 테스트"""
    
    def test_default_values(self):
        """기본값 확인"""
        config = TradingConfig()
        
        assert config.z_score_threshold == -2.0
        assert config.disparity_threshold == 92.0
        assert config.volume_confirmation_required is True
        assert config.signal_generation_timeout == 0.1
        assert config.data_processing_timeout == 0.05