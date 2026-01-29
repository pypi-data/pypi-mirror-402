from abc import ABC, abstractmethod

from markdown2 import Markdown


class MarkdownConverter(ABC):
    @abstractmethod
    def convert(self, markdown_text: str) -> str:
        """마크다운 텍스트를 HTML로 변환합니다."""


class PandocConverter(MarkdownConverter):
    # Pandoc 변환기
    def convert(self, markdown_text: str) -> str:
        # 여기에 Pandoc을 사용하여 변환 로직을 구현

        return "<p>이곳은 Pandoc 변환된 HTML입니다.</p>"


class Markdown2Converter(MarkdownConverter):
    # markdown2 변환기
    def convert(self, markdown_text: str) -> str:
        # 여기에 markdown2를 사용하여 변환 로직을 구현
        markdowner = Markdown()
        return markdowner.convert(markdown_text)
