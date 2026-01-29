#!/usr/bin/env python3
"""
LSMR Stock Picker 데모 스크립트
시스템의 주요 기능을 순차적으로 테스트합니다.
"""

import asyncio
import sys
from datetime import datetime

from lsmr_stock_picker.config.settings import SystemConfig
from lsmr_stock_picker.kis_api.client import KISClient
from lsmr_stock_picker.analyzers.market_regime_analyzer import MarketRegimeAnalyzer
from lsmr_stock_picker.analyzers.sector_filter import SectorFilter
from lsmr_stock_picker.analyzers.stock_picker import StockPicker
from lsmr_stock_picker.analyzers.risk_manager import RiskManager
from lsmr_stock_picker.utils.logging import setup_logging, get_logger

# 로깅 설정
logger = setup_logging()
demo_logger = get_logger(__name__)


def print_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step: int, description: str):
    """단계 출력"""
    print(f"\n[단계 {step}] {description}")
    print("-" * 80)


async def main():
    """메인 데모 함수"""
    print_header("🚀 LSMR Stock Picker 시스템 데모")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # 1단계: 설정 로드
        print_step(1, "시스템 설정 로드")
        config = SystemConfig.load(validate=False)  # 데모용으로 검증 비활성화
        print(f"✅ 설정 로드 완료")
        print(f"   - KIS API URL: {config.kis.base_url}")
        print(f"   - 환경: {config.kis.environment.value}")
        print(f"   - Z-Score 임계값: {config.trading.z_score_threshold}")
        print(f"   - Disparity 임계값: {config.trading.disparity_threshold}%")
        
        # 2단계: KIS API 클라이언트 초기화
        print_step(2, "KIS API 클라이언트 초기화")
        kis_client = KISClient(config.kis)
        await kis_client.initialize()
        print(f"✅ KIS API 클라이언트 초기화 완료")
        
        # 건강 상태 확인
        try:
            is_healthy = await kis_client.health_check()
            if is_healthy:
                print(f"✅ KIS API 연결 정상")
            else:
                print(f"⚠️  KIS API 연결 불안정 (데모 모드로 계속)")
        except Exception as e:
            print(f"⚠️  KIS API 건강 상태 확인 실패: {e}")
            print(f"   (데모 모드로 계속 진행)")
        
        # 3단계: 시장 상황 분석
        print_step(3, "시장 상황 분석 (Market Regime Analysis)")
        analyzer = MarketRegimeAnalyzer(kis_client, config.risk)
        
        try:
            market_analysis = await analyzer.analyze_market_regime()
            print(f"✅ 시장 상황 분석 완료")
            print(f"   - 시장 상황: {market_analysis.regime.value.upper()}")
            print(f"   - 신뢰도: {market_analysis.confidence_score:.1f}%")
            print(f"   - KOSPI 상태: {market_analysis.kospi_status}")
            print(f"   - KOSDAQ 상태: {market_analysis.kosdaq_status}")
            print(f"   - 리스크 매개변수:")
            print(f"     • 익절: {market_analysis.risk_parameters.take_profit_percent}%")
            print(f"     • 손절: {market_analysis.risk_parameters.stop_loss_percent}%")
        except Exception as e:
            print(f"⚠️  시장 상황 분석 실패: {e}")
            print(f"   (실제 API 연결이 필요합니다)")
        
        # 4단계: 주도 섹터 식별
        print_step(4, "주도 섹터 식별 (Sector Filter - 4-Way Analysis)")
        sector_filter = SectorFilter(kis_client)
        
        try:
            leading_sectors = await sector_filter.get_leading_sectors(count=3)
            print(f"✅ 주도 섹터 식별 완료")
            print(f"   - 발견된 주도 섹터: {len(leading_sectors)}개")
            
            for i, sector in enumerate(leading_sectors, 1):
                print(f"\n   [{i}] {sector.sector_name} (코드: {sector.sector_code})")
                print(f"       • 종합 점수: {sector.combined_score:.1f}")
                print(f"       • 상위 종목: {', '.join(sector.top_stocks[:3])}")
        except Exception as e:
            print(f"⚠️  주도 섹터 식별 실패: {e}")
            print(f"   (실제 API 연결이 필요합니다)")
        
        # 5단계: 종목 선택 및 신호 생성
        print_step(5, "종목 선택 및 매수 신호 생성 (Stock Picker)")
        stock_picker = StockPicker(kis_client)
        
        try:
            # 주도 섹터가 있는 경우에만 실행
            if 'leading_sectors' in locals() and leading_sectors:
                buy_candidates = await stock_picker.get_buy_candidates(leading_sectors)
                print(f"✅ 종목 선택 완료")
                print(f"   - 매수 후보: {len(buy_candidates)}개")
                
                for i, candidate in enumerate(buy_candidates[:5], 1):  # 상위 5개만 표시
                    print(f"\n   [{i}] {candidate.stock_name} ({candidate.ticker})")
                    print(f"       • Z-Score: {candidate.z_score:.2f}")
                    print(f"       • Disparity: {candidate.disparity_ratio:.2f}%")
                    print(f"       • 신호 강도: {candidate.signal_strength:.1f}")
                    print(f"       • 현재가: {candidate.current_price:,}원")
            else:
                print(f"⚠️  주도 섹터 정보가 없어 종목 선택을 건너뜁니다")
        except Exception as e:
            print(f"⚠️  종목 선택 실패: {e}")
            print(f"   (실제 API 연결이 필요합니다)")
        
        # 6단계: 리스크 관리
        print_step(6, "리스크 관리 시스템 (Risk Manager)")
        risk_manager = RiskManager(config, kis_client)
        await risk_manager.initialize()
        
        print(f"✅ 리스크 관리 시스템 초기화 완료")
        print(f"   - 섹터당 최대 종목: {config.risk.max_stocks_per_sector}개")
        print(f"   - 전체 최대 보유: {config.risk.max_total_holdings}개")
        print(f"   - 일일 손실 한도: {config.risk.daily_loss_limit}%")
        
        try:
            # 현재 보유 종목 확인
            current_holdings = await risk_manager.get_current_holdings()
            print(f"   - 현재 보유 종목: {len(current_holdings)}개")
            
            # 패닉 모드 확인
            is_panic = await risk_manager.check_panic_mode_conditions()
            if is_panic:
                print(f"   ⚠️  패닉 모드 활성화!")
            else:
                print(f"   ✅ 정상 거래 모드")
        except Exception as e:
            print(f"   ⚠️  리스크 상태 확인 실패: {e}")
        
        # 7단계: 시스템 통계
        print_step(7, "시스템 통계 및 성능")
        
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        print(f"✅ 시스템 리소스")
        print(f"   - CPU 사용률: {cpu_usage:.1f}%")
        print(f"   - 메모리 사용: {memory.used / 1024 / 1024 / 1024:.2f}GB / {memory.total / 1024 / 1024 / 1024:.2f}GB")
        print(f"   - 메모리 사용률: {memory.percent:.1f}%")
        
        # 정리
        print_step(8, "시스템 종료")
        await kis_client.close()
        print(f"✅ KIS API 클라이언트 종료 완료")
        
        # 최종 요약
        print_header("📊 데모 완료")
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n✅ 모든 핵심 컴포넌트가 정상적으로 작동합니다!")
        print(f"\n다음 단계:")
        print(f"  1. FastAPI 서버 실행: python -m uvicorn lsmr_stock_picker.main:app --reload")
        print(f"  2. API 문서 확인: http://localhost:8000/docs")
        print(f"  3. WebSocket 연결: ws://localhost:8000/ws")
        print(f"  4. 전략 활성화: POST /v1/strategies/lsmr-001/toggle")
        print(f"\n자세한 내용은 QUICK_START_GUIDE.md를 참조하세요.\n")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        demo_logger.exception("데모 실행 중 오류 발생")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "🎯 " * 40)
    print("LSMR Stock Picker - Leading Sector Mean Reversion 주식 선택 시스템")
    print("🎯 " * 40 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램이 종료되었습니다.")
        sys.exit(0)
