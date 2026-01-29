"""
자동 분석 워크플로우 (Analysis Workflow)
시장 체제 분석 → 섹터 필터 → 종목 선정 흐름을 조정하는 메인 워크플로우
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .market_regime_analyzer import MarketRegimeAnalyzer, MarketAnalysisResult
from .sector_filter import SectorFilter, SectorAnalysisResult
from .stock_picker import StockPicker, StockCandidate
from models.data_models import LeadingSector
from kis_api.client import KISClient, KISAPIError
from database.manager import DatabaseManager
from config.settings import SystemConfig
from utils.error_handling import (
    LSMRError,
    AnalysisError,
    handle_error_with_retry,
    ErrorCategory
)


logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """워크플로우 실행 결과"""
    success: bool
    execution_time: float
    analysis_date: str
    
    # 각 단계 결과
    market_regime_result: Optional[MarketAnalysisResult] = None
    sector_analysis_results: Optional[List[SectorAnalysisResult]] = None
    leading_sectors: Optional[List[LeadingSector]] = None
    stock_candidates: Optional[List[StockCandidate]] = None
    
    # 오류 정보
    error_message: Optional[str] = None
    failed_step: Optional[str] = None
    
    # 통계
    total_sectors_analyzed: int = 0
    total_stocks_analyzed: int = 0
    total_candidates_found: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            'success': self.success,
            'execution_time': self.execution_time,
            'analysis_date': self.analysis_date,
            'error_message': self.error_message,
            'failed_step': self.failed_step,
            'statistics': {
                'total_sectors_analyzed': self.total_sectors_analyzed,
                'total_stocks_analyzed': self.total_stocks_analyzed,
                'total_candidates_found': self.total_candidates_found
            }
        }
        
        if self.market_regime_result:
            result['market_regime'] = self.market_regime_result.to_dict()
        
        if self.sector_analysis_results:
            result['sector_analysis'] = [s.to_dict() for s in self.sector_analysis_results]
        
        if self.leading_sectors:
            result['leading_sectors'] = [s.to_dict() for s in self.leading_sectors]
        
        if self.stock_candidates:
            result['stock_candidates'] = [c.to_dict() for c in self.stock_candidates]
        
        return result


class AnalysisWorkflow:
    """
    자동 분석 워크플로우
    
    요구사항:
    - 13.1: 시스템 시작 시 시장 체제 분석 실행
    - 13.2: 시장 체제 분석 완료 후 섹터 분석 실행
    - 13.3: 섹터 분석 완료 후 상위 3개 섹터에 대한 종목 선정 실행
    - 13.4: 모든 분석 단계 완료 후 결과를 데이터베이스에 저장
    - 13.5: 분석 단계 실패 시 상세한 오류 정보 로깅 및 가능한 경우 다음 단계로 계속 진행
    """
    
    def __init__(
        self,
        kis_client: KISClient,
        db_manager: DatabaseManager,
        config: Optional[SystemConfig] = None
    ):
        """
        초기화
        
        Args:
            kis_client: KIS API 클라이언트
            db_manager: 데이터베이스 관리자
            config: 시스템 설정 (선택사항)
        """
        self.kis_client = kis_client
        self.db_manager = db_manager
        self.config = config
        
        # 분석 컴포넌트 초기화
        self.market_analyzer = MarketRegimeAnalyzer(
            kis_client=kis_client,
            db_manager=db_manager,
            risk_config=config.risk_config if config else None
        )
        
        self.sector_filter = SectorFilter(
            kis_client=kis_client,
            db_manager=db_manager,
            config=config
        )
        
        self.stock_picker = StockPicker(
            kis_client=kis_client,
            db_manager=db_manager,
            config=config
        )
        
        # 워크플로우 상태
        self._is_running = False
        self._last_execution_time: Optional[datetime] = None
        self._last_result: Optional[WorkflowResult] = None
        
        logger.info("Analysis Workflow 초기화 완료")
    
    async def run_full_analysis(
        self,
        use_cache: bool = False,
        save_to_db: bool = True
    ) -> WorkflowResult:
        """
        전체 분석 워크플로우 실행 (요구사항 13.1, 13.2, 13.3, 13.4, 13.5)
        
        Args:
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            WorkflowResult: 워크플로우 실행 결과
        """
        if self._is_running:
            logger.warning("워크플로우가 이미 실행 중입니다")
            return WorkflowResult(
                success=False,
                execution_time=0.0,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                error_message="워크플로우가 이미 실행 중입니다",
                failed_step="startup"
            )
        
        self._is_running = True
        start_time = datetime.now()
        analysis_date = start_time.strftime('%Y-%m-%d')
        
        logger.info("=" * 80)
        logger.info(f"전체 분석 워크플로우 시작: {analysis_date}")
        logger.info("=" * 80)
        
        try:
            # 단계 1: 시장 체제 분석 (요구사항 13.1)
            market_result = await self._run_market_regime_analysis(use_cache, save_to_db)
            
            # 단계 2: 섹터 분석 (요구사항 13.2)
            sector_results, leading_sectors = await self._run_sector_analysis(
                use_cache,
                save_to_db
            )
            
            # 단계 3: 종목 선정 (요구사항 13.3)
            stock_candidates = await self._run_stock_picking(
                leading_sectors,
                use_cache,
                save_to_db
            )
            
            # 실행 시간 계산
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 통계 계산
            total_sectors = len(sector_results) if sector_results else 0
            total_stocks = sum(len(c) for c in stock_candidates.values()) if stock_candidates else 0
            total_candidates = sum(
                len([c for c in candidates if c.signal_strength >= 60])
                for candidates in stock_candidates.values()
            ) if stock_candidates else 0
            
            # 결과 생성
            result = WorkflowResult(
                success=True,
                execution_time=execution_time,
                analysis_date=analysis_date,
                market_regime_result=market_result,
                sector_analysis_results=sector_results,
                leading_sectors=leading_sectors,
                stock_candidates=self._flatten_stock_candidates(stock_candidates),
                total_sectors_analyzed=total_sectors,
                total_stocks_analyzed=total_stocks,
                total_candidates_found=total_candidates
            )
            
            # 결과 저장
            self._last_execution_time = start_time
            self._last_result = result
            
            logger.info("=" * 80)
            logger.info(
                f"전체 분석 워크플로우 완료: "
                f"소요시간 {execution_time:.2f}초, "
                f"섹터 {total_sectors}개, "
                f"종목 {total_stocks}개 분석, "
                f"매수 후보 {total_candidates}개 발견"
            )
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"워크플로우 실행 오류: {e}"
            logger.error(error_msg, exc_info=True)
            
            return WorkflowResult(
                success=False,
                execution_time=execution_time,
                analysis_date=analysis_date,
                error_message=error_msg,
                failed_step="unknown"
            )
            
        finally:
            self._is_running = False
    
    async def _run_market_regime_analysis(
        self,
        use_cache: bool,
        save_to_db: bool
    ) -> Optional[MarketAnalysisResult]:
        """
        시장 체제 분석 단계 실행 (요구사항 13.1, 13.5)
        
        Args:
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            Optional[MarketAnalysisResult]: 시장 분석 결과 (실패 시 None)
        """
        step_name = "시장 체제 분석"
        logger.info(f"[단계 1/3] {step_name} 시작")
        
        try:
            result = await self.market_analyzer.analyze_market_regime(
                use_cache=use_cache,
                save_to_db=save_to_db
            )
            
            logger.info(
                f"[단계 1/3] {step_name} 완료: "
                f"{result.regime.value.upper()} "
                f"(신뢰도: {result.confidence_score:.1f}%)"
            )
            
            return result
            
        except Exception as e:
            # 요구사항 13.5: 상세한 오류 정보 로깅
            error_msg = f"{step_name} 실패: {e}"
            logger.error(error_msg, exc_info=True)
            
            # 부분 실패 처리: 다음 단계로 계속 진행
            logger.warning(f"{step_name} 실패했지만 다음 단계로 계속 진행합니다")
            return None
    
    async def _run_sector_analysis(
        self,
        use_cache: bool,
        save_to_db: bool
    ) -> tuple[Optional[List[SectorAnalysisResult]], Optional[List[LeadingSector]]]:
        """
        섹터 분석 단계 실행 (요구사항 13.2, 13.5)
        
        Args:
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            Tuple: (섹터 분석 결과 리스트, 주도 섹터 리스트) (실패 시 (None, None))
        """
        step_name = "섹터 분석"
        logger.info(f"[단계 2/3] {step_name} 시작")
        
        try:
            # 전체 섹터 분석
            sector_results = await self.sector_filter.analyze_all_sectors(
                use_cache=use_cache,
                save_to_db=save_to_db
            )
            
            # 상위 3개 주도 섹터 선정 (요구사항 2.7)
            leading_sectors = await self.sector_filter.get_leading_sectors(
                count=3,
                use_cache=True  # 방금 분석한 결과 사용
            )
            
            logger.info(
                f"[단계 2/3] {step_name} 완료: "
                f"{len(sector_results)}개 섹터 분석, "
                f"상위 3개 주도 섹터 선정 - " +
                ", ".join([f"{s.sector_name}({s.combined_score:.1f})" for s in leading_sectors])
            )
            
            return sector_results, leading_sectors
            
        except Exception as e:
            # 요구사항 13.5: 상세한 오류 정보 로깅
            error_msg = f"{step_name} 실패: {e}"
            logger.error(error_msg, exc_info=True)
            
            # 부분 실패 처리: 다음 단계로 계속 진행
            logger.warning(f"{step_name} 실패했지만 다음 단계로 계속 진행합니다")
            return None, None
    
    async def _run_stock_picking(
        self,
        leading_sectors: Optional[List[LeadingSector]],
        use_cache: bool,
        save_to_db: bool
    ) -> Dict[str, List[StockCandidate]]:
        """
        종목 선정 단계 실행 (요구사항 13.3, 13.5)
        
        Args:
            leading_sectors: 주도 섹터 리스트
            use_cache: 캐시 사용 여부
            save_to_db: 데이터베이스 저장 여부
            
        Returns:
            Dict[str, List[StockCandidate]]: 섹터별 종목 후보 딕셔너리
        """
        step_name = "종목 선정"
        logger.info(f"[단계 3/3] {step_name} 시작")
        
        if not leading_sectors:
            logger.warning(f"{step_name}: 주도 섹터가 없어 건너뜁니다")
            return {}
        
        stock_candidates = {}
        
        try:
            # 각 주도 섹터에 대해 종목 분석 (병렬 처리)
            tasks = []
            for sector in leading_sectors:
                task = self.stock_picker.analyze_sector_stocks(
                    sector=sector,
                    use_cache=use_cache,
                    save_to_db=save_to_db
                )
                tasks.append((sector.sector_name, task))
            
            # 병렬 실행
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 결과 수집
            for i, result in enumerate(results):
                sector_name = tasks[i][0]
                
                if isinstance(result, Exception):
                    # 요구사항 13.5: 개별 섹터 실패 시 로깅하고 계속 진행
                    logger.error(f"섹터 {sector_name} 종목 분석 실패: {result}")
                    stock_candidates[sector_name] = []
                else:
                    stock_candidates[sector_name] = result
                    logger.info(
                        f"섹터 {sector_name}: {len(result)}개 종목 후보 발견"
                    )
            
            total_candidates = sum(len(c) for c in stock_candidates.values())
            logger.info(
                f"[단계 3/3] {step_name} 완료: "
                f"총 {total_candidates}개 종목 후보 발견"
            )
            
            return stock_candidates
            
        except Exception as e:
            # 요구사항 13.5: 상세한 오류 정보 로깅
            error_msg = f"{step_name} 실패: {e}"
            logger.error(error_msg, exc_info=True)
            
            # 부분 실패 처리
            logger.warning(f"{step_name} 실패했지만 부분 결과를 반환합니다")
            return stock_candidates
    
    def _flatten_stock_candidates(
        self,
        candidates_by_sector: Dict[str, List[StockCandidate]]
    ) -> List[StockCandidate]:
        """
        섹터별 종목 후보를 단일 리스트로 평탄화
        
        Args:
            candidates_by_sector: 섹터별 종목 후보 딕셔너리
            
        Returns:
            List[StockCandidate]: 평탄화된 종목 후보 리스트
        """
        all_candidates = []
        for candidates in candidates_by_sector.values():
            all_candidates.extend(candidates)
        
        # 신호 강도로 정렬
        all_candidates.sort(key=lambda x: x.signal_strength, reverse=True)
        
        return all_candidates
    
    async def run_market_regime_only(self) -> Optional[MarketAnalysisResult]:
        """
        시장 체제 분석만 실행
        
        Returns:
            Optional[MarketAnalysisResult]: 시장 분석 결과
        """
        logger.info("시장 체제 분석 단독 실행")
        return await self._run_market_regime_analysis(use_cache=False, save_to_db=True)
    
    async def run_sector_analysis_only(self) -> Optional[List[LeadingSector]]:
        """
        섹터 분석만 실행
        
        Returns:
            Optional[List[LeadingSector]]: 주도 섹터 리스트
        """
        logger.info("섹터 분석 단독 실행")
        _, leading_sectors = await self._run_sector_analysis(use_cache=False, save_to_db=True)
        return leading_sectors
    
    def get_last_result(self) -> Optional[WorkflowResult]:
        """
        마지막 워크플로우 실행 결과 조회
        
        Returns:
            Optional[WorkflowResult]: 마지막 실행 결과
        """
        return self._last_result
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        워크플로우 상태 정보
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        return {
            'is_running': self._is_running,
            'last_execution_time': self._last_execution_time.isoformat() if self._last_execution_time else None,
            'last_result_success': self._last_result.success if self._last_result else None,
            'last_result_date': self._last_result.analysis_date if self._last_result else None
        }
    
    async def validate_workflow_components(self) -> Dict[str, bool]:
        """
        워크플로우 컴포넌트 검증
        
        Returns:
            Dict[str, bool]: 컴포넌트별 검증 결과
        """
        logger.info("워크플로우 컴포넌트 검증 시작")
        
        validation_results = {
            'kis_client': False,
            'database': False,
            'market_analyzer': False,
            'sector_filter': False,
            'stock_picker': False
        }
        
        try:
            # KIS API 클라이언트 검증
            try:
                await self.kis_client.authenticate()
                validation_results['kis_client'] = True
                logger.info("✓ KIS API 클라이언트 검증 성공")
            except Exception as e:
                logger.error(f"✗ KIS API 클라이언트 검증 실패: {e}")
            
            # 데이터베이스 검증
            try:
                await self.db_manager.connect()
                validation_results['database'] = True
                logger.info("✓ 데이터베이스 연결 검증 성공")
            except Exception as e:
                logger.error(f"✗ 데이터베이스 연결 검증 실패: {e}")
            
            # 분석 컴포넌트 검증
            validation_results['market_analyzer'] = self.market_analyzer is not None
            validation_results['sector_filter'] = self.sector_filter is not None
            validation_results['stock_picker'] = self.stock_picker is not None
            
            logger.info("✓ 분석 컴포넌트 검증 완료")
            
            all_valid = all(validation_results.values())
            if all_valid:
                logger.info("모든 워크플로우 컴포넌트 검증 성공")
            else:
                logger.warning("일부 워크플로우 컴포넌트 검증 실패")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"워크플로우 컴포넌트 검증 오류: {e}")
            return validation_results
    
    async def cleanup(self) -> None:
        """
        워크플로우 정리 및 리소스 해제
        """
        logger.info("워크플로우 정리 시작")
        
        try:
            # 캐시 초기화
            self.market_analyzer.clear_cache()
            self.sector_filter.clear_cache()
            self.stock_picker.clear_cache()
            
            # 데이터베이스 연결 종료
            if self.db_manager:
                await self.db_manager.disconnect()
            
            logger.info("워크플로우 정리 완료")
            
        except Exception as e:
            logger.error(f"워크플로우 정리 오류: {e}")
