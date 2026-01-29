from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .Menu import Menu


class MenuItem:
	_name: str
	_item: 'Callable[[],None] | Menu | None'
	
	def __init__(self, name: str, item: 'Callable[[],None] | Menu | None' = None):
		self._name = name
		self._item = item
	
	def get_value(self) -> 'Callable[[],None] | Menu | None':
		return self._item
	
	