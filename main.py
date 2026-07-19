"""
GoAhead - 전체 실행 스크립트
1) DB 생성
2) 더미 데이터 생성 및 삽입
3) 각 프로필별 최단경로 시뮬레이션
"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(__file__)


def run_step(script_name, desc):
    print(f"\n{'#'*60}")
    print(f"  STEP: {desc}")
    print(f"{'#'*60}")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, script_name)],
        cwd=SCRIPT_DIR,
    )
    if result.returncode != 0:
        print(f"[ERROR] {script_name} failed with code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    run_step("db_setup.py", "1. DB 테이블 생성")
    run_step("generate_data.py", "2. 더미 데이터 생성 및 DB 삽입")
    run_step("pathfinder.py", "3. 경로 시뮬레이션 (프로필별 다익스트라)")
    run_step("visualize.py", "4. 그래프 시각화")

    print("\n[DONE] 전체 파이프라인 완료!")
