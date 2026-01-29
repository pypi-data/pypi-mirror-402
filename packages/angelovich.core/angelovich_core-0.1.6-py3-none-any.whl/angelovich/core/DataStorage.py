import logging
import uuid
from typing import List, Dict, Optional, Type, Hashable, Iterable

from angelovich.core.Dispatcher import Dispatcher

logger = logging.getLogger(__name__)


class EntityComponent:
	def __init__(self):
		self.__entity_ref: Optional[Entity] = None

	def _set_entity_ref(self, entity: "Entity") -> None:
		self.__entity_ref = entity

	def _reset(self):
		self.__entity_ref = None

	# mark a related entity with a marker component
	def add_marker(self, marker_type: Type["EntityComponent"]) -> None:
		self.__entity_ref.add_component(marker_type())

	def _ds(self) -> "DataStorage":
		return self.__entity_ref._get_ds()


class EntityHashComponent(EntityComponent):
	def __hash__(self):
		raise NotImplementedError()

	def __eq__(self, other):
		return hash(self) == hash(other)


class Entity:
	def __init__(self, ds: "DataStorage"):
		self.__ds: DataStorage = ds
		self.__entity_id: int = 0
		self.__components: Dict[Type[EntityComponent], EntityComponent] = {}

	@property
	def entity_id(self) -> int:
		return self.__entity_id

	def has_component(self, component_type: Type[EntityComponent]) -> bool:
		return component_type in self.__components

	def add_component(self, component: EntityComponent) -> "Entity":
		if type(component) in self.__components:
			logger.warning(f"Component {type(component)} already added")

			return self
		self.__components[type(component)] = component
		component._set_entity_ref(self)
		self.__ds._add_component(self, component)
		return self

	def remove_component[T:EntityComponent](self, component_type: Type[T]) -> "Entity":
		self.__ds._remove_component(self, component_type)
		self.get_component(component_type)._reset()
		del self.__components[component_type]
		return self

	def get_component[T:EntityComponent](self, component_type: Type[T]) -> T:
		result = self.__components.get(component_type)
		if not result:
			raise RuntimeError(f"Component {component_type} not found in entity {self}")
		return result

	def is_valid(self) -> bool:
		return bool(self.__entity_id)

	def _init(self, entity_id: int) -> "Entity":
		self.__entity_id = entity_id
		return self

	def _reset(self) -> int:
		for c_type, component in self.__components.items():
			self.__ds._remove_component(self, c_type)
			component._reset()
		self.__components.clear()
		result = self.__entity_id
		self.__entity_id = 0
		return result

	def __repr__(self):
		return f"Entity {self.__entity_id} ({', '.join(c.__name__ for c in self.__components.keys())})"

	def _get_ds(self) -> "DataStorage":
		return self.__ds


class _Collection(Dispatcher, Iterable[Entity]):
	EVENT_ADDED = "ADDED"
	EVENT_REMOVED = "REMOVED"

	@property
	def entities(self) -> List[Entity]:
		raise NotImplementedError()

	def __iter__(self):
		raise NotImplementedError()

	def find(self, search_value: Hashable) -> Optional[Entity]:
		raise RuntimeError("Not hashable collection can't use find")

	def _add(self, entity: Entity, component: EntityComponent) -> None:
		self.dispatch(self.EVENT_ADDED, entity, component)

	def _remove(self, entity: Entity, component_type: type) -> None:
		self.dispatch(self.EVENT_REMOVED, entity)

	def __len__(self):
		raise NotImplementedError()


class HashCollection(_Collection):
	def __init__(self):
		super().__init__()
		self.__data: Dict[Hashable, Entity] = {}

	@property
	def entities(self) -> List[Entity]:
		return list(self.__data.values())

	def find(self, search_value: Hashable) -> Optional[Entity]:
		return self.__data.get(search_value, None)

	def _add(self, entity: Entity, component: EntityComponent) -> None:
		if component in self.__data:
			raise RuntimeError(f"Component {component} already added to entity {entity}")
		self.__data[component] = entity
		super()._add(entity, component)

	def _remove[T: EntityComponent](self, entity: Entity, component_type: Type[T]) -> None:
		super()._remove(entity, component_type)
		del self.__data[entity.get_component(component_type)]

	def __len__(self):
		return len(self.__data)

	def __iter__(self):
		for key in self.__data:
			yield self.__data[key]


class ListCollection(_Collection):
	def __init__(self):
		super().__init__()
		self.__data: List[Entity] = []

	@property
	def entities(self) -> List[Entity]:
		return self.__data.copy()

	def _add(self, entity: Entity, component: EntityComponent) -> None:
		self.__data.append(entity)
		super()._add(entity, component)

	def _remove(self, entity: Entity, _: type) -> None:
		super()._remove(entity, _)
		self.__data.remove(entity)

	def __len__(self):
		return len(self.__data)

	def __iter__(self):
		for value in self.__data:
			yield value


class DataStorage:
	def __init__(self):
		self.__entities: Dict[int, Entity] = {}
		self.__collections: Dict[type, _Collection] = {}

	def create_entity(self) -> Entity:
		eid = uuid.uuid4().int
		entity = Entity(self)
		self.__entities[eid] = entity._init(eid)
		return entity

	def remove_entity(self, entity: Entity) -> None:
		del self.__entities[entity._reset()]

	def get_entity(self, eid: int) -> Optional[Entity]:
		return self.__entities.get(eid, None)

	def get_collection[T: EntityComponent](self, component_type: Type[T]) -> _Collection:
		return self.__collections.setdefault(
			component_type,
			HashCollection() if hasattr(component_type, "__hash__") else ListCollection()
		)

	#
	def clear_collection[T: EntityComponent](self, component_type: Type[T]) -> None:
		entities = self.get_collection(component_type).entities
		for entity in entities:
			self.remove_entity(entity)

	def erase_collection[T: EntityComponent](self, component_type: Type[T]) -> None:
		entities = self.__collections.get(component_type).entities
		for entity in entities:
			entity.remove_component(component_type)

	def _add_component(self, entity: Entity, component: EntityComponent) -> None:
		self.__collections.setdefault(
			type(component),
			HashCollection() if isinstance(component, Hashable) else ListCollection()
		)._add(entity, component)

	def _remove_component[T: EntityComponent](self, entity: Entity, component_type: Type[T]) -> None:
		self.__collections.get(component_type)._remove(entity, component_type)
