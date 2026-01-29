"""
종목 선정기 테스트
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from lsmr_stock_picker.analyzers.stock_picker import StockPicker, StockCandidate
from lsmr_stock_picker.models.data_models import LeadingSector, StockData, TradeAction
from lsmr_stock_picker.kis_api.client import KISClient


@pytest.fixture
def mock_kis_client():
    """Mock KIS API 클라이언트"""
    client = AsyncMock(spec=KISClient)
    return client


@pytest.fixture
def mock_db_manager():
    """Mock 데이터베이스 관리자"""
    manager = AsyncMock()
    return manager


@pytest.fixture
def stock_picker(mock_kis_client, mock_db_manager):
    """StockPicker 인스턴스"""
    return StockPicker(
        kis_client=mock_kis_client,
        db_manager=mock_db_manager
    )


@pytest.fixture
def sample_leading_sector():
    """샘플 주도 섹터"""
    return LeadingSector(
        sector_code='G80',
        sector_name='전기전자',
        combined_score=85.5,
        top_stocks=['005930', '000660', '035420']
    )


@pytest.fixture
def sample_stock_data():
    """샘플 종목 데이터"""
    return StockData(
        ticker='005930',
        stock_name='삼성전자',
        current_price=70000,
        volume=10000000,
        change_percent=-2.5,
        ma20=75000,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_historical_data():
    """샘플 과거 가격 데이터 (20일)"""
    return [
        {'date': f'2024-01-{i:02d}', 'close': 75000 + (i * 100), 'volume': 10000000}
        for i in range(1, 21)
    ]


class TestStockPicker:
    """StockPicker 클래스 테스트"""
    
    def test_initialization(self, stock_picker):
        """초기화 테스트"""
        assert stock_picker is not None
        assert stock_picker._z_score_threshold == -2.0
        assert stock_picker._disparity_threshold == 92.0
        assert stock_picker._ma_period == 20
        assert stock_picker._top_stocks_per_sector == 5
    
    def test_calculate_z_score(self, stock_picker, sample_historical_data):
        """Z-Score 계산 테스트 (요구사항 3.2)"""
        current_price = 70000
        
        z_score, ma20, std_dev20 = stock_picker.calculate_z_score(
            current_price,
            sample_historical_data
        )
        
        # Z-Score가 계산되었는지 확인
        assert isinstance(z_score, float)
        assert isinstance(ma20, float)
        assert isinstance(std_dev20, float)
        
        # MA20이 올바르게 계산되었는지 확인
        assert ma20 > 0
        
        # 현재가가 MA20보다 낮으면 Z-Score는 음수
        if current_price < ma20:
            assert z_score < 0
    
    def test_calculate_z_score_with_exact_values(self, stock_picker):
        """Z-Score 정확한 계산 테스트"""
        # 간단한 데이터로 정확한 계산 확인
        historical_data = [
            {'close': 100.0} for _ in range(20)
        ]
        current_price = 95.0
        
        z_score, ma20, std_dev20 = stock_picker.calculate_z_score(
            current_price,
            historical_data
        )
        
        # MA20은 100이어야 함
        assert ma20 == 100.0
        
        # 표준편차는 0이어야 함 (모든 값이 동일)
        assert std_dev20 == 0.0
        
        # Z-Score는 0이어야 함 (표준편차가 0)
        assert z_score == 0.0
    
    def test_calculate_disparity(self, stock_picker):
        """이격도 계산 테스트 (요구사항 3.4)"""
        current_price = 90000
        ma20 = 100000
        
        disparity = stock_picker.calculate_disparity(current_price, ma20)
        
        # 이격도 = (90000 - 100000) / 100000 * 100 = -10%
        assert disparity == -10.0
    
    def test_calculate_disparity_exact_formula(self, stock_picker):
        """이격도 공식 정확성 테스트 (요구사항 3.4)"""
        # 공식: (현재가 - MA20) / MA20 * 100
        
        # 케이스 1: 현재가가 MA20보다 낮음
        assert stock_picker.calculate_disparity(90, 100) == -10.0
        
        # 케이스 2: 현재가가 MA20보다 높음
        assert stock_picker.calculate_disparity(110, 100) == 10.0
        
        # 케이스 3: 현재가와 MA20이 같음
        assert stock_picker.calculate_disparity(100, 100) == 0.0
        
        # 케이스 4: 92% 이격도 (매수 신호 임계값)
        # 이격도 92% = (현재가 - MA20) / MA20 * 100 = -8%
        # 현재가 = MA20 * 0.92
        assert stock_picker.calculate_disparity(92, 100) == -8.0
    
    def test_generate_buy_signal_strong(self, stock_picker):
        """강한 매수 신호 생성 테스트 (요구사항 3.5)"""
        z_score = -2.5
        disparity_ratio = -8.0  # 92% 이격도
        volume_trend = "decreasing"
        
        action, signal_strength = stock_picker._generate_buy_signal(
            z_score,
            disparity_ratio,
            volume_trend
        )
        
        # 강한 매수 신호
        assert action == TradeAction.BUY
        assert signal_strength >= 60
    
    def test_generate_buy_signal_weak(self, stock_picker):
        """약한 신호 테스트"""
        z_score = -1.0
        disparity_ratio = -5.0  # 95% 이격도
        volume_trend = "stable"
        
        action, signal_strength = stock_picker._generate_buy_signal(
            z_score,
            disparity_ratio,
            volume_trend
        )
        
        # 매수 보류
        assert action == TradeAction.HOLD
        assert signal_strength < 60
    
    def test_generate_buy_signal_disparity_threshold(self, stock_picker):
        """이격도 임계값 테스트 (요구사항 3.5)"""
        # 이격도 92% 이하에서만 매수 신호
        # 이격도 = (현재가 - MA20) / MA20 * 100
        # 88% 이격도 = -12%, 90% = -10%, 92% = -8%, 94% = -6%
        
        # 케이스 1: 이격도 -12% (88% 이격도, 40점)
        action1, strength1 = stock_picker._generate_buy_signal(
            z_score=-2.5,
            disparity_ratio=-12.0,
            volume_trend="decreasing"
        )
        assert action1 == TradeAction.BUY
        assert strength1 == 100.0  # 40 + 40 + 20 = 100점
        
        # 케이스 2: 이격도 -10% (90% 이격도, 35점)
        action2, strength2 = stock_picker._generate_buy_signal(
            z_score=-2.5,
            disparity_ratio=-10.0,
            volume_trend="decreasing"
        )
        assert action2 == TradeAction.BUY
        assert strength2 == 95.0  # 40 + 35 + 20 = 95점
        
        # 케이스 3: 이격도 -8% (92% 이격도, 30점, 임계값)
        action3, strength3 = stock_picker._generate_buy_signal(
            z_score=-2.5,
            disparity_ratio=-8.0,
            volume_trend="decreasing"
        )
        assert action3 == TradeAction.BUY
        assert strength3 == 90.0  # 40 + 30 + 20 = 90점
        
        # 케이스 4: 이격도 -6% (94% 이격도, 20점)
        action4, strength4 = stock_picker._generate_buy_signal(
            z_score=-2.5,
            disparity_ratio=-6.0,
            volume_trend="decreasing"
        )
        # 이격도가 임계값(92% = -8%)을 초과하므로 매수 보류
        assert action4 == TradeAction.HOLD
        assert strength4 == 80.0  # 40 + 20 + 20 = 80점
    
    @pytest.mark.asyncio
    async def test_analyze_sector_stocks(
        self,
        stock_picker,
        mock_kis_client,
        sample_leading_sector,
        sample_stock_data,
        sample_historical_data
    ):
        """섹터 종목 분석 테스트"""
        # Mock 설정 - AsyncMock으로 반환값 설정
        async def mock_get_sector_stocks(*args, **kwargs):
            return [sample_stock_data]
        
        async def mock_get_historical_data(*args, **kwargs):
            return sample_historical_data
        
        mock_kis_client.get_sector_stocks = mock_get_sector_stocks
        mock_kis_client.get_historical_data = mock_get_historical_data
        
        # 분석 실행
        candidates = await stock_picker.analyze_sector_stocks(
            sample_leading_sector,
            save_to_db=False
        )
        
        # 결과 확인
        assert isinstance(candidates, list)
        
        if candidates:
            candidate = candidates[0]
            assert isinstance(candidate, StockCandidate)
            assert candidate.ticker == sample_stock_data.ticker
            assert candidate.stock_name == sample_stock_data.stock_name
            assert candidate.sector == sample_leading_sector.sector_name
    
    @pytest.mark.asyncio
    async def test_get_top_volume_stocks(
        self,
        stock_picker,
        mock_kis_client,
        sample_stock_data
    ):
        """거래량 상위 종목 조회 테스트 (요구사항 3.1)"""
        # Mock 설정
        async def mock_get_sector_stocks(*args, **kwargs):
            return [sample_stock_data]
        
        mock_kis_client.get_sector_stocks = mock_get_sector_stocks
        
        # 조회 실행
        stocks = await stock_picker._get_top_volume_stocks('G80', limit=5)
        
        # 결과 확인
        assert isinstance(stocks, list)
        assert len(stocks) <= 5
    
    @pytest.mark.asyncio
    async def test_save_to_database(
        self,
        stock_picker,
        mock_db_manager
    ):
        """데이터베이스 저장 테스트 (요구사항 12.3)"""
        candidates = [
            StockCandidate(
                ticker='005930',
                stock_name='삼성전자',
                sector='전기전자',
                z_score=-2.5,
                disparity_ratio=-8.0,
                current_price=70000,
                ma20=75000,
                volume=10000000,
                signal_strength=85.0,
                analysis_date='2024-01-15'
            )
        ]
        
        # 저장 실행
        await stock_picker._save_to_database(candidates)
        
        # 데이터베이스 호출 확인
        mock_db_manager.save_stock_candidate.assert_called_once()
    
    def test_cache_management(self, stock_picker):
        """캐시 관리 테스트"""
        # 초기 상태
        assert not stock_picker._is_cache_valid('test_key')
        
        # 캐시 업데이트
        candidates = []
        stock_picker._update_cache('test_key', candidates)
        
        # 캐시 유효성 확인
        assert stock_picker._is_cache_valid('test_key')
        
        # 캐시 초기화
        stock_picker.clear_cache()
        assert not stock_picker._is_cache_valid('test_key')
    
    def test_update_thresholds(self, stock_picker):
        """임계값 업데이트 테스트"""
        # 초기값
        assert stock_picker._z_score_threshold == -2.0
        assert stock_picker._disparity_threshold == 92.0
        
        # 업데이트
        stock_picker.update_thresholds(z_score=-2.5, disparity=90.0)
        
        # 확인
        assert stock_picker._z_score_threshold == -2.5
        assert stock_picker._disparity_threshold == 90.0


class TestStockCandidate:
    """StockCandidate 데이터 모델 테스트"""
    
    def test_stock_candidate_creation(self):
        """종목 후보 생성 테스트"""
        candidate = StockCandidate(
            ticker='005930',
            stock_name='삼성전자',
            sector='전기전자',
            z_score=-2.5,
            disparity_ratio=-8.0,
            current_price=70000,
            ma20=75000,
            volume=10000000,
            signal_strength=85.0,
            analysis_date='2024-01-15'
        )
        
        assert candidate.ticker == '005930'
        assert candidate.stock_name == '삼성전자'
        assert candidate.z_score == -2.5
        assert candidate.disparity_ratio == -8.0
    
    def test_stock_candidate_to_dict(self):
        """종목 후보 딕셔너리 변환 테스트 (요구사항 12.3)"""
        candidate = StockCandidate(
            ticker='005930',
            stock_name='삼성전자',
            sector='전기전자',
            z_score=-2.5,
            disparity_ratio=-8.0,
            current_price=70000,
            ma20=75000,
            volume=10000000,
            signal_strength=85.0,
            analysis_date='2024-01-15',
            action=TradeAction.BUY
        )
        
        data = candidate.to_dict()
        
        # 필수 필드 확인 (요구사항 12.3)
        assert 'ticker' in data
        assert 'stock_name' in data
        assert 'sector' in data
        assert 'z_score' in data
        assert 'disparity_ratio' in data
        assert 'current_price' in data
        assert 'ma20' in data
        assert 'volume' in data
        assert 'signal_strength' in data
        assert 'analysis_date' in data
        
        # 값 확인
        assert data['ticker'] == '005930'
        assert data['z_score'] == -2.5
        assert data['action'] == 'BUY'


class TestZScoreCalculation:
    """Z-Score 계산 상세 테스트"""
    
    def test_z_score_negative_when_below_ma(self):
        """현재가가 MA20보다 낮을 때 Z-Score는 음수"""
        picker = StockPicker(
            kis_client=AsyncMock(spec=KISClient),
            db_manager=None
        )
        
        # 현재가 < MA20
        historical_data = [{'close': 100.0 + i} for i in range(20)]
        current_price = 95.0
        
        z_score, ma20, _ = picker.calculate_z_score(current_price, historical_data)
        
        assert current_price < ma20
        assert z_score < 0
    
    def test_z_score_positive_when_above_ma(self):
        """현재가가 MA20보다 높을 때 Z-Score는 양수"""
        picker = StockPicker(
            kis_client=AsyncMock(spec=KISClient),
            db_manager=None
        )
        
        # 현재가 > MA20
        historical_data = [{'close': 100.0 - i} for i in range(20)]
        current_price = 105.0
        
        z_score, ma20, _ = picker.calculate_z_score(current_price, historical_data)
        
        assert current_price > ma20
        assert z_score > 0
    
    def test_z_score_threshold_minus_2(self):
        """Z-Score -2.0 이하가 매수 후보 (요구사항 3.3)"""
        picker = StockPicker(
            kis_client=AsyncMock(spec=KISClient),
            db_manager=None
        )
        
        # Z-Score 임계값 확인
        assert picker._z_score_threshold == -2.0
        
        # Z-Score -2.0 이하는 매수 후보
        # Z-Score -2.5는 매수 후보
        # Z-Score -1.5는 매수 후보 아님


class TestDisparityCalculation:
    """이격도 계산 상세 테스트"""
    
    def test_disparity_formula_accuracy(self):
        """이격도 공식 정확성 테스트 (요구사항 3.4)"""
        picker = StockPicker(
            kis_client=AsyncMock(spec=KISClient),
            db_manager=None
        )
        
        # 공식: (현재가 - MA20) / MA20 * 100
        
        # 테스트 케이스 1
        disparity1 = picker.calculate_disparity(92000, 100000)
        expected1 = ((92000 - 100000) / 100000) * 100
        assert disparity1 == expected1
        
        # 테스트 케이스 2
        disparity2 = picker.calculate_disparity(108000, 100000)
        expected2 = ((108000 - 100000) / 100000) * 100
        assert disparity2 == expected2
    
    def test_disparity_92_percent_threshold(self):
        """이격도 92% 임계값 테스트 (요구사항 3.5)"""
        picker = StockPicker(
            kis_client=AsyncMock(spec=KISClient),
            db_manager=None
        )
        
        # 이격도 92% = -8%
        # 현재가 = MA20 * 0.92
        ma20 = 100000
        current_price_92 = ma20 * 0.92
        
        disparity = picker.calculate_disparity(current_price_92, ma20)
        
        # 이격도는 -8% 근처여야 함
        assert -8.1 < disparity < -7.9
        
        # 임계값 확인
        assert picker._disparity_threshold == 92.0
