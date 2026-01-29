from pathlib import Path
from typing import Callable
import os, sys

from .AppContext import AppContext, Setting

from .Menu.Menu import Menu
from .Global_exceptions import global_exception_handler
from .Menu.Menu_Item import MenuItem


class App:
	_read_key: Callable[[], str | None]
	_menu: Menu
	_running: bool
	_ctx: AppContext
	
	def __init__(self, *, head_menu:Menu):
		self._menu = head_menu
		self._running = True
		self._ctx = AppContext(self.get_app_dir())
		self._read_key = self.get_read_key()
		settings: Menu| None = self.build_settings_menu(self._menu, self._ctx, self.get_params(self._menu))
		if settings is not None:
			self._menu._items.append(MenuItem(name="Настройки", item=settings))
			self._menu._items_keys.append("Настройки")
		self._menu._items.append(MenuItem(name="Выход"))
		self._menu._items_keys.append("Выход")
		self.create_back_exit(self._menu)
		sys.excepthook = global_exception_handler
		
	def create_back_exit(self, menu: Menu):
		for item in menu._items:
			if isinstance(item._item, Menu):
				self.create_back_exit(item._item)
		if "Назад" not in menu.get_item_keys() and "Выход" not in menu.get_item_keys():
			back_item = MenuItem(name="Назад")
			menu._items.append(back_item)
			menu._items_keys.append("Назад")
			
	
	@staticmethod
	def get_app_dir() -> Path:
		return Path(sys.argv[0]).resolve().parent
	
	@staticmethod
	def get_read_key() -> Callable[[], str | None]:
		if os.name == "nt":
			import msvcrt
			
			def read_key():
				key = msvcrt.getch()
				
				if key == b'\xe0':
					key = msvcrt.getch()
					return {
						b'H': "UP",
						b'P': "DOWN"
					}.get(key)
				
				if key == b'\r':
					return "ENTER"
				if key == b'\x1b':
					return "ESC"
				
				return None
		else:
			import tty
			import termios
			
			def read_key():
				fd = sys.stdin.fileno()
				old = termios.tcgetattr(fd)
				
				try:
					tty.setraw(fd)
					ch = sys.stdin.read(1)
					
					if ch == "\x1b":
						seq = sys.stdin.read(2)
						return {
							"[A": "UP",
							"[B": "DOWN"
						}.get(seq)
					
					if ch == "\r":
						return "ENTER"
					if ch == "\x03":
						return "ESC"
				
				finally:
					termios.tcsetattr(fd, termios.TCSADRAIN, old)
				
				return None
		return read_key
	
	def call_item(self):
		menu: Menu = self._menu
		
		action: str = menu._current_item._name
		if action == "Назад":
			self._menu = menu.get_parent()
		elif action == "Выход":
			self._running = False
		else:
			obj = self._menu.to_call()
			if isinstance(obj, Menu):
				self._menu = obj
				self._menu.on_enter()
			elif isinstance(obj, Callable):
				self._menu.clear()
				self._menu.print_text(text=action)
				obj(self._ctx)
				self.after_call()
	
	def after_call(self):
		print("\nДля продолжения нажмите Enter...")
		key = self._read_key()
		while key != "ENTER":
			key = self._read_key()
		self._menu.draw()
	
	def run(self):
		# Скроем курсор
		sys.stdout.write("\033[?25l")
		sys.stdout.flush()
		while self._running:
			self._menu.draw()
			key = self._read_key()
			# print(key)
			if key == "UP":
				self._menu.change_index((self._menu._index - 1) % len(self._menu._items_keys))
			elif key == "DOWN":
				self._menu.change_index((self._menu._index + 1) % len(self._menu._items_keys))
			elif key == "ENTER":
				self.call_item()
		self._menu.clear()
		# Покажем курсор снова
		sys.stdout.write("\033[?25h")
		sys.stdout.flush()
		
	def get_params(self, menu: Menu):
		result = set()
		for item in menu._items:
			if isinstance(item._item, Menu):
				item._item._parent = menu
				result |= self.get_params(item._item)
			elif callable(item._item):
				result |= getattr(item._item, "required_settings", set())
		return result
	
	@staticmethod
	def build_settings_menu(parent: Menu, context: AppContext, keys: set[Setting]) -> Menu | None:
		items = {}
		def editor(ctx, k):
			val = getattr(ctx, f"{k.name}", None)
			print(val)
			if val is not None:
				print(f"Значение \'{val.title}\' = {val.value}")
			else:
				print("Настройка не задана!")
			print("Введите новое значение(или \'q\' чтобы выйти) -> ", end="")
			new_val = input()
			k.value = new_val
			if new_val != "q":
				setattr(ctx, f"{k.name}", k)

		
		for key in sorted(keys, key=lambda x: x._title):
			items[f"{key._title}"] = lambda val, ctx=context, k=key, e=editor: e(ctx, k)
		items["Назад"] = None
		if items.keys().__len__() == 1:
			return None
		return Menu(title="Настройки", items=items, parent=parent)