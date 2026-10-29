"""Система доставки товаров между складом и магазином."""

from abc import ABC, abstractmethod


# ---------- Исключения ----------
class StorageError(Exception):
    """Базовое исключение для операций с хранилищем."""


class NotEnoughItemsError(StorageError):
    """Недостаточно товара в источнике."""


class NoFreeSpaceError(StorageError):
    """Не хватает свободного места в приёмнике."""


class TooManyUniqueItemsError(StorageError):
    """Превышен лимит уникальных товаров."""


# ---------- Абстрактный класс ----------
class Storage(ABC):
    """Абстрактное хранилище товаров."""

    def __init__(self, items: dict, capacity: int):
        self._items = {k.lower(): v for k, v in items.items() if v > 0}
        self._capacity = capacity

    @abstractmethod
    def add(self, name: str, amount: int) -> None:
        """Добавить товар name в количестве amount."""

    @abstractmethod
    def remove(self, name: str, amount: int) -> None:
        """Забрать товар name в количестве amount."""

    # --- общие методы ---
    def get_free_space(self) -> int:
        return self._capacity - sum(self._items.values())

    def get_items(self) -> dict:
        return dict(self._items)

    def get_unique_items_count(self) -> int:
        return len(self._items)

    # --- dunder-методы ---
    def __len__(self) -> int:
        return sum(self._items.values())

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._items

    def __iter__(self):
        return iter(self._items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(items={self._items!r}, capacity={self._capacity})"

    def __str__(self) -> str:
        if not self._items:
            return "пусто"
        return ", ".join(f"{n}: {c}" for n, c in self._items.items())


# ---------- Склад ----------
class Store(Storage):
    """Склад — без ограничений на число видов товаров."""

    def __init__(self, items: dict, capacity: int = 100):
        super().__init__(items, capacity)

    def add(self, name: str, amount: int) -> None:
        if amount <= 0:
            raise ValueError("количество должно быть положительным")
        if self.get_free_space() < amount:
            raise NoFreeSpaceError(
                f"на складе недостаточно места: нужно {amount}, "
                f"свободно {self.get_free_space()}"
            )
        key = name.lower()
        self._items[key] = self._items.get(key, 0) + amount

    def remove(self, name: str, amount: int) -> None:
        if amount <= 0:
            raise ValueError("количество должно быть положительным")
        key = name.lower()
        if self._items.get(key, 0) < amount:
            raise NotEnoughItemsError(
                f"на складе нет {amount} '{key}': есть {self._items.get(key, 0)}"
            )
        self._items[key] -= amount
        if self._items[key] == 0:
            del self._items[key]


# ---------- Магазин ----------
class Shop(Storage):
    """Магазин — не более 5 уникальных товаров."""

    MAX_UNIQUE = 5

    def __init__(self, items: dict, capacity: int = 20):
        super().__init__(items, capacity)

    def add(self, name: str, amount: int) -> None:
        if amount <= 0:
            raise ValueError("количество должно быть положительным")
        key = name.lower()
        is_new = key not in self._items
        if is_new and self.get_unique_items_count() >= self.MAX_UNIQUE:
            raise TooManyUniqueItemsError(
                f"в магазине уже {self.MAX_UNIQUE} видов товаров, "
                f"нельзя добавить новый '{key}'"
            )
        if self.get_free_space() < amount:
            raise NoFreeSpaceError(
                f"в магазине недостаточно места: нужно {amount}, "
                f"свободно {self.get_free_space()}"
            )
        self._items[key] = self._items.get(key, 0) + amount

    def remove(self, name: str, amount: int) -> None:
        if amount <= 0:
            raise ValueError("количество должно быть положительным")
        key = name.lower()
        if self._items.get(key, 0) < amount:
            raise NotEnoughItemsError(
                f"в магазине нет {amount} '{key}': есть {self._items.get(key, 0)}"
            )
        self._items[key] -= amount
        if self._items[key] == 0:
            del self._items[key]


# ---------- Запрос ----------
class Request:
    """Разбор строки вида: 'доставить 3 печеньки из склад в магазин'."""

    def __init__(self, request_str: str):
        self.amount = 0
        self.product = ""
        self.from_point = ""
        self.to_point = ""
        self._parse(request_str)

    def _parse(self, raw: str) -> None:
        parts = raw.lower().split()
        if len(parts) != 7:
            raise ValueError("ожидается 7 слов в запросе")
        keyword, amount_str, product, prep1, from_point, prep2, to_point = parts
        if keyword != "доставить":
            raise ValueError("запрос должен начинаться со слова 'доставить'")
        if prep1 != "из" or prep2 != "в":
            raise ValueError("используйте шаблон: доставить n товар из x в y")
        if not amount_str.isdigit() or int(amount_str) <= 0:
            raise ValueError("количество должно быть положительным числом")
        self.amount = int(amount_str)
        self.product = product
        self.from_point = from_point
        self.to_point = to_point

    def __repr__(self) -> str:
        return (f"Request(amount={self.amount}, product={self.product!r}, "
                f"from={self.from_point!r}, to={self.to_point!r})")

    def __str__(self) -> str:
        return (f"доставить {self.amount} {self.product} "
                f"из {self.from_point} в {self.to_point}")


# ---------- Основная логика ----------
def build_storages() -> dict:
    """Создаёт хранилища и возвращает словарь для сопоставления по имени."""
    initial_store = {"печеньки": 10, "собачки": 10, "коробки": 10,
                     "конфеты": 10, "игрушки": 10}
    initial_shop = {"собачки": 2, "коробки": 5}
    return {
        "склад": Store(items=initial_store),
        "магазин": Shop(items=initial_shop),
    }


def show_state(storages: dict) -> None:
    print("\nтекущие запасы:")
    for name, storage in storages.items():
        print(f"  {name}: {storage}")


def handle_request(storages: dict, request: Request) -> None:
    """Выполняет один запрос с проверками и отчётом."""
    src = storages.get(request.from_point)
    dst = storages.get(request.to_point)

    if src is None or dst is None:
        print("неверное название хранилища, используйте 'склад' или 'магазин'")
        return
    if src is dst:
        print("источник и приёмник совпадают — доставка не имеет смысла")
        return

    # наличие товара
    if request.product not in src or src.get_items()[request.product] < request.amount:
        have = src.get_items().get(request.product, 0)
        if have == 0:
            print(f"в '{request.from_point}' нет товара '{request.product}'")
        else:
            print(f"не хватает '{request.product}' в '{request.from_point}': "
                  f"нужно {request.amount}, есть {have}")
        return

    # свободное место в приёмнике
    if dst.get_free_space() < request.amount:
        print(f"в '{request.to_point}' недостаточно места: "
              f"нужно {request.amount}, свободно {dst.get_free_space()}")
        return

    # проверка лимита уникальных товаров магазина
    if isinstance(dst, Shop) and request.product not in dst:
        if dst.get_unique_items_count() >= Shop.MAX_UNIQUE:
            print(f"в магазине уже {Shop.MAX_UNIQUE} видов товаров, "
                  f"нельзя добавить новый '{request.product}'")
            return

    # собственно перемещение
    print(f"курьер забирает {request.amount} {request.product} "
          f"из {request.from_point}")
    src.remove(request.product, request.amount)
    print(f"курьер везёт {request.amount} {request.product} "
          f"из {request.from_point} в {request.to_point}")
    dst.add(request.product, request.amount)
    print(f"курьер доставил {request.amount} {request.product} "
          f"в {request.to_point}")


def main() -> None:
    storages = build_storages()
    print("система доставки запущена. введите 'стоп' или 'выход' для завершения")

    while True:
        show_state(storages)
        raw = input(
            "\nвведите запрос:\n"
            "  доставить <кол-во> <товар> из <склад|магазин> в <склад|магазин>\n"
            "  (или 'стоп'/'выход')\n-> "
        ).strip()

        if raw.lower() in ("стоп", "выход"):
            print("спасибо за использование системы доставки!")
            break

        try:
            request = Request(raw)
            handle_request(storages, request)
        except (ValueError, StorageError) as exc:
            print(f"ошибка: {exc}")
        except Exception as exc:
            print(f"непредвиденная ошибка: {exc}")


if __name__ == "__main__":
    main()