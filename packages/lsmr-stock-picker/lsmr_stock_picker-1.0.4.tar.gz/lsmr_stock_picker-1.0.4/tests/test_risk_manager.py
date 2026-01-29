"""
리스크 매니저 테스트
포지션 제한, 손절매, 긴급 청산 기능 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from lsmr_stock_picker.analyzers.risk_manager import RiskManager, RiskParameters
from lsmr_stock_picker.config.settings import SystemConfig, RiskConfig
from lsmr_stock_picker.models.data_models import (
    MarketRegime, StockSignal, TradeAction, Holding
)


@pytest.fixture
def mock_config():
    """테스트용 설정"""
    config = MagicMock()
    config.risk = RiskConfig(
        max_stocks_per_sector=3,
        max_total_holdings=10,
        default_take_profit=3.0,
        default_stop_loss=2.5,
        daily_loss_limit=5.0,
        emergency_stop_timeout=0.5
    )
    config.kis = MagicMock()
    config.kis.account_number = "12345678-01"
    return config


@pytest.fixture
def mock_kis_client():
    """테스트용 KIS 클라이언트"""
    client = AsyncMock()
    
    # 계좌 잔고 조회 모킹
    client.get_account_balance.return_value = {
        'output2': [{
            'tot_evlu_amt': '10000000'  # 1천만원
        }]
    }
    
    # 보유 종목 조회 모킹
    client.get_holdings.return_value = []
    
    # 주문 실행 모킹
    client.execute_order.return_value = {
        'status': 'SUCCESS',
        'order_number': 'TEST123',
        'message': '주문 성공'
    }
    
    return client


@pytest.fixture
async def risk_manager(mock_config, mock_kis_client):
    """테스트용 리스크 매니저"""
    manager = RiskManager(mock_config, mock_kis_client)
    await manager.initialize()
    return manager


class TestRiskManager:
    """리스크 매니저 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_config, mock_kis_client):
        """초기화 테스트"""
        manager = RiskManager(mock_config, mock_kis_client)
        await manager.initialize()
        
        # 기본 매개변수 확인
        assert manager.current_params.take_profit_percent == 3.0
        assert manager.current_params.stop_loss_percent == 2.5
        assert manager.current_params.max_stocks_per_sector == 3
        assert manager.current_params.max_total_holdings == 10
        
        # 패닉 모드 비활성화 확인
        assert not manager.panic_mode.is_active
        assert not manager.emergency_stop_active
    
    @pytest.mark.asyncio
    async def test_validate_position_limits_buy_signal(self, risk_manager):
        """매수 신호 포지션 제한 검증 테스트"""
        # 정상적인 매수 신호
        signal = StockSignal(
            ticker="005930",
            stock_name="삼성전자",
            z_score=-2.1,
            disparity_ratio=91.5,
            signal_strength=85.0,
            action=TradeAction.BUY,
            sector_code="IT"
        )
        
        can_trade, reason = await risk_manager.validate_position_limits(signal)
        
        # 정상적으로 거래 가능해야 함
        assert can_trade
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_validate_position_limits_sell_signal(self, risk_manager):
        """매도 신호는 항상 허용되어야 함"""
        signal = StockSignal(
            ticker="005930",
            stock_name="삼성전자",
            z_score=0.0,
            disparity_ratio=100.0,
            signal_strength=50.0,
            action=TradeAction.SELL,
            sector_code="IT"
        )
        
        can_trade, reason = await risk_manager.validate_position_limits(signal)
        
        # 매도는 항상 허용
        assert can_trade
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_validate_position_limits_panic_mode(self, risk_manager):
        """패닉 모드에서는 매수 금지"""
        # 패닉 모드 활성화
        risk_manager.panic_mode.is_active = True
        
        signal = StockSignal(
            ticker="005930",
            stock_name="삼성전자",
            z_score=-2.1,
            disparity_ratio=91.5,
            signal_strength=85.0,
            action=TradeAction.BUY,
            sector_code="IT"
        )
        
        can_trade, reason = await risk_manager.validate_position_limits(signal)
        
        # 패닉 모드에서는 매수 금지
        assert not can_trade
        assert "패닉 모드" in reason
    
    @pytest.mark.asyncio
    async def test_validate_position_limits_emergency_stop(self, risk_manager):
        """긴급 정지에서는 모든 거래 금지"""
        # 긴급 정지 활성화
        risk_manager.emergency_stop_active = True
        
        signal = StockSignal(
            ticker="005930",
            stock_name="삼성전자",
            z_score=-2.1,
            disparity_ratio=91.5,
            signal_strength=85.0,
            action=TradeAction.BUY,
            sector_code="IT"
        )
        
        can_trade, reason = await risk_manager.validate_position_limits(signal)
        
        # 긴급 정지에서는 모든 거래 금지
        assert not can_trade
        assert "긴급 정지" in reason
    
    @pytest.mark.asyncio
    async def test_check_stop_loss_conditions(self, risk_manager):
        """손절매 조건 확인 테스트"""
        # 테스트 보유 종목 (손실 상황)
        holdings = [
            Holding(
                ticker="005930",
                stock_name="삼성전자",
                account="12345678-01",
                quantity=10,
                avg_price=75000,
                current_price=72000,
                profit_rate=-4.0,  # 손절 기준(-2.5%) 초과
                weight=30.0
            ),
            Holding(
                ticker="000660",
                stock_name="SK하이닉스",
                account="12345678-01",
                quantity=5,
                avg_price=130000,
                current_price=125000,
                profit_rate=-3.8,  # 손절 기준 초과
                weight=25.0
            ),
            Holding(
                ticker="035420",
                stock_name="NAVER",
                account="12345678-01",
                quantity=3,
                avg_price=200000,
                current_price=210000,
                profit_rate=5.0,  # 익절 기준(3%) 초과
                weight=20.0
            )
        ]
        
        stop_orders = await risk_manager.check_stop_loss_conditions(holdings)
        
        # 3개 종목 모두 손절/익절 대상
        assert len(stop_orders) == 3
        
        # 손절매 주문 확인
        samsung_order = next(order for order in stop_orders if order.ticker == "005930")
        assert "손절매" in samsung_order.reason
        
        # 익절 주문 확인
        naver_order = next(order for order in stop_orders if order.ticker == "035420")
        assert "익절" in naver_order.reason
    
    def test_update_risk_parameters_bull_market(self, risk_manager):
        """강세장 리스크 매개변수 업데이트 테스트"""
        risk_manager.update_risk_parameters(MarketRegime.BULL)
        
        # 강세장 매개변수 확인
        assert risk_manager.current_params.take_profit_percent == 5.0
        assert risk_manager.current_params.stop_loss_percent == 3.0
    
    def test_update_risk_parameters_bear_market(self, risk_manager):
        """약세장 리스크 매개변수 업데이트 테스트"""
        risk_manager.update_risk_parameters(MarketRegime.BEAR)
        
        # 약세장 매개변수 확인
        assert risk_manager.current_params.take_profit_percent == 2.0
        assert risk_manager.current_params.stop_loss_percent == 2.0
    
    def test_update_risk_parameters_neutral_market(self, risk_manager):
        """중립 시장 리스크 매개변수 업데이트 테스트"""
        risk_manager.update_risk_parameters(MarketRegime.NEUTRAL)
        
        # 기본값 확인
        assert risk_manager.current_params.take_profit_percent == 3.0
        assert risk_manager.current_params.stop_loss_percent == 2.5
    
    def test_update_parameters_hot_update(self, risk_manager):
        """매개변수 핫 업데이트 테스트"""
        # 매개변수 업데이트
        success = risk_manager.update_parameters(
            take_profit=4.0,
            stop_loss=2.0
        )
        
        assert success
        assert risk_manager.current_params.take_profit_percent == 4.0
        assert risk_manager.current_params.stop_loss_percent == 2.0
    
    def test_update_parameters_partial_update(self, risk_manager):
        """부분 매개변수 업데이트 테스트"""
        original_stop_loss = risk_manager.current_params.stop_loss_percent
        
        # 익절만 업데이트
        success = risk_manager.update_parameters(take_profit=6.0)
        
        assert success
        assert risk_manager.current_params.take_profit_percent == 6.0
        assert risk_manager.current_params.stop_loss_percent == original_stop_loss
    
    @pytest.mark.asyncio
    async def test_emergency_liquidate_all_no_holdings(self, risk_manager):
        """보유 종목이 없을 때 긴급 청산 테스트"""
        # 보유 종목 없음으로 설정
        risk_manager.kis_client.get_holdings.return_value = []
        
        results = await risk_manager.emergency_liquidate_all()
        
        # 청산할 종목이 없으므로 빈 결과
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self, risk_manager):
        """긴급 정지 테스트"""
        result = await risk_manager.emergency_stop()
        
        # 긴급 정지 성공 확인
        assert result['status'] == 'SUCCESS'
        assert 'timestamp' in result
        assert 'liquidation_results' in result
        assert risk_manager.emergency_stop_active
        assert risk_manager.panic_mode.is_active
    
    def test_reset_emergency_stop(self, risk_manager):
        """긴급 정지 해제 테스트"""
        # 긴급 정지 활성화
        risk_manager.emergency_stop_active = True
        
        # 해제
        success = risk_manager.reset_emergency_stop()
        
        assert success
        assert not risk_manager.emergency_stop_active
    
    def test_reset_panic_mode(self, risk_manager):
        """패닉 모드 해제 테스트"""
        # 패닉 모드 활성화
        risk_manager.panic_mode.is_active = True
        
        # 해제
        success = risk_manager.reset_panic_mode()
        
        assert success
        assert not risk_manager.panic_mode.is_active
    
    def test_get_risk_status(self, risk_manager):
        """리스크 상태 정보 조회 테스트"""
        status = risk_manager.get_risk_status()
        
        # 필수 필드 확인
        assert 'current_parameters' in status
        assert 'panic_mode' in status
        assert 'emergency_stop_active' in status
        assert 'timestamp' in status
        
        # 매개변수 정보 확인
        params = status['current_parameters']
        assert 'take_profit_percent' in params
        assert 'stop_loss_percent' in params
        assert 'max_stocks_per_sector' in params
        assert 'max_total_holdings' in params
    
    @pytest.mark.asyncio
    async def test_get_current_holdings(self, risk_manager):
        """현재 보유 종목 조회 테스트"""
        # 테스트 데이터 설정 - get_account_balance 응답 형식에 맞춤
        risk_manager.kis_client.get_account_balance.return_value = {
            'output1': [
                {
                    'pdno': '005930',
                    'prdt_name': '삼성전자',
                    'hldg_qty': '10',
                    'pchs_avg_pric': '75000.0',
                    'prpr': '77000.0'
                }
            ],
            'output2': [{}]
        }
        
        holdings = await risk_manager.get_current_holdings()
        
        assert len(holdings) == 1
        assert holdings[0].ticker == '005930'
        assert holdings[0].stock_name == '삼성전자'
        assert holdings[0].quantity == 10
        assert holdings[0].avg_price == 75000.0
        assert holdings[0].current_price == 77000.0


@pytest.mark.asyncio
async def test_risk_manager_integration():
    """리스크 매니저 통합 테스트"""
    # 실제 설정으로 테스트 (KIS API 호출 없이)
    config = SystemConfig.load(validate=False)  # 검증 비활성화
    
    # KIS 클라이언트 모킹
    with patch('lsmr_stock_picker.analyzers.risk_manager.KISClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # 계좌 잔고 모킹
        mock_client.get_account_balance.return_value = {
            'output2': [{'tot_evlu_amt': '10000000'}]
        }
        mock_client.get_holdings.return_value = []
        
        # 리스크 매니저 생성 및 초기화
        risk_manager = RiskManager(config, mock_client)
        await risk_manager.initialize()
        
        # 기본 기능 테스트
        assert risk_manager.current_params.max_total_holdings == 10
        assert not risk_manager.panic_mode.is_active
        
        # 시장 상황별 매개변수 조정 테스트
        risk_manager.update_risk_parameters(MarketRegime.BULL)
        assert risk_manager.current_params.take_profit_percent == 5.0
        
        # 리스크 상태 조회 테스트
        status = risk_manager.get_risk_status()
        assert status['emergency_stop_active'] == False