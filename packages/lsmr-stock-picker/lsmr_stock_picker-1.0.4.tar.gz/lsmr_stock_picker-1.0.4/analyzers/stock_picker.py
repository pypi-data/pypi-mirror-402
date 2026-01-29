"""
종목 선정기 (Stock Picker)
평균회귀 로직을 사용하여 매수 후보 종목을 식별하는 컴포넌트
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

from models.data_models import LeadingSector, StockData, TradeAction
from kis_api.client import KISClient, KISAPIError
from config.settings import SystemConfig


logger = logging.getLogger(__name__)


@dataclass
class StockCandidate:
    """종목 후보 데이터 모델"""
    ticker: str
    stock_name: str
    sector: str
    z_score: float
    disparity_ratio: float
    current_price: float
    ma20: float
    volume: int
    signal_strength: float  # 0-100
    analysis_date: str
    
    # 추가 상세 정보
    std_dev20: Optional[float] = None
    volume_trend: Optional[str] = None
    action: Optional[TradeAction] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            'ticker': self.ticker,
            'stock_name': self.stock_name,
            'sector': self.sector,
            'z_score': self.z_score,
            'disparity_ratio': self.disparity_ratio,
            'current_price': self.current_price,
            'ma20': self.ma20,
            'volume': self.volume,
            'signal_strength': self.signal_strength,
            'analysis_date': self.analysis_date,
            'std_dev20': self.std_dev20,
            'volume_trend': self.volume_trend
        }
        if self.action:
            result['action'] = self.action.value
        return result


class StockPicker:
    """
    종목 선정기 - 평균회귀 로직을 사용한 매수 후보 식별
    
    요구사항:
    - 3.1: 주도 섹터에서 거래량 상위 5개 종목 조회
    - 3.2: 20일 이동평균과 표준편차를 사용한 Z-Score 계산
    - 3.3: Z-Score -2.0 이하 종목을 매수 후보로 등록
    - 3.4: 이격도 계산 공식: (현재가 - MA20) / MA20 * 100
    - 3.5: 이격도 92% 이하 시 최종 매수 신호 생성
    - 3.6: 거래량 추세 확인 (가격 하락 중 거래량 감소 및 반전 징후)
    - 12.3: 결과를 데이터베이스에 저장
    """
    
    def __init__(
        self,
        kis_client: KISClient,
        db_manager=None,
        config: Optional[SystemConfig] = None
    ):
        """
        초기화
        
        Args:
            kis_client: KIS API 클라이언트
            db_manager: 데이터베이스 관리자 (선택사항)
            config: 시스템 설정 (선택사항)
        """
        self.kis_client = kis_client
        self.db_manager = db_manager
        self.config = config
        
        # 분석 파라미터
        self._z_score_threshold = -2.0  # Z-Score 임계값 (요구사항 3.3)
        self._disparity_threshold = 92.0  # 이격도 임계값 (요구사항 3.5)
        self._ma_period = 20  # 이동평균 기간
        self._top_stocks_per_sector = 5  # 섹터당 상위 종목 수 (요구사항 3.1)
        
        # 캐시 설정
        self._cache: Dict[str, List[StockCandidate]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=30)  # 30분 캐시
        
        logger.info("Stock Picker 초기화 완료")
    
    async def analyze_sector_stocks(
        self,
        sector: LeadingSector,
        use_cache: bool = True,
        save_to_db: bool = True
    ) -> List[StockCandidate]:
        """
        섹터 내 종목 분석 및 매수 후보 식별
        
        Args:
            sector: 주도 섹터 정보
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            List[StockCandidate]: 매수 후보 종목 리스트
            
        Raises:
            KISAPIError: API 호출 실패시
        """
        try:
            # 캐시 확인
            cache_key = f"{sector.sector_code}_{datetime.now().strftime('%Y%m%d')}"
            if use_cache and self._is_cache_valid(cache_key):
                logger.debug(f"캐시된 종목 분석 결과 반환: {sector.sector_name}")
                return self._cache[cache_key]
            
            logger.info(f"섹터 {sector.sector_name} 종목 분석 시작")
            analysis_start = datetime.now()
            
            # 1. 거래량 상위 종목 조회 (요구사항 3.1)
            top_stocks = await self._get_top_volume_stocks(
                sector.sector_code,
                limit=self._top_stocks_per_sector
            )
            
            if not top_stocks:
                logger.warning(f"섹터 {sector.sector_name}에서 종목을 찾을 수 없습니다")
                return []
            
            logger.debug(
                f"섹터 {sector.sector_name}에서 거래량 상위 {len(top_stocks)}개 종목 조회 완료"
            )
            
            # 2. 각 종목 분석 (병렬 처리)
            analysis_tasks = []
            for stock in top_stocks:
                task = self._analyze_single_stock(stock, sector.sector_name)
                analysis_tasks.append(task)
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 3. 유효한 매수 후보만 필터링
            candidates = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"종목 {top_stocks[i].ticker} 분석 실패: {result}")
                elif result is not None:
                    candidates.append(result)
            
            # 4. 신호 강도로 정렬
            candidates.sort(key=lambda x: x.signal_strength, reverse=True)
            
            # 5. 데이터베이스에 저장 (요구사항 12.3)
            if save_to_db and self.db_manager and candidates:
                await self._save_to_database(candidates)
            
            # 6. 캐시 업데이트
            self._update_cache(cache_key, candidates)
            
            analysis_duration = (datetime.now() - analysis_start).total_seconds()
            logger.info(
                f"섹터 {sector.sector_name} 종목 분석 완료: "
                f"{len(candidates)}개 매수 후보 식별 "
                f"(소요시간: {analysis_duration:.3f}초)"
            )
            
            return candidates
            
        except Exception as e:
            logger.error(f"섹터 종목 분석 오류: {e}")
            raise KISAPIError(f"종목 분석 실패: {e}")
    
    async def _get_top_volume_stocks(
        self,
        sector_code: str,
        limit: int = 5
    ) -> List[StockData]:
        """
        섹터 내 거래량 상위 종목 조회 (요구사항 3.1)
        
        Args:
            sector_code: 섹터 코드
            limit: 조회할 종목 수
            
        Returns:
            List[StockData]: 거래량 상위 종목 리스트
        """
        try:
            # KIS API를 통해 섹터 내 종목 조회 (거래량순)
            stocks = await self.kis_client.get_sector_stocks(
                sector_code,
                limit=limit,
                sort_by='volume'
            )
            
            logger.debug(
                f"섹터 {sector_code}에서 거래량 상위 {len(stocks)}개 종목 조회: " +
                ", ".join([f"{s.ticker}({s.volume:,})" for s in stocks[:3]])
            )
            
            return stocks
            
        except Exception as e:
            logger.error(f"섹터 {sector_code} 종목 조회 오류: {e}")
            raise
    
    async def _analyze_single_stock(
        self,
        stock: StockData,
        sector_name: str
    ) -> Optional[StockCandidate]:
        """
        개별 종목 분석
        
        Args:
            stock: 종목 데이터
            sector_name: 섹터 이름
            
        Returns:
            Optional[StockCandidate]: 매수 후보 (조건 미충족시 None)
        """
        try:
            logger.debug(f"종목 분석 시작: {stock.stock_name} ({stock.ticker})")
            
            # 1. 과거 가격 데이터 조회 (20일)
            historical_data = await self.kis_client.get_historical_data(
                stock.ticker,
                days=self._ma_period
            )
            
            if len(historical_data) < self._ma_period:
                logger.warning(
                    f"종목 {stock.ticker}: 충분한 과거 데이터 없음 "
                    f"({len(historical_data)}/{self._ma_period}일)"
                )
                return None
            
            # 2. Z-Score 계산 (요구사항 3.2)
            z_score, ma20, std_dev20 = self.calculate_z_score(
                stock.current_price,
                historical_data
            )
            
            # 3. Z-Score 임계값 확인 (요구사항 3.3)
            if z_score > self._z_score_threshold:
                logger.debug(
                    f"종목 {stock.ticker}: Z-Score {z_score:.2f} > "
                    f"임계값 {self._z_score_threshold} (매수 후보 제외)"
                )
                return None
            
            # 4. 이격도 계산 (요구사항 3.4)
            disparity_ratio = self.calculate_disparity(stock.current_price, ma20)
            
            # 5. 거래량 추세 분석 (요구사항 3.6)
            volume_trend = await self._analyze_volume_trend(stock.ticker, historical_data)
            
            # 6. 매수 신호 생성 (요구사항 3.5)
            action, signal_strength = self._generate_buy_signal(
                z_score,
                disparity_ratio,
                volume_trend
            )
            
            # 7. 분석 날짜 (YYYY-MM-DD 형식, 요구사항 12.4)
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            # 8. 매수 후보 생성
            candidate = StockCandidate(
                ticker=stock.ticker,
                stock_name=stock.stock_name,
                sector=sector_name,
                z_score=z_score,
                disparity_ratio=disparity_ratio,
                current_price=stock.current_price,
                ma20=ma20,
                volume=stock.volume,
                signal_strength=signal_strength,
                analysis_date=analysis_date,
                std_dev20=std_dev20,
                volume_trend=volume_trend,
                action=action
            )
            
            logger.info(
                f"매수 후보 식별: {stock.stock_name} ({stock.ticker}) - "
                f"Z-Score: {z_score:.2f}, 이격도: {disparity_ratio:.2f}%, "
                f"신호강도: {signal_strength:.1f}, 액션: {action.value}"
            )
            
            return candidate
            
        except Exception as e:
            logger.error(f"종목 {stock.ticker} 분석 오류: {e}")
            return None
    
    def calculate_z_score(
        self,
        current_price: float,
        historical_data: List[Dict[str, Any]]
    ) -> Tuple[float, float, float]:
        """
        Z-Score 계산 (요구사항 3.2)
        
        공식: (현재가 - MA20) / StdDev20
        
        Args:
            current_price: 현재가
            historical_data: 과거 가격 데이터 (최소 20일)
            
        Returns:
            Tuple[float, float, float]: (Z-Score, MA20, StdDev20)
        """
        try:
            # 종가 추출
            prices = [data['close'] for data in historical_data[-self._ma_period:]]
            
            # 20일 이동평균 계산
            ma20 = float(statistics.mean(prices))
            
            # 20일 표준편차 계산
            std_dev20 = float(statistics.stdev(prices)) if len(prices) > 1 else 0.0
            
            # Z-Score 계산
            if std_dev20 > 0:
                z_score = float((current_price - ma20) / std_dev20)
            else:
                z_score = 0.0
            
            logger.debug(
                f"Z-Score 계산: 현재가 {current_price:.0f}, "
                f"MA20 {ma20:.0f}, StdDev {std_dev20:.2f}, "
                f"Z-Score {z_score:.2f}"
            )
            
            return round(z_score, 4), round(ma20, 2), round(std_dev20, 2)
            
        except Exception as e:
            logger.error(f"Z-Score 계산 오류: {e}")
            return 0.0, 0.0, 0.0
    
    def calculate_disparity(
        self,
        current_price: float,
        ma20: float
    ) -> float:
        """
        이격도 계산 (요구사항 3.4)
        
        공식: (현재가 - MA20) / MA20 * 100
        
        Args:
            current_price: 현재가
            ma20: 20일 이동평균
            
        Returns:
            float: 이격도 (%)
        """
        try:
            if ma20 <= 0:
                logger.warning(f"유효하지 않은 MA20 값: {ma20}")
                return 100.0
            
            # 이격도 계산
            disparity = ((current_price - ma20) / ma20) * 100
            
            logger.debug(
                f"이격도 계산: 현재가 {current_price:.0f}, "
                f"MA20 {ma20:.0f}, 이격도 {disparity:.2f}%"
            )
            
            return round(disparity, 4)
            
        except Exception as e:
            logger.error(f"이격도 계산 오류: {e}")
            return 100.0
    
    async def _analyze_volume_trend(
        self,
        ticker: str,
        historical_data: List[Dict[str, Any]]
    ) -> str:
        """
        거래량 추세 분석 (요구사항 3.6)
        
        가격 하락 중 거래량 감소 및 반전 징후 확인
        
        Args:
            ticker: 종목 티커
            historical_data: 과거 데이터
            
        Returns:
            str: 거래량 추세 ("increasing", "decreasing", "stable")
        """
        try:
            if len(historical_data) < 5:
                return "stable"
            
            # 최근 5일 데이터
            recent_data = historical_data[-5:]
            
            # 가격 추세 확인
            prices = [data['close'] for data in recent_data]
            price_declining = prices[-1] < prices[0]
            
            # 거래량 추세 확인
            volumes = [data['volume'] for data in recent_data]
            volume_avg_early = statistics.mean(volumes[:3])
            volume_avg_late = statistics.mean(volumes[-3:])
            
            # 거래량 변화율
            volume_change = ((volume_avg_late - volume_avg_early) / volume_avg_early) * 100
            
            # 추세 판정
            if price_declining and volume_change < -10:
                # 가격 하락 중 거래량 감소 (긍정적 신호)
                trend = "decreasing"
                logger.debug(
                    f"종목 {ticker}: 가격 하락 중 거래량 감소 감지 "
                    f"(거래량 변화: {volume_change:.1f}%)"
                )
            elif volume_change > 20:
                # 거래량 급증 (반전 징후)
                trend = "increasing"
                logger.debug(
                    f"종목 {ticker}: 거래량 급증 감지 "
                    f"(거래량 변화: {volume_change:.1f}%)"
                )
            else:
                trend = "stable"
            
            return trend
            
        except Exception as e:
            logger.error(f"거래량 추세 분석 오류: {e}")
            return "stable"
    
    def _generate_buy_signal(
        self,
        z_score: float,
        disparity_ratio: float,
        volume_trend: str
    ) -> Tuple[TradeAction, float]:
        """
        매수 신호 생성 (요구사항 3.5)
        
        Args:
            z_score: Z-Score
            disparity_ratio: 이격도 (%)
            volume_trend: 거래량 추세
            
        Returns:
            Tuple[TradeAction, float]: (거래 액션, 신호 강도 0-100)
        """
        try:
            signal_strength = 0.0
            action = TradeAction.HOLD
            
            # 1. Z-Score 기반 점수 (최대 40점)
            if z_score <= -2.5:
                signal_strength += 40
            elif z_score <= -2.0:
                signal_strength += 30
            elif z_score <= -1.5:
                signal_strength += 20
            
            # 2. 이격도 기반 점수 (최대 40점)
            # 이격도 92% 이하가 최종 매수 신호 (요구사항 3.5)
            # 이격도 = (현재가 - MA20) / MA20 * 100
            # 88% = -12%, 90% = -10%, 92% = -8%, 94% = -6%
            if disparity_ratio <= -12:  # 88% 이하
                signal_strength += 40
            elif disparity_ratio <= -10:  # 90% 이하
                signal_strength += 35
            elif disparity_ratio <= -8:  # 92% 이하
                signal_strength += 30
            elif disparity_ratio <= -6:  # 94% 이하
                signal_strength += 20
            
            # 3. 거래량 추세 기반 점수 (최대 20점)
            if volume_trend == "decreasing":
                # 가격 하락 중 거래량 감소 (긍정적)
                signal_strength += 20
            elif volume_trend == "increasing":
                # 거래량 증가 (반전 징후)
                signal_strength += 15
            else:
                signal_strength += 5
            
            # 4. 최종 매수 신호 판정
            # 이격도 92% 이하이고 신호 강도가 60 이상이면 매수
            # 이격도 92% = -8%, 따라서 disparity_ratio <= -8이어야 함
            disparity_threshold_value = -(100 - self._disparity_threshold)  # 92 -> -8
            if disparity_ratio <= disparity_threshold_value and signal_strength >= 60:
                action = TradeAction.BUY
                logger.debug(
                    f"매수 신호 생성: Z-Score {z_score:.2f}, "
                    f"이격도 {disparity_ratio:.2f}%, "
                    f"신호강도 {signal_strength:.1f}"
                )
            else:
                action = TradeAction.HOLD
                logger.debug(
                    f"매수 보류: Z-Score {z_score:.2f}, "
                    f"이격도 {disparity_ratio:.2f}%, "
                    f"신호강도 {signal_strength:.1f}"
                )
            
            return action, round(signal_strength, 2)
            
        except Exception as e:
            logger.error(f"매수 신호 생성 오류: {e}")
            return TradeAction.HOLD, 0.0
    
    async def _save_to_database(
        self,
        candidates: List[StockCandidate]
    ) -> None:
        """
        분석 결과를 데이터베이스에 저장 (요구사항 12.3)
        
        Args:
            candidates: 종목 후보 리스트
        """
        try:
            if not self.db_manager:
                logger.warning("데이터베이스 관리자가 설정되지 않아 저장을 건너뜁니다")
                return
            
            # 각 종목 후보 저장
            for candidate in candidates:
                await self.db_manager.save_stock_candidate(
                    ticker=candidate.ticker,
                    stock_name=candidate.stock_name,
                    sector=candidate.sector,
                    z_score=candidate.z_score,
                    disparity_ratio=candidate.disparity_ratio,
                    current_price=candidate.current_price,
                    ma20=candidate.ma20,
                    volume=candidate.volume,
                    signal_strength=candidate.signal_strength,
                    analysis_date=candidate.analysis_date
                )
            
            logger.info(f"종목 후보 {len(candidates)}개 데이터베이스 저장 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            # 저장 실패해도 분석 결과는 반환되도록 예외를 다시 발생시키지 않음
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 확인"""
        if cache_key not in self._cache or cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _update_cache(
        self,
        cache_key: str,
        candidates: List[StockCandidate]
    ) -> None:
        """캐시 업데이트"""
        self._cache[cache_key] = candidates
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
        logger.debug(f"종목 분석 결과 캐시 업데이트: {cache_key}")
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache.clear()
        self._cache_expiry.clear()
        logger.debug("종목 분석 캐시 초기화")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 정보"""
        return {
            'cached_sectors': len(self._cache),
            'cache_keys': list(self._cache.keys()),
            'total_candidates': sum(len(c) for c in self._cache.values())
        }
    
    def update_thresholds(
        self,
        z_score: Optional[float] = None,
        disparity: Optional[float] = None
    ) -> None:
        """
        분석 임계값 업데이트
        
        Args:
            z_score: Z-Score 임계값
            disparity: 이격도 임계값
        """
        if z_score is not None:
            self._z_score_threshold = z_score
        if disparity is not None:
            self._disparity_threshold = disparity
        
        self.clear_cache()  # 임계값 변경시 캐시 초기화
        logger.info("종목 분석 임계값 업데이트 및 캐시 초기화")
