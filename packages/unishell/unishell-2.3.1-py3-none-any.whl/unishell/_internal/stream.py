from typing import List, Any, Dict, TypeVar, Optional, Union, overload
from functools import wraps

T = TypeVar('T')
StreamType = TypeVar('StreamType', bound='Stream')

def chainable(cls: type) -> type:
    """Декоратор для класса, который заставляет все методы возвращать self, если они ничего не возвращают."""
    
    # Получаем все атрибуты класса
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value):
            # Создаем замыкание для сохранения текущего attr_value
            def make_wrapper(method):
                @wraps(method)
                def wrapper(self, *args, **kwargs):
                    result = method(self, *args, **kwargs)
                    # Если метод ничего не возвращает, возвращаем self
                    return result if result is not None else self
                return wrapper
            
            # Заменяем метод на обернутый
            setattr(cls, attr_name, make_wrapper(attr_value))
    
    return cls

class Stream:
    """
    Переопределяет операции работы с потоками для классов наследников.
    Для корректной работы необходимо переопределить следующие методы:
    __stream_rewrite__(self,value) < / >  - запрос на перезапись данных
    __stream_append__(self,value) << / >> - запрос на добавление данных
    __stream_getData__(self)              - запрос на данные
    """
    
    def __lt__(self, other: Union['Stream', str]) -> 'Stream':
        """
        Оператор < : перезаписывает содержимое из другого объекта в текущий.
        """
        if isinstance(other, Stream):
            self.__stream_rewrite__(other.__stream_getData__())
        elif isinstance(other, str):
            self.__stream_rewrite__(other)
        else:
            raise TypeError(f"Ожидался наследник Stream или str")
        return self
    
    def __gt__(self, other: Union['Stream', str]) -> 'Stream':
        """
        Оператор > : перезаписывает содержимое из текущего объекта в другой.
        """
        if isinstance(other, Stream):
            other.__stream_rewrite__(self.__stream_getData__())
            return other
        elif isinstance(other, str):
            self.__stream_rewrite__(other)
            return self
        else:
            raise TypeError(f"Ожидался наследник Stream или str")
    
    def __lshift__(self, other: Union['Stream', str]) -> 'Stream':
        """
        Оператор << : добавляет в конец содержимое из другого объекта в текущий.
        """
        if isinstance(other, Stream):
            self.__stream_append__(other.__stream_getData__())
        elif isinstance(other, str):
            self.__stream_append__(other)  # Исправлено: было __stream_rewrite__, должно быть __stream_append__
        else:
            raise TypeError(f"Ожидался наследник Stream или str")
        return self
    
    def __rshift__(self, other: Union['Stream', str]) -> 'Stream':
        """
        Оператор >> : добавляет в конец содержимое из текущего объекта в другой.
        """
        if isinstance(other, Stream):
            other.__stream_append__(self.__stream_getData__())
            return other
        elif isinstance(other, str):
            self.__stream_append__(other)
            return self
        else:
            raise TypeError(f"Ожидался наследник Stream или str")
    
    def __stream_rewrite__(self, value: str) -> None:
        raise NotImplementedError(f"Этот метод не разрешен в {self.__class__.__name__}")
    
    def __stream_append__(self, value: str) -> None:
        raise NotImplementedError(f"Этот метод не разрешен в {self.__class__.__name__}")
    
    def __stream_getData__(self) -> str:
        raise NotImplementedError(f"Этот метод не разрешен в {self.__class__.__name__}")

# Type variable для аннотаций
subStream = TypeVar('subStream', bound=Stream)