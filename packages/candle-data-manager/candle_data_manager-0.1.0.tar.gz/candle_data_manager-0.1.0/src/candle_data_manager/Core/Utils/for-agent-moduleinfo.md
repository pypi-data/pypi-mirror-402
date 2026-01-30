# Utils

Provider에서 사용하는 공통 유틸리티 모음.

## NormalizationService
거래소별 데이터 정규화.
키 매핑, 타입 변환, 가격 스케일링 (× 10^8).

## NullHandlingService
Null 값 처리.
volume → 0, 가격 → 이전값/DB/에러.

## ApiValidationService
API 키 검증.
환경변수에서 API 키 조회, 서버 상태 확인.

## TimeConverter
다양한 시간 형식 → Unix timestamp 변환.
