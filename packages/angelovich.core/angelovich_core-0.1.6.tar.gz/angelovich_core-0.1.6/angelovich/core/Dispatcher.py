import asyncio
from typing import Callable, Hashable, Dict, List, Tuple, Coroutine, Any

CallbackType = Callable[[...], Coroutine[Any, Any, Any]]


class Dispatcher:
	def __init__(self):
		self.__handlers: Dict[str, List[Tuple[Hashable, CallbackType]]] = {}

	def add_listener(self, event: str, callback: CallbackType, scope: Hashable = None) -> None:
		self.__handlers.setdefault(event, []).append((scope, callback))

	def remove_listener(self, event: str, scope: Hashable = None) -> None:
		self.__handlers[event] = [(s, c) for s, c in self.__handlers.get(event, []) if s != scope]

	def remove_all_listeners(self, scope: Hashable) -> None:
		for event, handlers in self.__handlers.items():
			self.__handlers[event] = [(s, c) for s, c in handlers if s != scope]

	def dispatch(self, event: str, *args, **kwargs) -> Tuple[asyncio.Task[Any], ...]:
		return tuple(asyncio.create_task(callback(*args, **kwargs)) for e, callback in self.__handlers.get(event, []))
