"""
시장 상황 분석기 (Market Regime Analyzer)
KOSPI/KOSDAQ 지수 분석을 통한 시장 상황 판단 및 리스크 매개변수 설정
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from models.data_models import MarketRegime
from kis_api.client import KISClient, KISAPIError, IndexData
from config.settings import RiskConfig


logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """시장 상황별 리스크 매개변수"""
    take_profit_percent: float
    stop_loss_percent: float
    regime: MarketRegime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'take_profit_percent': self.take_profit_percent,
            'stop_loss_percent': self.stop_loss_percent,
            'regime': self.regime.value
        }


@dataclass
class MarketAnalysisResult:
    """시장 분석 결과"""
    regime: MarketRegime
    kospi_data: IndexData
    kosdaq_data: IndexData
    risk_parameters: RiskParameters
    analysis_timestamp: datetime
    confidence_score: float  # 0-100, 분석 신뢰도
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'regime': self.regime.value,
            'kospi_data': self.kospi_data.to_dict(),
            'kosdaq_data': self.kosdaq_data.to_dict(),
            'risk_parameters': self.risk_parameters.to_dict(),
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'confidence_score': self.confidence_score
        }


class MarketRegimeAnalyzer:
    """
    시장 상황 분석기
    
    요구사항:
    - 1.1: KOSPI/KOSDAQ 지수 데이터 조회
    - 1.2, 1.3, 1.4: 시장 체제 분류 (BULL/BEAR/NEUTRAL)
    - 1.5, 1.6, 1.7: 시장 체제 기반 리스크 파라미터 매핑
    - 12.1: 결과를 데이터베이스에 저장
    """
    
    def __init__(
        self,
        kis_client: KISClient,
        db_manager=None,
        risk_config: Optional[RiskConfig] = None
    ):
        """
        초기화
        
        Args:
            kis_client: KIS API 클라이언트
            db_manager: 데이터베이스 관리자 (선택사항)
            risk_config: 리스크 설정 (선택사항)
        """
        self.kis_client = kis_client
        self.db_manager = db_manager
        self.risk_config = risk_config or RiskConfig()
        
        # 캐시 설정
        self._cache: Optional[MarketAnalysisResult] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # 5분 캐시
        
        # 성능 최적화
        self._last_analysis_time: float = 0
        self._min_analysis_interval: float = 30.0  # 30초 최소 간격
        
        logger.info("Market Regime Analyzer 초기화 완료")
    
    async def analyze_market_regime(self, use_cache: bool = True, save_to_db: bool = True) -> MarketAnalysisResult:
        """
        시장 상황 분석 실행 (요구사항 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 12.1)
        
        Args:
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            MarketAnalysisResult: 시장 분석 결과
            
        Raises:
            KISAPIError: API 호출 실패시
        """
        try:
            # 캐시 확인
            if use_cache and self._is_cache_valid():
                logger.debug("캐시된 시장 분석 결과 반환")
                return self._cache
            
            # 성능 최적화: 최소 간격 확인
            current_time = asyncio.get_event_loop().time()
            if current_time - self._last_analysis_time < self._min_analysis_interval:
                if self._cache:
                    logger.debug("최소 분석 간격 미달, 캐시된 결과 반환")
                    return self._cache
            
            logger.info("시장 상황 분석 시작")
            analysis_start = datetime.now()
            
            # KOSPI, KOSDAQ 데이터 병렬 조회
            kospi_task = self.kis_client.get_index_data('0001')  # KOSPI
            kosdaq_task = self.kis_client.get_index_data('1001')  # KOSDAQ
            
            kospi_data, kosdaq_data = await asyncio.gather(
                kospi_task, kosdaq_task, return_exceptions=True
            )
            
            # 예외 처리
            if isinstance(kospi_data, Exception):
                raise KISAPIError(f"KOSPI 데이터 조회 실패: {kospi_data}")
            if isinstance(kosdaq_data, Exception):
                raise KISAPIError(f"KOSDAQ 데이터 조회 실패: {kosdaq_data}")
            
            # 시장 상황 분류
            regime = self._classify_market_regime(kospi_data, kosdaq_data)
            
            # 리스크 매개변수 설정
            risk_params = self._get_risk_parameters(regime)
            
            # 신뢰도 점수 계산
            confidence = self._calculate_confidence_score(kospi_data, kosdaq_data, regime)
            
            # 분석 결과 생성
            result = MarketAnalysisResult(
                regime=regime,
                kospi_data=kospi_data,
                kosdaq_data=kosdaq_data,
                risk_parameters=risk_params,
                analysis_timestamp=analysis_start,
                confidence_score=confidence
            )
            
            # 데이터베이스에 저장 (요구사항 12.1)
            if save_to_db and self.db_manager:
                await self._save_to_database(result)
            
            # 캐시 업데이트
            self._update_cache(result)
            self._last_analysis_time = current_time
            
            analysis_duration = (datetime.now() - analysis_start).total_seconds()
            logger.info(
                f"시장 상황 분석 완료: {regime.value.upper()} "
                f"(신뢰도: {confidence:.1f}%, 소요시간: {analysis_duration:.3f}초)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"시장 상황 분석 오류: {e}")
            raise KISAPIError(f"시장 상황 분석 실패: {e}")
    
    def _classify_market_regime(self, kospi_data: IndexData, kosdaq_data: IndexData) -> MarketRegime:
        """
        시장 상황 분류 로직 (요구사항 1.2, 1.3, 1.4)
        
        Args:
            kospi_data: KOSPI 지수 데이터
            kosdaq_data: KOSDAQ 지수 데이터
            
        Returns:
            MarketRegime: 분류된 시장 상황
        """
        try:
            # 20일 이동평균 대비 현재 지수 위치 확인
            kospi_above_ma20 = kospi_data.current_price > kospi_data.ma20
            kosdaq_above_ma20 = kosdaq_data.current_price > kosdaq_data.ma20
            
            logger.debug(
                f"지수 위치 분석 - KOSPI: {kospi_data.current_price:.2f} "
                f"(MA20: {kospi_data.ma20:.2f}, 상위: {kospi_above_ma20}), "
                f"KOSDAQ: {kosdaq_data.current_price:.2f} "
                f"(MA20: {kosdaq_data.ma20:.2f}, 상위: {kosdaq_above_ma20})"
            )
            
            # 시장 상황 분류 규칙
            if kospi_above_ma20 and kosdaq_above_ma20:
                regime = MarketRegime.BULL
                logger.info("시장 상황: 강세장 (BULL) - 양 지수 모두 20일 이동평균 상위")
            elif not kospi_above_ma20 and not kosdaq_above_ma20:
                regime = MarketRegime.BEAR
                logger.info("시장 상황: 약세장 (BEAR) - 양 지수 모두 20일 이동평균 하위")
            else:
                regime = MarketRegime.NEUTRAL
                logger.info("시장 상황: 중립 (NEUTRAL) - 지수간 혼재 신호")
            
            return regime
            
        except Exception as e:
            logger.error(f"시장 상황 분류 오류: {e}")
            # 기본값으로 중립 반환
            return MarketRegime.NEUTRAL
    
    async def _save_to_database(self, result: MarketAnalysisResult) -> None:
        """
        분석 결과를 데이터베이스에 저장 (요구사항 12.1)
        
        Args:
            result: 시장 분석 결과
        """
        try:
            if not self.db_manager:
                logger.warning("데이터베이스 관리자가 설정되지 않아 저장을 건너뜁니다")
                return
            
            # 날짜 형식: YYYY-MM-DD (요구사항 12.4)
            analysis_date = result.analysis_timestamp.strftime('%Y-%m-%d')
            
            await self.db_manager.save_market_regime(
                regime=result.regime.value,
                kospi_value=result.kospi_data.current_price,
                kosdaq_value=result.kosdaq_data.current_price,
                kospi_ma20=result.kospi_data.ma20,
                kosdaq_ma20=result.kosdaq_data.ma20,
                take_profit_percent=result.risk_parameters.take_profit_percent,
                stop_loss_percent=result.risk_parameters.stop_loss_percent,
                analysis_date=analysis_date
            )
            
            logger.info(f"시장 체제 분석 결과 데이터베이스 저장 완료: {analysis_date}")
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            # 저장 실패해도 분석 결과는 반환되도록 예외를 다시 발생시키지 않음
    
    def _get_risk_parameters(self, regime: MarketRegime) -> RiskParameters:
        """
        시장 상황별 리스크 매개변수 설정
        
        Args:
            regime: 시장 상황
            
        Returns:
            RiskParameters: 리스크 매개변수
        """
        try:
            if regime == MarketRegime.BULL:
                # 강세장: 높은 수익 목표, 적당한 손실 제한
                take_profit = 5.0
                stop_loss = 3.0
                logger.debug("강세장 리스크 매개변수 적용: 수익실현 5%, 손절 3%")
                
            elif regime == MarketRegime.BEAR:
                # 약세장: 낮은 수익 목표, 엄격한 손실 제한
                take_profit = 2.0
                stop_loss = 2.0
                logger.debug("약세장 리스크 매개변수 적용: 수익실현 2%, 손절 2%")
                
            else:  # NEUTRAL
                # 중립: 기본 매개변수 사용
                take_profit = self.risk_config.default_take_profit
                stop_loss = self.risk_config.default_stop_loss
                logger.debug(f"중립 시장 기본 매개변수 적용: 수익실현 {take_profit}%, 손절 {stop_loss}%")
            
            return RiskParameters(
                take_profit_percent=take_profit,
                stop_loss_percent=stop_loss,
                regime=regime
            )
            
        except Exception as e:
            logger.error(f"리스크 매개변수 설정 오류: {e}")
            # 기본값 반환
            return RiskParameters(
                take_profit_percent=self.risk_config.default_take_profit,
                stop_loss_percent=self.risk_config.default_stop_loss,
                regime=regime
            )
    
    def _calculate_confidence_score(
        self, 
        kospi_data: IndexData, 
        kosdaq_data: IndexData, 
        regime: MarketRegime
    ) -> float:
        """
        분석 신뢰도 점수 계산
        
        Args:
            kospi_data: KOSPI 지수 데이터
            kosdaq_data: KOSDAQ 지수 데이터
            regime: 분류된 시장 상황
            
        Returns:
            float: 신뢰도 점수 (0-100)
        """
        try:
            confidence = 50.0  # 기본 신뢰도
            
            # 지수별 이동평균 대비 거리 계산
            kospi_distance = abs(kospi_data.current_price - kospi_data.ma20) / kospi_data.ma20 * 100
            kosdaq_distance = abs(kosdaq_data.current_price - kosdaq_data.ma20) / kosdaq_data.ma20 * 100
            
            # 거리가 클수록 신뢰도 증가 (명확한 신호)
            distance_factor = min((kospi_distance + kosdaq_distance) * 10, 30)
            confidence += distance_factor
            
            # 지수간 일치도 확인
            kospi_above = kospi_data.current_price > kospi_data.ma20
            kosdaq_above = kosdaq_data.current_price > kosdaq_data.ma20
            
            if regime == MarketRegime.BULL and kospi_above and kosdaq_above:
                confidence += 20  # 강세장에서 양 지수 모두 상위
            elif regime == MarketRegime.BEAR and not kospi_above and not kosdaq_above:
                confidence += 20  # 약세장에서 양 지수 모두 하위
            elif regime == MarketRegime.NEUTRAL:
                confidence -= 10  # 중립은 불확실성 증가
            
            # 변화율 일치도 확인
            if (kospi_data.change_rate > 0) == (kosdaq_data.change_rate > 0):
                confidence += 10  # 같은 방향 움직임
            else:
                confidence -= 5   # 반대 방향 움직임
            
            # 0-100 범위로 제한
            confidence = max(0, min(100, confidence))
            
            logger.debug(
                f"신뢰도 계산: KOSPI 거리 {kospi_distance:.2f}%, "
                f"KOSDAQ 거리 {kosdaq_distance:.2f}%, 최종 신뢰도 {confidence:.1f}%"
            )
            
            return confidence
            
        except Exception as e:
            logger.error(f"신뢰도 점수 계산 오류: {e}")
            return 50.0  # 기본값
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cache or not self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry
    
    def _update_cache(self, result: MarketAnalysisResult) -> None:
        """캐시 업데이트"""
        self._cache = result
        self._cache_expiry = datetime.now() + self._cache_duration
        logger.debug(f"시장 분석 결과 캐시 업데이트 (만료: {self._cache_expiry})")
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache = None
        self._cache_expiry = None
        logger.debug("시장 분석 캐시 초기화")
    
    async def get_current_regime(self, use_cache: bool = True) -> MarketRegime:
        """
        현재 시장 상황만 간단히 조회
        
        Args:
            use_cache: 캐시 사용 여부
            
        Returns:
            MarketRegime: 현재 시장 상황
        """
        try:
            result = await self.analyze_market_regime(use_cache)
            return result.regime
        except Exception as e:
            logger.error(f"시장 상황 조회 오류: {e}")
            return MarketRegime.NEUTRAL  # 기본값
    
    async def get_current_risk_parameters(self, use_cache: bool = True) -> RiskParameters:
        """
        현재 리스크 매개변수만 간단히 조회
        
        Args:
            use_cache: 캐시 사용 여부
            
        Returns:
            RiskParameters: 현재 리스크 매개변수
        """
        try:
            result = await self.analyze_market_regime(use_cache)
            return result.risk_parameters
        except Exception as e:
            logger.error(f"리스크 매개변수 조회 오류: {e}")
            # 기본값 반환
            return RiskParameters(
                take_profit_percent=self.risk_config.default_take_profit,
                stop_loss_percent=self.risk_config.default_stop_loss,
                regime=MarketRegime.NEUTRAL
            )
    
    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 정보"""
        return {
            'cached': self._cache is not None,
            'cache_expiry': self._cache_expiry.isoformat() if self._cache_expiry else None,
            'cache_valid': self._is_cache_valid(),
            'last_analysis_time': self._last_analysis_time,
            'min_analysis_interval': self._min_analysis_interval
        }
    
    def update_risk_config(self, new_config: RiskConfig) -> None:
        """리스크 설정 업데이트"""
        self.risk_config = new_config
        self.clear_cache()  # 설정 변경시 캐시 초기화
        logger.info("리스크 설정 업데이트 및 캐시 초기화")
    
    async def validate_analysis_performance(self) -> Dict[str, Any]:
        """
        분석 성능 검증 (요구사항 8.1 - 100ms 이하 응답시간)
        
        Returns:
            Dict[str, Any]: 성능 검증 결과
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 캐시 없이 분석 실행
            await self.analyze_market_regime(use_cache=False)
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # 밀리초 변환
            
            performance_ok = response_time < 100.0  # 100ms 기준
            
            result = {
                'response_time_ms': response_time,
                'performance_requirement_met': performance_ok,
                'requirement_threshold_ms': 100.0,
                'timestamp': datetime.now().isoformat()
            }
            
            if performance_ok:
                logger.info(f"성능 검증 통과: {response_time:.2f}ms")
            else:
                logger.warning(f"성능 검증 실패: {response_time:.2f}ms (기준: 100ms)")
            
            return result
            
        except Exception as e:
            logger.error(f"성능 검증 오류: {e}")
            return {
                'response_time_ms': 0,
                'performance_requirement_met': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }