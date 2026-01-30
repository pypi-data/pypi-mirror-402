from pydantic import BaseModel
from typing import List

from doc_layout_parser.domain.block import Block


class Page(BaseModel):
    """Страница обработанного документа."""

    blocks: List[Block]
