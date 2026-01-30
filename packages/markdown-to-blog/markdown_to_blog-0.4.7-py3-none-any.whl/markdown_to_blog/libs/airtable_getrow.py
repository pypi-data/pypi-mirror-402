"""
Airtable 레코드 조회 유틸리티.

주의:
- 패키지 내부 라이브러리로 사용되므로 import 시점에 `.env` 로드나 loguru sink 설정 같은
  부작용(side-effect)을 만들지 않습니다.
- 필요한 경우 호출 측에서 `.env` 로드(예: `airtable_post_generator._load_dotenv_if_present`)를
  수행한 뒤 사용하세요.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger
from pyairtable import Api


class AirtableClient:
    """Airtable API 클라이언트."""

    def __init__(
        self,
        api_key: str | None = None,
        base_id: str | None = None,
        table_name: str | None = None,
        base_name: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME")
        self.base_name = base_name or os.getenv("AIRTABLE_BASE_NAME")

        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY가 설정되지 않았습니다.")
        if not self.base_id:
            raise ValueError("AIRTABLE_BASE_ID가 설정되지 않았습니다.")
        if not self.table_name:
            raise ValueError("AIRTABLE_TABLE_NAME이 설정되지 않았습니다.")

        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)

        # 호출 측에서 loguru를 무력화하는 패턴이 있어도 문제 없도록,
        # 여기서는 sink 설정을 건드리지 않고 메시지만 남깁니다.
        logger.debug(
            "AirtableClient initialized (Base: {}, Table: {})",
            self.base_name or self.base_id,
            self.table_name,
        )

    def get_record(self, record_id: str) -> dict[str, Any]:
        """특정 record_id로 레코드 전체(id/fields/createdTime)를 조회합니다."""
        return self.table.get(record_id)

    def get_record_fields(self, record_id: str) -> dict[str, Any]:
        """특정 record_id로 레코드의 `fields`만 조회합니다."""
        record = self.table.get(record_id)
        fields = record.get("fields", {})
        if not isinstance(fields, dict):
            raise ValueError("Airtable record fields가 dict가 아닙니다.")
        return fields
