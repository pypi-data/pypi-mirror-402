from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateResult:
    # Active/Passive Update 결과
    success_symbols: list  # 성공한 Symbol 리스트
    failed_symbols: list  # 실패한 Symbol과 이유 리스트 [(symbol, reason), ...]
    total_rows: int  # 총 저장된 row 수
