import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from candle_data_manager.Core.CandleFetcher.Service.NullHandlingService.NullHandlingService import NullHandlingService
from candle_data_manager.Particles.InvalidDataError import InvalidDataError
from candle_data_manager.Core.Models.CandleRepository import CandleRepository


class TestVolumeNullHandling:

    def test_volume_null_becomes_zero(self):
        # volume이 null이면 0으로 변환
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': None}
        ]

        result = service.handle(data, symbol)

        assert result[0]['volume'] == 0

    def test_multiple_volume_nulls(self):
        # 여러 캔들의 volume이 null
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': None},
            {'timestamp': 2, 'open': 105, 'high': 115, 'low': 100, 'close': 110, 'volume': None}
        ]

        result = service.handle(data, symbol)

        assert result[0]['volume'] == 0
        assert result[1]['volume'] == 0

    def test_volume_with_valid_value_unchanged(self):
        # volume이 유효한 값이면 그대로 유지
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000}
        ]

        result = service.handle(data, symbol)

        assert result[0]['volume'] == 1000


class TestPriceNullHandling:

    def test_price_null_uses_previous_close(self):
        # 가격이 null이면 이전 캔들의 close 값 사용
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            {'timestamp': 2, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 500}
        ]

        result = service.handle(data, symbol)

        assert result[1]['open'] == 105
        assert result[1]['high'] == 105
        assert result[1]['low'] == 105
        assert result[1]['close'] == 105

    def test_partial_null_prices(self):
        # 일부 가격만 null인 경우
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            {'timestamp': 2, 'open': None, 'high': 115, 'low': None, 'close': 110, 'volume': 500}
        ]

        result = service.handle(data, symbol)

        assert result[1]['open'] == 105
        assert result[1]['high'] == 115
        assert result[1]['low'] == 105
        assert result[1]['close'] == 110

    def test_consecutive_null_prices(self):
        # 연속된 캔들의 가격이 null
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            {'timestamp': 2, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 500},
            {'timestamp': 3, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 600}
        ]

        result = service.handle(data, symbol)

        assert result[1]['close'] == 105
        assert result[2]['close'] == 105

    def test_first_candle_null_uses_db(self):
        # 첫 캔들의 가격이 null → DB 조회
        conn_manager = MagicMock()
        symbol = Mock()
        symbol.id = 1

        # DB에서 반환할 마지막 캔들 데이터 (가격은 이미 float로 변환됨)
        mock_df = pd.DataFrame({
            'timestamp': [1000],
            'open': [95.0],
            'high': [100.0],
            'low': [90.0],
            'close': [98.0],
            'volume': [500.0]
        })

        # CandleRepository.query_to_dataframe mock
        with patch('candle_data_manager.Core.CandleFetcher.Service.NullHandlingService.NullHandlingService.CandleRepository') as mock_repo:
            mock_repo.query_to_dataframe.return_value = mock_df

            service = NullHandlingService(conn_manager)

            data = [
                {'timestamp': 2000, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 1000}
            ]

            result = service.handle(data, symbol)

            assert result[0]['open'] == 98.0
            assert result[0]['high'] == 98.0
            assert result[0]['low'] == 98.0
            assert result[0]['close'] == 98.0

    def test_first_candle_null_no_db_data_raises_error(self):
        # 첫 캔들 null + DB에도 데이터 없음 → InvalidDataError
        conn_manager = MagicMock()
        symbol = Mock()
        symbol.id = 1

        # DB에서 빈 DataFrame 반환
        mock_df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        with patch('candle_data_manager.Core.CandleFetcher.Service.NullHandlingService.NullHandlingService.CandleRepository') as mock_repo:
            mock_repo.query_to_dataframe.return_value = mock_df

            service = NullHandlingService(conn_manager)

            data = [
                {'timestamp': 2000, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 1000}
            ]

            with pytest.raises(InvalidDataError) as exc_info:
                service.handle(data, symbol)

            assert "Cannot fill null prices" in str(exc_info.value)


class TestMixedNullHandling:

    def test_volume_and_price_nulls(self):
        # volume과 가격 모두 null
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            {'timestamp': 2, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': None}
        ]

        result = service.handle(data, symbol)

        assert result[1]['open'] == 105
        assert result[1]['high'] == 105
        assert result[1]['low'] == 105
        assert result[1]['close'] == 105
        assert result[1]['volume'] == 0

    def test_no_nulls(self):
        # null이 없는 경우 그대로 반환
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = [
            {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            {'timestamp': 2, 'open': 105, 'high': 115, 'low': 100, 'close': 110, 'volume': 1100}
        ]

        result = service.handle(data, symbol)

        assert result[0] == data[0]
        assert result[1] == data[1]

    def test_empty_list(self):
        # 빈 리스트 처리
        conn_manager = Mock()
        service = NullHandlingService(conn_manager)
        symbol = Mock()

        data = []

        result = service.handle(data, symbol)

        assert result == []


class TestDbQuery:

    def test_db_query_with_symbol_id(self):
        # DB 조회시 symbol_id 전달 확인
        conn_manager = MagicMock()
        symbol = Mock()
        symbol.id = 42

        mock_df = pd.DataFrame({
            'timestamp': [1000],
            'open': [95.0],
            'high': [100.0],
            'low': [90.0],
            'close': [98.0],
            'volume': [500.0]
        })

        with patch('candle_data_manager.Core.CandleFetcher.Service.NullHandlingService.NullHandlingService.CandleRepository') as mock_repo:
            mock_repo.query_to_dataframe.return_value = mock_df

            service = NullHandlingService(conn_manager)

            data = [
                {'timestamp': 2000, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 1000}
            ]

            service.handle(data, symbol)

            # query_to_dataframe 호출시 symbol_id가 전달되었는지 확인
            call_args = mock_repo.query_to_dataframe.call_args
            assert call_args[1]['symbol_id'] == 42

    def test_db_query_with_timestamp_limit(self):
        # DB 조회시 첫 캔들의 timestamp보다 작은 데이터만 조회
        conn_manager = MagicMock()
        symbol = Mock()
        symbol.id = 1

        mock_df = pd.DataFrame({
            'timestamp': [1000],
            'open': [95.0],
            'high': [100.0],
            'low': [90.0],
            'close': [98.0],
            'volume': [500.0]
        })

        with patch('candle_data_manager.Core.CandleFetcher.Service.NullHandlingService.NullHandlingService.CandleRepository') as mock_repo:
            mock_repo.query_to_dataframe.return_value = mock_df

            service = NullHandlingService(conn_manager)

            data = [
                {'timestamp': 2000, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': 1000}
            ]

            service.handle(data, symbol)

            # end_ts로 첫 캔들의 timestamp가 전달되었는지 확인
            call_args = mock_repo.query_to_dataframe.call_args
            assert call_args[1]['end_ts'] == 2000
