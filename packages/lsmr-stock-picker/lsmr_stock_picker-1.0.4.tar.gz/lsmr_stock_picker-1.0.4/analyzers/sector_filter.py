"""
섹터 필터 (Sector Filter)
4-way 분석을 사용하여 주도 섹터를 식별하는 컴포넌트
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from models.data_models import LeadingSector
from kis_api.client import KISClient, KISAPIError
from config.settings import SystemConfig


logger = logging.getLogger(__name__)


@dataclass
class SectorAnalysisResult:
    """섹터 분석 결과"""
    sector_code: str
    sector_name: str
    price_momentum_score: float  # 0-100
    supply_demand_score: float   # 0-100
    breadth_score: float         # 0-100
    relative_strength_score: float  # 0-100
    combined_score: float        # 0-100
    rank: int
    analysis_date: str
    
    # 상세 정보
    is_leading: bool = False
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    foreign_net_buy_days: int = 0
    institution_net_buy_days: int = 0
    advancing_stocks: int = 0
    declining_stocks: int = 0
    market_relative_return: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'sector_code': self.sector_code,
            'sector_name': self.sector_name,
            'price_momentum_score': self.price_momentum_score,
            'supply_demand_score': self.supply_demand_score,
            'breadth_score': self.breadth_score,
            'relative_strength_score': self.relative_strength_score,
            'combined_score': self.combined_score,
            'rank': self.rank,
            'analysis_date': self.analysis_date,
            'is_leading': self.is_leading,
            'ma5': self.ma5,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'foreign_net_buy_days': self.foreign_net_buy_days,
            'institution_net_buy_days': self.institution_net_buy_days,
            'advancing_stocks': self.advancing_stocks,
            'declining_stocks': self.declining_stocks,
            'market_relative_return': self.market_relative_return
        }


class SectorFilter:
    """
    섹터 필터 - 4-way 분석을 사용한 주도 섹터 식별
    
    요구사항:
    - 2.1: 4-way 분석을 사용하여 모든 가용 섹터 평가
    - 2.2: 가격 모멘텀 평가 (5/20/60일 상승 순서)
    - 2.3: 수급 분석 (외국인 + 기관 순매수 3일)
    - 2.4: 확산 분석 (상승 대 하락 종목 비율 3:1)
    - 2.5: 상대강도 순위 (시장 대비 상위 20%)
    - 2.6: 주도 섹터 분류 (4가지 기준 모두 충족)
    - 2.7: 상위 3개 섹터 선정
    - 12.2: 결과를 데이터베이스에 저장
    """
    
    # 섹터 코드 매핑 (KIS API 섹터 코드)
    SECTOR_CODES = {
        'G25': '음식료품',
        'G35': '섬유의복',
        'G50': '종이목재',
        'G40': '화학',
        'G45': '의약품',
        'G55': '비금속광물',
        'G60': '철강금속',
        'G70': '기계',
        'G80': '전기전자',
        'G85': '의료정밀',
        'G90': '운수장비',
        'G20': '유통업',
        'G15': '전기가스업',
        'G30': '건설업',
        'G65': '운수창고업',
        'G75': '통신업',
        'G95': '서비스업',
        'G10': '금융업',
    }
    
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
        self.config = config  # SystemConfig는 선택사항으로 처리
        
        # 캐시 설정
        self._cache: Optional[List[SectorAnalysisResult]] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)  # 1시간 캐시
        
        # 분석 임계값
        self._price_momentum_threshold = 70.0  # 가격 모멘텀 점수 임계값
        self._supply_demand_threshold = 70.0   # 수급 점수 임계값
        self._breadth_threshold = 70.0         # 확산 점수 임계값
        self._relative_strength_threshold = 80.0  # 상대강도 점수 임계값 (상위 20%)
        
        logger.info("Sector Filter 초기화 완료")
    
    async def analyze_all_sectors(
        self,
        use_cache: bool = True,
        save_to_db: bool = True
    ) -> List[SectorAnalysisResult]:
        """
        모든 섹터 분석 실행 (요구사항 2.1)
        
        Args:
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            List[SectorAnalysisResult]: 섹터 분석 결과 리스트 (점수순 정렬)
            
        Raises:
            KISAPIError: API 호출 실패시
        """
        try:
            # 캐시 확인
            if use_cache and self._is_cache_valid():
                logger.debug("캐시된 섹터 분석 결과 반환")
                return self._cache
            
            logger.info(f"섹터 분석 시작 (총 {len(self.SECTOR_CODES)}개 섹터)")
            analysis_start = datetime.now()
            
            # 모든 섹터 병렬 분석
            sector_tasks = []
            for sector_code, sector_name in self.SECTOR_CODES.items():
                task = self._analyze_single_sector(sector_code, sector_name)
                sector_tasks.append(task)
            
            # 병렬 실행
            results = await asyncio.gather(*sector_tasks, return_exceptions=True)
            
            # 성공한 결과만 필터링
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    sector_code = list(self.SECTOR_CODES.keys())[i]
                    logger.warning(f"섹터 {sector_code} 분석 실패: {result}")
                else:
                    valid_results.append(result)
            
            if not valid_results:
                raise KISAPIError("모든 섹터 분석 실패")
            
            # 종합 점수로 정렬
            valid_results.sort(key=lambda x: x.combined_score, reverse=True)
            
            # 순위 부여
            for rank, result in enumerate(valid_results, start=1):
                result.rank = rank
                
                # 주도 섹터 판정 (요구사항 2.6)
                result.is_leading = self._is_leading_sector(result)
            
            # 데이터베이스에 저장 (요구사항 12.2)
            if save_to_db and self.db_manager:
                await self._save_to_database(valid_results)
            
            # 캐시 업데이트
            self._update_cache(valid_results)
            
            analysis_duration = (datetime.now() - analysis_start).total_seconds()
            leading_count = sum(1 for r in valid_results if r.is_leading)
            
            logger.info(
                f"섹터 분석 완료: {len(valid_results)}개 섹터 분석, "
                f"{leading_count}개 주도 섹터 식별 "
                f"(소요시간: {analysis_duration:.3f}초)"
            )
            
            return valid_results
            
        except Exception as e:
            logger.error(f"섹터 분석 오류: {e}")
            raise KISAPIError(f"섹터 분석 실패: {e}")
    
    async def _analyze_single_sector(
        self,
        sector_code: str,
        sector_name: str
    ) -> SectorAnalysisResult:
        """
        개별 섹터 분석
        
        Args:
            sector_code: 섹터 코드
            sector_name: 섹터 이름
            
        Returns:
            SectorAnalysisResult: 섹터 분석 결과
        """
        try:
            logger.debug(f"섹터 분석 시작: {sector_name} ({sector_code})")
            
            # 섹터 데이터 조회
            sector_data = await self.kis_client.get_sector_data(sector_code)
            
            # 4-way 분석 수행
            price_score, price_details = await self._evaluate_price_momentum(sector_data)
            supply_score, supply_details = await self._evaluate_supply_demand(sector_data)
            breadth_score, breadth_details = await self._evaluate_breadth(sector_data)
            strength_score, strength_details = await self._evaluate_relative_strength(sector_data)
            
            # 종합 점수 계산 (가중 평균)
            combined_score = self._calculate_combined_score(
                price_score, supply_score, breadth_score, strength_score
            )
            
            # 분석 날짜 (YYYY-MM-DD 형식, 요구사항 12.4)
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            result = SectorAnalysisResult(
                sector_code=sector_code,
                sector_name=sector_name,
                price_momentum_score=price_score,
                supply_demand_score=supply_score,
                breadth_score=breadth_score,
                relative_strength_score=strength_score,
                combined_score=combined_score,
                rank=0,  # 나중에 설정
                analysis_date=analysis_date,
                **price_details,
                **supply_details,
                **breadth_details,
                **strength_details
            )
            
            logger.debug(
                f"섹터 {sector_name} 분석 완료: "
                f"종합점수 {combined_score:.1f} "
                f"(가격 {price_score:.1f}, 수급 {supply_score:.1f}, "
                f"확산 {breadth_score:.1f}, 상대강도 {strength_score:.1f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"섹터 {sector_name} 분석 오류: {e}")
            raise
    
    async def _evaluate_price_momentum(
        self,
        sector_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        가격 모멘텀 평가 (요구사항 2.2)
        
        5/20/60일 이동평균 상승 순서 확인 및 신고점 여부 확인
        
        Args:
            sector_data: 섹터 데이터
            
        Returns:
            Tuple[float, Dict]: (점수 0-100, 상세 정보)
        """
        try:
            score = 0.0
            details = {}
            
            # 이동평균 데이터 추출
            ma5 = sector_data.get('ma5', 0)
            ma20 = sector_data.get('ma20', 0)
            ma60 = sector_data.get('ma60', 0)
            current_price = sector_data.get('current_price', 0)
            high_52week = sector_data.get('high_52week', 0)
            
            details['ma5'] = ma5
            details['ma20'] = ma20
            details['ma60'] = ma60
            
            # 5/20/60일 상승 순서 확인 (각 25점)
            if ma5 > ma20:
                score += 25
            if ma20 > ma60:
                score += 25
            if ma5 > ma60:
                score += 25
            
            # 신고점 근처 확인 (25점)
            if high_52week > 0 and current_price >= high_52week * 0.95:  # 52주 고점의 95% 이상
                score += 25
            
            logger.debug(
                f"가격 모멘텀 평가: 점수 {score:.1f} "
                f"(MA5: {ma5:.2f}, MA20: {ma20:.2f}, MA60: {ma60:.2f})"
            )
            
            return score, details
            
        except Exception as e:
            logger.error(f"가격 모멘텀 평가 오류: {e}")
            return 0.0, {}
    
    async def _evaluate_supply_demand(
        self,
        sector_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        수급 분석 (요구사항 2.3)
        
        외국인 및 기관투자자 3거래일 연속 순매수 확인
        
        Args:
            sector_data: 섹터 데이터
            
        Returns:
            Tuple[float, Dict]: (점수 0-100, 상세 정보)
        """
        try:
            score = 0.0
            details = {}
            
            # 외국인/기관 순매수 데이터 (최근 3일)
            foreign_net_buy = sector_data.get('foreign_net_buy_days', [])
            institution_net_buy = sector_data.get('institution_net_buy_days', [])
            
            # 3거래일 연속 순매수 확인
            foreign_consecutive = self._count_consecutive_positive(foreign_net_buy)
            institution_consecutive = self._count_consecutive_positive(institution_net_buy)
            
            details['foreign_net_buy_days'] = foreign_consecutive
            details['institution_net_buy_days'] = institution_consecutive
            
            # 외국인 3일 연속 순매수 (50점)
            if foreign_consecutive >= 3:
                score += 50
            elif foreign_consecutive == 2:
                score += 30
            elif foreign_consecutive == 1:
                score += 10
            
            # 기관 3일 연속 순매수 (50점)
            if institution_consecutive >= 3:
                score += 50
            elif institution_consecutive == 2:
                score += 30
            elif institution_consecutive == 1:
                score += 10
            
            logger.debug(
                f"수급 분석: 점수 {score:.1f} "
                f"(외국인 {foreign_consecutive}일, 기관 {institution_consecutive}일 연속 순매수)"
            )
            
            return score, details
            
        except Exception as e:
            logger.error(f"수급 분석 오류: {e}")
            return 0.0, {}
    
    async def _evaluate_breadth(
        self,
        sector_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        확산 분석 (요구사항 2.4)
        
        섹터 내 상승 대 하락 종목 비율 확인 (3:1 기준)
        
        Args:
            sector_data: 섹터 데이터
            
        Returns:
            Tuple[float, Dict]: (점수 0-100, 상세 정보)
        """
        try:
            score = 0.0
            details = {}
            
            # 상승/하락 종목 수
            advancing = sector_data.get('advancing_stocks', 0)
            declining = sector_data.get('declining_stocks', 0)
            
            details['advancing_stocks'] = advancing
            details['declining_stocks'] = declining
            
            # 비율 계산
            if declining > 0:
                ratio = advancing / declining
                
                # 3:1 이상 (100점)
                if ratio >= 3.0:
                    score = 100
                # 2:1 이상 (70점)
                elif ratio >= 2.0:
                    score = 70
                # 1.5:1 이상 (50점)
                elif ratio >= 1.5:
                    score = 50
                # 1:1 이상 (30점)
                elif ratio >= 1.0:
                    score = 30
                else:
                    score = 0
            elif advancing > 0:
                # 하락 종목이 없으면 만점
                score = 100
            
            logger.debug(
                f"확산 분석: 점수 {score:.1f} "
                f"(상승 {advancing}개, 하락 {declining}개, 비율 {advancing/max(declining, 1):.2f}:1)"
            )
            
            return score, details
            
        except Exception as e:
            logger.error(f"확산 분석 오류: {e}")
            return 0.0, {}
    
    async def _evaluate_relative_strength(
        self,
        sector_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        상대강도 순위 (요구사항 2.5)
        
        시장 지수 대비 섹터 수익률 상위 20% 확인
        
        Args:
            sector_data: 섹터 데이터
            
        Returns:
            Tuple[float, Dict]: (점수 0-100, 상세 정보)
        """
        try:
            score = 0.0
            details = {}
            
            # 시장 대비 상대 수익률
            sector_return = sector_data.get('return_rate', 0)
            market_return = sector_data.get('market_return', 0)
            relative_return = sector_return - market_return
            
            details['market_relative_return'] = relative_return
            
            # 상대 수익률 기반 점수 계산
            # 상위 20% 기준: 시장 대비 +2% 이상
            if relative_return >= 2.0:
                score = 100  # 상위 20%
            elif relative_return >= 1.0:
                score = 80   # 상위 40%
            elif relative_return >= 0:
                score = 60   # 시장 수익률 이상
            elif relative_return >= -1.0:
                score = 40   # 시장 대비 소폭 하락
            else:
                score = 20   # 시장 대비 큰 폭 하락
            
            logger.debug(
                f"상대강도 분석: 점수 {score:.1f} "
                f"(섹터 수익률 {sector_return:.2f}%, 시장 대비 {relative_return:+.2f}%)"
            )
            
            return score, details
            
        except Exception as e:
            logger.error(f"상대강도 분석 오류: {e}")
            return 0.0, {}
    
    def _calculate_combined_score(
        self,
        price_score: float,
        supply_score: float,
        breadth_score: float,
        strength_score: float
    ) -> float:
        """
        종합 점수 계산 (가중 평균)
        
        Args:
            price_score: 가격 모멘텀 점수
            supply_score: 수급 점수
            breadth_score: 확산 점수
            strength_score: 상대강도 점수
            
        Returns:
            float: 종합 점수 (0-100)
        """
        # 가중치 설정 (합계 1.0)
        weights = {
            'price': 0.25,      # 가격 모멘텀 25%
            'supply': 0.25,     # 수급 25%
            'breadth': 0.25,    # 확산 25%
            'strength': 0.25    # 상대강도 25%
        }
        
        combined = (
            price_score * weights['price'] +
            supply_score * weights['supply'] +
            breadth_score * weights['breadth'] +
            strength_score * weights['strength']
        )
        
        return round(combined, 2)
    
    def _is_leading_sector(self, result: SectorAnalysisResult) -> bool:
        """
        주도 섹터 판정 (요구사항 2.6)
        
        4가지 기준 모두 임계값 이상이어야 주도 섹터로 분류
        
        Args:
            result: 섹터 분석 결과
            
        Returns:
            bool: 주도 섹터 여부
        """
        is_leading = (
            result.price_momentum_score >= self._price_momentum_threshold and
            result.supply_demand_score >= self._supply_demand_threshold and
            result.breadth_score >= self._breadth_threshold and
            result.relative_strength_score >= self._relative_strength_threshold
        )
        
        if is_leading:
            logger.info(f"주도 섹터 식별: {result.sector_name} (종합점수: {result.combined_score:.1f})")
        
        return is_leading
    
    def _count_consecutive_positive(self, values: List[float]) -> int:
        """
        연속 양수 일수 계산
        
        Args:
            values: 값 리스트 (최신순)
            
        Returns:
            int: 연속 양수 일수
        """
        count = 0
        for value in values:
            if value > 0:
                count += 1
            else:
                break
        return count
    
    async def get_leading_sectors(
        self,
        count: int = 3,
        use_cache: bool = True
    ) -> List[LeadingSector]:
        """
        상위 주도 섹터 조회 (요구사항 2.7)
        
        Args:
            count: 반환할 섹터 수 (기본 3개)
            use_cache: 캐시 사용 여부
            
        Returns:
            List[LeadingSector]: 상위 주도 섹터 리스트
        """
        try:
            # 전체 섹터 분석
            all_sectors = await self.analyze_all_sectors(use_cache=use_cache)
            
            # 상위 N개 선정
            top_sectors = all_sectors[:count]
            
            # LeadingSector 객체로 변환
            leading_sectors = []
            for sector in top_sectors:
                # 섹터 내 상위 종목 조회 (추후 구현)
                top_stocks = await self._get_top_stocks_in_sector(sector.sector_code)
                
                leading = LeadingSector(
                    sector_code=sector.sector_code,
                    sector_name=sector.sector_name,
                    combined_score=sector.combined_score,
                    top_stocks=top_stocks
                )
                leading_sectors.append(leading)
            
            logger.info(
                f"상위 {count}개 주도 섹터 선정: " +
                ", ".join([f"{s.sector_name}({s.combined_score:.1f})" for s in leading_sectors])
            )
            
            return leading_sectors
            
        except Exception as e:
            logger.error(f"주도 섹터 조회 오류: {e}")
            return []
    
    async def _get_top_stocks_in_sector(
        self,
        sector_code: str,
        limit: int = 5
    ) -> List[str]:
        """
        섹터 내 상위 종목 조회
        
        Args:
            sector_code: 섹터 코드
            limit: 조회할 종목 수
            
        Returns:
            List[str]: 종목 티커 리스트
        """
        try:
            # KIS API를 통해 섹터 내 종목 조회
            stocks = await self.kis_client.get_sector_stocks(sector_code, limit=limit)
            return [stock.ticker for stock in stocks]
            
        except Exception as e:
            logger.warning(f"섹터 {sector_code} 내 종목 조회 실패: {e}")
            return []
    
    async def _save_to_database(
        self,
        results: List[SectorAnalysisResult]
    ) -> None:
        """
        분석 결과를 데이터베이스에 저장 (요구사항 12.2)
        
        Args:
            results: 섹터 분석 결과 리스트
        """
        try:
            if not self.db_manager:
                logger.warning("데이터베이스 관리자가 설정되지 않아 저장을 건너뜁니다")
                return
            
            # 각 섹터 결과 저장
            for result in results:
                await self.db_manager.save_sector_analysis(
                    sector_code=result.sector_code,
                    sector_name=result.sector_name,
                    price_momentum_score=result.price_momentum_score,
                    supply_demand_score=result.supply_demand_score,
                    breadth_score=result.breadth_score,
                    relative_strength_score=result.relative_strength_score,
                    combined_score=result.combined_score,
                    rank=result.rank,
                    analysis_date=result.analysis_date
                )
            
            logger.info(f"섹터 분석 결과 {len(results)}개 데이터베이스 저장 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            # 저장 실패해도 분석 결과는 반환되도록 예외를 다시 발생시키지 않음
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cache or not self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry
    
    def _update_cache(self, results: List[SectorAnalysisResult]) -> None:
        """캐시 업데이트"""
        self._cache = results
        self._cache_expiry = datetime.now() + self._cache_duration
        logger.debug(f"섹터 분석 결과 캐시 업데이트 (만료: {self._cache_expiry})")
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache = None
        self._cache_expiry = None
        logger.debug("섹터 분석 캐시 초기화")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 정보"""
        return {
            'cached': self._cache is not None,
            'cache_expiry': self._cache_expiry.isoformat() if self._cache_expiry else None,
            'cache_valid': self._is_cache_valid(),
            'cached_sectors': len(self._cache) if self._cache else 0
        }
    
    def update_thresholds(
        self,
        price_momentum: Optional[float] = None,
        supply_demand: Optional[float] = None,
        breadth: Optional[float] = None,
        relative_strength: Optional[float] = None
    ) -> None:
        """
        분석 임계값 업데이트
        
        Args:
            price_momentum: 가격 모멘텀 임계값
            supply_demand: 수급 임계값
            breadth: 확산 임계값
            relative_strength: 상대강도 임계값
        """
        if price_momentum is not None:
            self._price_momentum_threshold = price_momentum
        if supply_demand is not None:
            self._supply_demand_threshold = supply_demand
        if breadth is not None:
            self._breadth_threshold = breadth
        if relative_strength is not None:
            self._relative_strength_threshold = relative_strength
        
        self.clear_cache()  # 임계값 변경시 캐시 초기화
        logger.info("섹터 분석 임계값 업데이트 및 캐시 초기화")
