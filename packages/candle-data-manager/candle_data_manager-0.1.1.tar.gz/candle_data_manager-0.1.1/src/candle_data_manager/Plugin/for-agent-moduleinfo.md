# Plugin

여러 Service를 조합하여 중간 수준의 복합 작업을 수행하는 계층. Service는 Core만 의존하지만, Plugin은 여러 Service와 다른 Plugin을 조합할 수 있다.

## SymbolPreparationPlugin

Symbol 등록 + 테이블 준비 조합 Plugin

register_and_prepare(session, archetype, exchange, tradetype, base, quote, timeframe, **optional) -> Symbol
    SymbolService로 Symbol 등록 + SymbolMetadata로 테이블 준비

## UpdateOrchestrationPlugin

Active/Passive Update 조율 Plugin. 메모리 버퍼를 관리하며 대량 데이터 업데이트를 처리한다.

__init__(symbol_service, data_fetch_service, data_save_service, symbol_metadata, symbol_prep_plugin, buffer_size=100000)
    의존성 주입 및 버퍼 크기 설정

active_update(session, archetype, exchange, tradetype) -> UpdateResult
    마켓 리스트 획득 → Symbol 등록 → 전체 데이터 수집
    - 메모리 버퍼 사용 (Symbol별 분리, 총 row 수로 오버플로우 체크)
    - 부분 성공 허용 (실패한 Symbol 수집)

passive_update(session, archetype=None, exchange=None, tradetype=None, base=None, quote=None, timeframe=None, buffer_size=None) -> UpdateResult
    기존 Symbol의 증분 업데이트
    - 조건으로 Symbol 검색
    - 각 Symbol의 last_timestamp 이후 데이터 fetch
    - 메모리 버퍼 사용
    - 부분 성공 허용

## 설계 원칙

1. **복합 작업 조율**: 여러 Service를 조합하여 워크플로우 구성
2. **Plugin 간 조합 허용**: Plugin이 다른 Plugin을 사용할 수 있음 (SymbolPreparationPlugin → UpdateOrchestrationPlugin)
3. **Service 의존성 제한 없음**: Plugin은 필요한 만큼 Service 의존 가능
4. **재사용성**: 공통 작업 패턴을 Plugin으로 추출하여 재사용
