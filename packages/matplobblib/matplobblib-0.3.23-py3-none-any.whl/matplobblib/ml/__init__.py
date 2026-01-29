#######################################################################################################################
import re
import pandas as pd
import matplotlib.pyplot as plt
from ..forall import *
#######################################################################################################################
from .rm import *                       # Модификации линейной регрессионной модели
from .logreg import *                       # Модификации модели классификации
from .additional_funcs import *         # Дополнительные функции
from .tree import *                     # Деревья
from .svc import *                      # Классификатор методом опорных векторов
from .knn import *                       # K-nn
from .randomforrest import *            # Случайный лес
from .nbc import *                      # Наивный байесовский классификатор

pattern = r'"""\s*(.*?)\s*(?=def __init__|Args|Параметры)'

files_dict ={
    'Дополнительные функции' : AF,
    'Модификации линейной регрессионной модели': RM,
    'Модель Логистической регрессии': CM,
    'Реализация дерева решений' : TREES,
    'Классификатор методом опорных векторов' : SVCS,
    'К-ближайших соседей': KNNS,
    'Случайный лес': RF,
    'Наивный байесовский классификатор': NBC
}

names = list(files_dict.keys())
modules = list(files_dict.values())

def imports():
    return '''
    
    from scipy.integrate import quad
    import math
    import numpy a np
    import sympy
    import itertools
    sympy.init_printing(use_unicode=True,use_latex=True)
    '''
    
def enable_ppc():
    return'''
import pyperclip

#Делаем функцию которая принимает переменную text
def write(name):
    pyperclip.copy(name) #Копирует в буфер обмена информацию
    pyperclip.paste()'''
    


funcs_dicts = [
    dict([
        (task, func) for func in module
        if (task := get_task_from_func(func)) is not None
    ])
    for module in modules
]
funcs_dicts_ts = [
    dict([
        (task, func) for func in module
        if (task := get_task_from_func(func, True)) is not None
    ])
    for module in modules
]
funcs_dicts_full = [dict([(i.__name__, getsource(i)) for i in module]) for module in modules]
funcs_dicts_full_nd = [dict([(i.__name__, getsource_no_docstring(i)) for i in module]) for module in modules]


themes_list_funcs = dict([(names[i],list(funcs_dicts[i].values()) ) for i in range(len(names))]) # Название темы : список функций по теме
themes_list_dicts = dict([(names[i],funcs_dicts[i]) for i in range(len(names))])                 # Название темы : словарь по теме, где ЗАДАНИЕ: ФУНКЦИИ
themes_list_dicts_full = dict([(names[i],funcs_dicts_full[i]) for i in range(len(names))])       # Название темы : словарь по теме, где НАЗВАНИЕ ФУНКЦИИ: ТЕКСТ ФУНКЦИИ
themes_list_dicts_full_nd = dict([(names[i],funcs_dicts_full_nd[i]) for i in range(len(names))])        # Название темы : словарь по теме, где НАЗВАНИЕ ФУНКЦИИ: ТЕКСТ ФУНКЦИИ БЕЗ ДОКУМЕНТАЦИИ


# Тема -> Функция -> Задание

def description(
    dict_to_show=themes_list_funcs,
    key=None,
    show_only_keys: bool = False,
    show_keys_second_level: bool = True,
    n_symbols: int = 32,
    to_print: bool = True,
    show_doc = False):
    """
    Отображает информацию о доступных функциях и темах в модуле ML.

    Функция предоставляет несколько режимов для просмотра содержимого модуля:
    - Показать все темы и функции в них.
    - Показать функции в рамках одной темы.
    - Показать исходный код конкретной функции.

    Args:
        dict_to_show (str or dict, optional): Словарь для отображения или название темы.
            По умолчанию `themes_list_funcs`.
        key (hashable, optional): Ключ для фильтрации (например, имя функции).
        show_only_keys (bool, optional): Если True, показывать только ключи (названия тем).
            По умолчанию False.
        show_keys_second_level (bool, optional): Если True, показывать ключи второго уровня (названия функций).
            По умолчанию True.
        n_symbols (int, optional): Максимальное количество символов для описания.
            По умолчанию 32.
        to_print (bool, optional): Если True, выводит результат в консоль. Иначе возвращает строку.
            По умолчанию True.
        show_doc (bool, optional): Если True, показывает полный исходный код функции с документацией.
            По умолчанию False.

    Returns:
        str or None: Форматированная строка с информацией, если `to_print` равно False.
            В противном случае None.

    Examples:
        >>> # Показать только названия тем в модуле ML
        >>> description(show_only_keys=True)

        >>> # Показать функции и их краткое описание для темы 'Реализация дерева решений'
        >>> description('Реализация дерева решений')

        >>> # Показать исходный код класса 'DecisionTree'
        >>> description('Реализация дерева решений', key='DecisionTree', show_doc=True)

    Notes:
        - Функция использует предопределенные словари `themes_list_funcs`, `themes_list_dicts` и др.
          для доступа к метаданным функций.
        - Для корректного отображения длинных описаний используется автоматический перенос строк.
    """
    
    # Если dict_to_show - строка (название темы) и не указан конкретный ключ (key)
    if type(dict_to_show) == str and key == None:
        dict_to_show = themes_list_dicts[dict_to_show]
        dict_to_show = invert_dict(dict_to_show)
        text = ""
        length1 = 1 + max([len(x.__name__) for x in list(dict_to_show.keys())])
        
        for key in dict_to_show.keys():
            text += f'{key.__name__:<{length1}}' # Имя функции, выровненное по левому краю
            
            if not show_only_keys:
                text += ': '
                text += f'{dict_to_show[key]};\n' + ' '*(length1+2) # Описание задачи
            text += '\n'
            
        if to_print == True:
            return print(text)
        return text
    
    # Если dict_to_show - строка (название темы) и указан конкретный ключ (имя функции)
    elif type(dict_to_show) == str and key in themes_list_dicts_full[dict_to_show].keys():
        if show_doc:
            return print(themes_list_dicts_full[dict_to_show][key]) # Вывод исходного кода функции
        else:
            return print(themes_list_dicts_full_nd[dict_to_show][key]) # Вывод исходного кода функции
    
    else:
        show_only_keys = False
    text = ""
    length1 = 1 + max([len(x) for x in list(dict_to_show.keys())]) # Максимальная длина ключа первого уровня (названия темы)
    
    for key in dict_to_show.keys():
        text += f'{key:^{length1}}' # Название темы, выровненное по центру
        if not show_only_keys:
            text += ': '
            for f in dict_to_show[key]:
                text += f'{f.__name__}'
                if show_keys_second_level:
                    text += ': '
                    try:
                        # Получение описания функции из инвертированного словаря
                        func_text_len = len(invert_dict(themes_list_dicts[key])[f])
                        
                        # Форматирование описания с переносами строк и ограничением по длине
                        func_text = invert_dict(themes_list_dicts[key])[f]
                        text += func_text.replace('\n','\n'+' '*(length1 + len(f.__name__))) if func_text_len < n_symbols else func_text[:n_symbols].replace('\n','\n'+' '*(length1 + len(f.__name__)))+'...'
                    except:
                        pass # Пропуск, если описание не найдено
                text += ';\n' + ' '*(length1+2) # + '\n' + ' '*(length1+2)
        text += '\n'
        
    if to_print == True:
        return print(text)
    return text



def search(query: str, to_print: bool = True, data: str = description(n_symbols=10000, to_print=False)):
    """
    Ищет функции и классы в модуле ML по ключевым словам в их описаниях.

    Функция выполняет регистронезависимый поиск по описаниям всех доступных
    элементов и выводит найденные совпадения.

    Args:
        query (str): Строка для поиска. Может быть частью слова или фразой.
        to_print (bool, optional): Если True, результат выводится в консоль.
            Иначе возвращается в виде списка строк. По умолчанию True.
        data (str, optional): Строка с данными для поиска, обычно результат
            вызова `description(to_print=False)`. По умолчанию генерируется
            автоматически.

    Returns:
        list or None: Список найденных строк в формате "Тема : Описание",
            если `to_print` равно False. В противном случае None.

    Examples:
        >>> # Найти все, что связано с регрессией
        >>> search("регрессия")

        >>> # Найти реализации деревьев и вернуть результат в виде списка
        >>> results = search("дерево", to_print=False)
        >>> print(results)

    Notes:
        - Поиск чувствителен к структуре данных, предоставляемых функцией `description`.
        - Для полного поиска по всем описаниям `description` вызывается с `n_symbols=10000`.
    """
    # Разделение входных данных на отдельные темы
    topics = re.split(r'\n\s*\n', data)
    matches = []

    for topic_data in topics:
        # Пропуск пустых блоков тем
        if not topic_data.strip():
            continue

        topic_match = re.match(r'^\s*(.*?):', topic_data)
        if not topic_match:
            continue
        
        # Извлечение названия темы
        topic = topic_match.group(1).strip()
        # Поиск всех функций и их описаний в текущей теме
        functions = re.findall(r'(\w+)\s*:\s*([\s\S]*?)(?=\n\s*\w+\s*:|\Z)', topic_data)

        for func, description in functions:
            # Проверка наличия запроса (без учета регистра) в описании функции
            if query.lower() in description.lower():
                matches.append(f"{topic} : {description.strip()}")
    
    # Вывод результатов или их возврат списком
    if to_print:
        return print("\n".join(matches))
    return matches