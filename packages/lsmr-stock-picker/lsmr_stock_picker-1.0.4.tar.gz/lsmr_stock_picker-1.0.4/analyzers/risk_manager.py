"""
리스크 관리자
포지션 제한, 손절매, 긴급 통제를 시행하는 컴포넌트
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass

from models.data_models import (
    MarketRegime,
    RiskParameters,
    Holding,
    TradeAction
)


logger = logging.getLogger(__name__)


@dataclass
class PositionLimit:
    """포지션 제한 설정"""
    max_stocks_per_sector: int = 3  # 섹터당 최대 종목 수
    max_total_holdings: int = 10    # 총 최대 보유 종목 수
    daily_loss_limit_percent: float = 5.0  # 일일 손실 한도 (%)


@dataclass
class StopLossOrder:
    """손절매 주문"""
    ticker: str
    stock_name: str
    current_price: float
    avg_price: float
    loss_percent: float
    reason: str


class RiskManager:
    """
    리스크 관리자
    
    요구사항:
    - 6.1: 섹터당 최대 3개 종목 제한
    - 6.2: 총 최대 10개 포지션 제한
    - 6.3: 일일 손실 한도 도달 시 패닉 모드
    - 6.4: 플랫폼 리스크 설정 우선순위
    - 6.5: 슬리피지 관리
    """
    
    def __init__(self, position_limit: Optional[PositionLimit] = None):
        """
        리스크 관리자 초기화
        
        Args:
            position_limit: 포지션 제한 설정 (기본값 사용 가능)
        """
        self.position_limit = position_limit or PositionLimit()
        self.panic_mode = False
        self.daily_loss_percent = 0.0
        self.current_risk_params = RiskParameters(
            take_profit_percent=3.0,
            stop_loss_percent=2.5,
            max_position_size=10.0,
            max_sector_exposure=30.0
        )
        
        logger.info(
            f"리스크 관리자 초기화 완료 - "
            f"섹터당 최대: {self.position_limit.max_stocks_per_sector}개, "
            f"총 최대: {self.position_limit.max_total_holdings}개, "
            f"일일 손실 한도: {self.position_limit.daily_loss_limit_percent}%"
        )
    
    def validate_position_limits(
        self,
        holdings: List[Holding],
        new_ticker: str,
        new_sector: str
    ) -> Tuple[bool, str]:
        """
        포지션 제한 검증
        
        요구사항 6.1: 섹터당 최대 3개 종목
        요구사항 6.2: 총 최대 10개 포지션
        
        Args:
            holdings: 현재 보유 종목 리스트
            new_ticker: 신규 매수 종목 티커
            new_sector: 신규 매수 종목 섹터
            
        Returns:
            (검증 통과 여부, 실패 사유)
        """
        # 이미 보유 중인 종목인지 확인
        if any(h.ticker == new_ticker for h in holdings):
            return True, "이미 보유 중인 종목 - 추가 매수 가능"
        
        # 요구사항 6.2: 총 포지션 제한 확인
        if len(holdings) >= self.position_limit.max_total_holdings:
            reason = (
                f"총 포지션 제한 초과 - "
                f"현재: {len(holdings)}개, "
                f"최대: {self.position_limit.max_total_holdings}개"
            )
            logger.warning(reason)
            return False, reason
        
        # 요구사항 6.1: 섹터당 포지션 제한 확인
        sector_holdings = [h for h in holdings if hasattr(h, 'sector') and h.sector == new_sector]
        if len(sector_holdings) >= self.position_limit.max_stocks_per_sector:
            reason = (
                f"섹터 포지션 제한 초과 - "
                f"섹터: {new_sector}, "
                f"현재: {len(sector_holdings)}개, "
                f"최대: {self.position_limit.max_stocks_per_sector}개"
            )
            logger.warning(reason)
            return False, reason
        
        return True, "포지션 제한 검증 통과"
    
    def check_stop_loss_conditions(
        self,
        holdings: List[Holding]
    ) -> List[StopLossOrder]:
        """
        손절매 조건 확인
        
        현재 리스크 파라미터의 stop_loss_percent를 기준으로
        손절매가 필요한 종목을 식별합니다.
        
        Args:
            holdings: 현재 보유 종목 리스트
            
        Returns:
            손절매 주문 리스트
        """
        stop_loss_orders = []
        
        for holding in holdings:
            # 손실률 계산
            loss_percent = ((holding.current_price - holding.avg_price) / holding.avg_price) * 100
            
            # 손절매 조건 확인
            if loss_percent <= -self.current_risk_params.stop_loss_percent:
                order = StopLossOrder(
                    ticker=holding.ticker,
                    stock_name=holding.stock_name,
                    current_price=holding.current_price,
                    avg_price=holding.avg_price,
                    loss_percent=loss_percent,
                    reason=f"손절매 - 손실률 {loss_percent:.2f}% (기준: -{self.current_risk_params.stop_loss_percent}%)"
                )
                stop_loss_orders.append(order)
                logger.warning(
                    f"손절매 신호 - {holding.stock_name}({holding.ticker}): "
                    f"손실률 {loss_percent:.2f}%"
                )
        
        return stop_loss_orders
    
    def update_risk_parameters(
        self,
        regime: MarketRegime
    ) -> RiskParameters:
        """
        시장 체제 기반 동적 리스크 파라미터 업데이트
        
        요구사항 1.5, 1.6, 1.7:
        - BULL: 익절 5%, 손절 3%
        - BEAR: 익절 2%, 손절 2%
        - NEUTRAL: 기본 파라미터
        
        Args:
            regime: 시장 체제
            
        Returns:
            업데이트된 리스크 파라미터
        """
        if regime == MarketRegime.BULL:
            # 요구사항 1.5: 상승장 파라미터
            self.current_risk_params = RiskParameters(
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                max_position_size=10.0,
                max_sector_exposure=30.0
            )
            logger.info("리스크 파라미터 업데이트 - 상승장 모드 (익절: 5%, 손절: 3%)")
        
        elif regime == MarketRegime.BEAR:
            # 요구사항 1.6: 하락장 파라미터
            self.current_risk_params = RiskParameters(
                take_profit_percent=2.0,
                stop_loss_percent=2.0,
                max_position_size=5.0,
                max_sector_exposure=20.0
            )
            logger.info("리스크 파라미터 업데이트 - 하락장 모드 (익절: 2%, 손절: 2%)")
        
        else:  # NEUTRAL
            # 요구사항 1.7: 박스권 기본 파라미터
            self.current_risk_params = RiskParameters(
                take_profit_percent=3.0,
                stop_loss_percent=2.5,
                max_position_size=8.0,
                max_sector_exposure=25.0
            )
            logger.info("리스크 파라미터 업데이트 - 박스권 모드 (익절: 3%, 손절: 2.5%)")
        
        return self.current_risk_params
    
    def check_panic_mode(
        self,
        daily_loss_percent: float
    ) -> bool:
        """
        패닉 모드 확인
        
        요구사항 6.3: 일일 손실 한도 도달 시 패닉 모드 진입
        
        Args:
            daily_loss_percent: 일일 손실률 (%)
            
        Returns:
            패닉 모드 여부
        """
        self.daily_loss_percent = daily_loss_percent
        
        # 요구사항 6.3: 일일 손실 한도 확인
        if abs(daily_loss_percent) >= self.position_limit.daily_loss_limit_percent:
            if not self.panic_mode:
                self.panic_mode = True
                logger.critical(
                    f"패닉 모드 진입 - "
                    f"일일 손실률: {daily_loss_percent:.2f}%, "
                    f"한도: {self.position_limit.daily_loss_limit_percent}%"
                )
            return True
        
        # 손실이 한도 이하로 회복되면 패닉 모드 해제
        if self.panic_mode and abs(daily_loss_percent) < self.position_limit.daily_loss_limit_percent * 0.8:
            self.panic_mode = False
            logger.info(
                f"패닉 모드 해제 - "
                f"일일 손실률: {daily_loss_percent:.2f}%"
            )
        
        return self.panic_mode
    
    def get_emergency_liquidation_orders(
        self,
        holdings: List[Holding]
    ) -> List[Dict]:
        """
        긴급 청산 주문 생성
        
        패닉 모드 또는 긴급 상황 시 모든 포지션을 청산하는 주문을 생성합니다.
        
        Args:
            holdings: 현재 보유 종목 리스트
            
        Returns:
            긴급 청산 주문 리스트
        """
        liquidation_orders = []
        
        for holding in holdings:
            order = {
                'ticker': holding.ticker,
                'stock_name': holding.stock_name,
                'quantity': holding.quantity,
                'action': TradeAction.SELL.value,
                'order_type': 'MARKET',  # 시장가 주문으로 빠른 청산
                'reason': '[EMERGENCY_LIQUIDATION]',
                'priority': 'HIGH'
            }
            liquidation_orders.append(order)
        
        if liquidation_orders:
            logger.critical(
                f"긴급 청산 주문 생성 - {len(liquidation_orders)}개 종목"
            )
        
        return liquidation_orders
    
    def override_with_platform_settings(
        self,
        platform_risk_params: Optional[RiskParameters]
    ) -> None:
        """
        플랫폼 리스크 설정으로 재정의
        
        요구사항 6.4: 플랫폼 수준 리스크 통제 우선순위
        
        Args:
            platform_risk_params: 플랫폼에서 제공하는 리스크 파라미터
        """
        if platform_risk_params is None:
            return
        
        logger.info(
            f"플랫폼 리스크 설정 적용 - "
            f"익절: {platform_risk_params.take_profit_percent}%, "
            f"손절: {platform_risk_params.stop_loss_percent}%"
        )
        
        # 요구사항 6.4: 플랫폼 설정이 로컬 설정을 재정의
        self.current_risk_params = platform_risk_params
    
    def get_order_type_for_execution(
        self,
        action: TradeAction,
        urgency: str = "NORMAL"
    ) -> str:
        """
        실행 주문 타입 결정
        
        요구사항 6.5: 슬리피지 관리를 위한 주문 타입 선택
        
        Args:
            action: 거래 액션 (BUY/SELL)
            urgency: 긴급도 (NORMAL/HIGH/EMERGENCY)
            
        Returns:
            주문 타입 (MARKET/LIMIT/BEST)
        """
        # 요구사항 6.5: 빠른 실행을 위해 시장가 또는 최선 가능 가격 사용
        if urgency == "EMERGENCY":
            return "MARKET"  # 긴급 상황: 시장가
        elif urgency == "HIGH":
            return "BEST"    # 높은 긴급도: 최우선 호가
        else:
            return "LIMIT"   # 일반: 지정가
    
    def calculate_position_size(
        self,
        available_cash: float,
        stock_price: float,
        total_portfolio_value: float
    ) -> int:
        """
        포지션 크기 계산
        
        리스크 파라미터의 max_position_size를 기준으로
        적절한 매수 수량을 계산합니다.
        
        Args:
            available_cash: 가용 현금
            stock_price: 종목 가격
            total_portfolio_value: 총 포트폴리오 가치
            
        Returns:
            매수 수량
        """
        # 최대 포지션 크기 (포트폴리오의 %)
        max_position_value = total_portfolio_value * (self.current_risk_params.max_position_size / 100)
        
        # 가용 현금과 최대 포지션 크기 중 작은 값 선택
        position_value = min(available_cash, max_position_value)
        
        # 수량 계산 (소수점 버림)
        quantity = int(position_value / stock_price)
        
        return quantity
    
    def get_risk_status(self) -> Dict:
        """
        현재 리스크 상태 조회
        
        Returns:
            리스크 상태 정보
        """
        return {
            'panic_mode': self.panic_mode,
            'daily_loss_percent': self.daily_loss_percent,
            'current_risk_params': self.current_risk_params.to_dict(),
            'position_limits': {
                'max_stocks_per_sector': self.position_limit.max_stocks_per_sector,
                'max_total_holdings': self.position_limit.max_total_holdings,
                'daily_loss_limit_percent': self.position_limit.daily_loss_limit_percent
            }
        }
    
    def reset_daily_tracking(self) -> None:
        """
        일일 추적 데이터 초기화
        
        매일 시작 시 호출하여 일일 손실률 등을 초기화합니다.
        """
        self.daily_loss_percent = 0.0
        if self.panic_mode:
            self.panic_mode = False
            logger.info("일일 추적 데이터 초기화 - 패닉 모드 해제")
