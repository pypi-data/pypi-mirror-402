"""
데이터 모델 테스트
"""

import pytest
from datetime import datetime
from lsmr_stock_picker.models.data_models import (
    Strategy, TradeLog, Holding, SystemHealthMetrics, ProcessStatus,
    LeadingSector, StockAnalysis, StockSignal, IndexData, StockData,
    MarketRegime, TradeAction, StrategyStatus, VolumeTrend,
    validate_data_model, serialize_to_json,
    validate_ticker_format, validate_reason_code_format, validate_percentage
)


class TestStrategy:
    """Strategy 데이터 모델 테스트"""
    
    def test_valid_strategy(self):
        """유효한 전략 데이터 테스트"""
        strategy = Strategy(
            id="lsmr-001",
            name="LSMR Stock Picker",
            status="active",
            return_rate=5.2,
            account="12345678",
            take_profit_percent=5.0,
            stop_loss_percent=3.0
        )
        
        errors = strategy.validate()
        assert errors == []
        
        # JSON 직렬화 테스트 (mockData.ts 스펙 준수)
        json_data = strategy.to_dict()
        assert json_data["returnRate"] == 5.2  # camelCase
        assert json_data["takeProfitPercent"] == 5.0  # camelCase
        assert json_data["stopLossPercent"] == 3.0  # camelCase
    
    def test_invalid_strategy(self):
        """잘못된 전략 데이터 테스트"""
        strategy = Strategy(
            id="",  # 빈 ID
            name="Test",
            status="invalid_status",  # 잘못된 상태
            return_rate=5.0,
            account="123",
            take_profit_percent=-1.0,  # 음수
            stop_loss_percent=150.0  # 100% 초과
        )
        
        errors = strategy.validate()
        assert len(errors) > 0
        assert any("잘못된 상태 값" in error for error in errors)
        assert any("take_profit_percent" in error for error in errors)


class TestTradeLog:
    """TradeLog 데이터 모델 테스트"""
    
    def test_valid_trade_log(self):
        """유효한 거래 로그 테스트"""
        trade_log = TradeLog(
            timestamp=datetime.now(),
            strategy="lsmr-001",
            action="BUY",
            stock_name="삼성전자",
            ticker="005930",
            quantity=10,
            price=75000.0,
            reason="[Z-Score -2.2]",
            category="Trade"
        )
        
        errors = trade_log.validate()
        assert errors == []
        
        # JSON 직렬화 테스트 (mockData.ts 스펙 준수)
        json_data = trade_log.to_dict()
        assert json_data["stockName"] == "삼성전자"  # camelCase
        assert json_data["category"] == "Trade"
    
    def test_invalid_trade_log(self):
        """잘못된 거래 로그 테스트"""
        trade_log = TradeLog(
            timestamp=datetime.now(),
            strategy="test",
            action="INVALID",  # 잘못된 액션
            stock_name="테스트",
            ticker="INVALID",  # 잘못된 티커
            quantity=-5,  # 음수 수량
            price=-1000.0,  # 음수 가격
            reason="잘못된 이유",  # 잘못된 형식
            category="Wrong"  # 잘못된 카테고리
        )
        
        errors = trade_log.validate()
        assert len(errors) > 0
        assert any("티커는 6자리 숫자여야 합니다" in error for error in errors)
        assert any("이유 코드는 [내용] 형태여야 합니다" in error for error in errors)
        assert any("카테고리는 'Trade'여야 합니다" in error for error in errors)


class TestHolding:
    """Holding 데이터 모델 테스트"""
    
    def test_valid_holding(self):
        """유효한 보유 종목 테스트"""
        holding = Holding(
            ticker="005930",
            stock_name="삼성전자",
            account="12345678",
            quantity=10,
            avg_price=75000.0,
            current_price=76000.0,
            profit_rate=1.33,
            weight=15.5
        )
        
        errors = holding.validate()
        assert errors == []
        
        # JSON 직렬화 테스트 (mockData.ts 스펙 준수)
        json_data = holding.to_dict()
        assert json_data["stockName"] == "삼성전자"  # camelCase
        assert json_data["avgPrice"] == 75000.0  # camelCase
        assert json_data["currentPrice"] == 76000.0  # camelCase
        assert json_data["profitRate"] == 1.33  # camelCase


class TestSystemHealthMetrics:
    """SystemHealthMetrics 데이터 모델 테스트"""
    
    def test_valid_health_metrics(self):
        """유효한 시스템 건강 상태 테스트"""
        process = ProcessStatus(
            name="lsmr-engine",
            status="running",
            cpu_percent=15.5,
            memory_mb=256.0
        )
        
        health_metrics = SystemHealthMetrics(
            cpu_usage=25.7,
            memory_usage=2.5,
            memory_total=8.0,
            processes=[process],
            timestamp=datetime.now(),
            kis_api_connected=True
        )
        
        errors = health_metrics.validate()
        assert errors == []
        
        json_data = health_metrics.to_dict()
        assert "timestamp" in json_data
        assert "kis_api_connected" in json_data
        assert len(json_data["processes"]) == 1
    
    def test_invalid_memory_usage(self):
        """잘못된 메모리 사용량 테스트"""
        health_metrics = SystemHealthMetrics(
            cpu_usage=25.7,
            memory_usage=10.0,  # 총 메모리보다 큼
            memory_total=8.0,
            processes=[],
            timestamp=datetime.now()
        )
        
        errors = health_metrics.validate()
        assert any("메모리 사용량이 총 메모리보다 클 수 없습니다" in error for error in errors)


class TestValidationFunctions:
    """검증 함수 테스트"""
    
    def test_validate_ticker_format(self):
        """티커 형식 검증 테스트"""
        assert validate_ticker_format("005930") is None  # 유효
        assert validate_ticker_format("12345") is not None  # 5자리
        assert validate_ticker_format("1234567") is not None  # 7자리
        assert validate_ticker_format("ABCDEF") is not None  # 문자
        assert validate_ticker_format(123456) is not None  # 숫자 타입
    
    def test_validate_reason_code_format(self):
        """이유 코드 형식 검증 테스트"""
        assert validate_reason_code_format("[Z-Score -2.2]") is None  # 유효
        assert validate_reason_code_format("[Leading Stock Pullback]") is None  # 유효
        assert validate_reason_code_format("Z-Score -2.2") is not None  # 대괄호 없음
        assert validate_reason_code_format("") is not None  # 빈 문자열
        assert validate_reason_code_format(123) is not None  # 숫자 타입
    
    def test_validate_percentage(self):
        """퍼센티지 검증 테스트"""
        assert validate_percentage(50.0, "test") is None  # 유효
        assert validate_percentage(0.0, "test") is None  # 경계값
        assert validate_percentage(100.0, "test") is None  # 경계값
        assert validate_percentage(-1.0, "test") is not None  # 음수
        assert validate_percentage(101.0, "test") is not None  # 100% 초과
        assert validate_percentage("50", "test") is not None  # 문자열


class TestEnums:
    """Enum 클래스 테스트"""
    
    def test_market_regime_values(self):
        """MarketRegime enum 값 테스트"""
        assert MarketRegime.BULL.value == "bull"
        assert MarketRegime.BEAR.value == "bear"
        assert MarketRegime.NEUTRAL.value == "neutral"
    
    def test_trade_action_values(self):
        """TradeAction enum 값 테스트"""
        assert TradeAction.BUY.value == "BUY"
        assert TradeAction.SELL.value == "SELL"
        assert TradeAction.HOLD.value == "HOLD"
    
    def test_strategy_status_values(self):
        """StrategyStatus enum 값 테스트"""
        assert StrategyStatus.ACTIVE.value == "active"
        assert StrategyStatus.INACTIVE.value == "inactive"
        assert StrategyStatus.ERROR.value == "error"


class TestUtilityFunctions:
    """유틸리티 함수 테스트"""
    
    def test_serialize_to_json(self):
        """JSON 직렬화 테스트"""
        strategy = Strategy(
            id="test-001",
            name="테스트 전략",
            status="active",
            return_rate=3.5,
            account="12345678",
            take_profit_percent=5.0,
            stop_loss_percent=3.0
        )
        
        json_str = serialize_to_json(strategy)
        assert "returnRate" in json_str  # camelCase 확인
        assert "테스트 전략" in json_str  # 한글 지원 확인
    
    def test_validate_data_model(self):
        """데이터 모델 검증 유틸리티 테스트"""
        valid_strategy = Strategy(
            id="test",
            name="Test",
            status="active",
            return_rate=5.0,
            account="12345678",
            take_profit_percent=5.0,
            stop_loss_percent=3.0
        )
        
        errors = validate_data_model(valid_strategy)
        assert errors == []
        
        # 검증 메서드가 없는 객체 테스트
        class NoValidateMethod:
            pass
        
        errors = validate_data_model(NoValidateMethod())
        assert len(errors) > 0
        assert "검증 메서드가 없는 객체입니다" in errors[0]