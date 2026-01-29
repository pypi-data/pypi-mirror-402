from __future__ import annotations

import time
from typing import Dict, Callable, List
import os

from .Menu_Item import MenuItem


class Menu:
	_title: str
	_items: List[MenuItem]
	_items_keys: List[str]
	_index: int
	_current_item: MenuItem
	_parent: Menu | None
	_offset: int = 30
	
	def __init__(self,*, title: str, items: Dict[str, Callable[[],None] | Menu | None] | List[MenuItem], parent: Menu = None):
		self._title = title
		# Create MenuItem if it does not exist in args
		if isinstance(items, Dict):
			_menu_items: List[MenuItem] = []
			for key, value in items.items():
				_menu_item = MenuItem(key, value)
				_menu_items.append(_menu_item)
			self._items = _menu_items
		elif isinstance(items, List):
			self._items = items
			
		self._items_keys = self.get_item_keys()
		self._index = 0
		self._current_item = self._items[0]
		self._parent = parent
	
	def get_item_keys(self) -> List[str]:
		keys:List[str] = []
		for item in self._items:
			keys.append(item._name)
		return keys
		
	
	def on_enter(self):
		self._index = 0
		self._current_item = self._items[0]
	
	def get_parent(self):
		if self._parent is not None:
			return self._parent
	
	def change_index(self, new_index: int):
		self._index = new_index
		self._current_item = self._items[self._index]
	
	def to_call(self) -> Callable | Menu | None:
		return self._current_item._item
	
	def get_values(self) -> List[MenuItem]:
		return self._items
	
	def print_text(self, text: str = None):
		if text is None:
			text = self._title
		print("*" * (len(text) + self._offset))
		print(text.center(len(text) + self._offset))
		print("*" * (len(text) + self._offset))
		print()

	def draw(self):
		self.clear()
		self.print_text()
		for i, item in enumerate(self._items):
			if i == self._index:
				str_format: str = "\033[1m\033[35m\033[43m{}\033[0m"
				print(str_format.format(item._name).center(len(str_format) + len(item._name) + self._offset - int(self._offset // 15)))
			else:
				print(item._name.center(len(item._name) + self._offset))

	@staticmethod
	def clear() -> None:
		os.system("cls" if os.name == "nt" else "clear")