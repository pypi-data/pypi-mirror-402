__all__ = ['E', 'Hi', 'PalmTable','M_M_V_L_an', 'M_M_V_L_im', 'EngsetTable', 'Mi_M_V_L_an', 'VM_M_V_L_PRA_an', 'M_G_V_L_an', 'ErlangFormula2', 'M_M_V_W_FF_R_an', 'M_M_V_W_FF_R_im', 'VM_VMl_V_L_an', 'VM_VMl_VDg_L_an', 'VM_VMl_VDg_L_im']

import ctypes
import os
import site
site_packages_path = site.getsitepackages()[0]
dll_name = './Lib/site-packages/teletraffic/libTeletrafficAll.dll'
dll_path = os.path.join(site_packages_path, dll_name)
lib1 = ctypes.CDLL(dll_path)

def E (z, v):
    '''
    B-формула Эрланга
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    Результат:
    p - вероятность потери заявки
    '''
    lib1.E.argtypes = [ctypes.c_int, ctypes.c_double]
    lib1.E.restype = ctypes.c_double
    p1 = lib1.E(v, z)
    return p1

def Hi (z, v, d):
    '''
    Формула Пальма-Якобеуса
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    d - количество занятых обслуживающих приборов 
    Результат:
    p - вероятность потери заявки
    '''
    lib1.Hi.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_int]
    lib1.Hi.restype = ctypes.c_double
    p1 = lib1.Hi(v, z, d)
    return p1

def PalmTable (z, v):
    '''
    Таблица Пальма
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    Результат:
    p - вероятность потери заявки
    '''
    lib1.PalmTable.argtypes = [ctypes.c_int, ctypes.c_double]
    lib1.PalmTable.restype = ctypes.c_double
    p1 = lib1.PalmTable(v, z)
    return p1

def MMVLannew(v, z):
    lib1.M_M_V_L_an.argtypes = [ctypes.c_int, ctypes.c_double]
    lib1.M_M_V_L_an.restype = ctypes.c_char_p
    arr = lib1.M_M_V_L_an(v, z).decode().split()
    arr = [float(x) for x in arr]
    return arr

class M_M_V_L_an:
    '''
    Аналитическая модель M_M_V_L в символике Кендалла-Башарина
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    Свойства-геттеры:
    loss - вероятность потери заявки
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели M_M_V_L
    '''
    def __init__(self, z, v):
        self.__Arr = MMVLannew(v, z)
    @property
    def loss(self):
        return self.__Arr[0]
    @property
    def serv(self):
        return self.__Arr[1]
    def show(self):
        print("Характеристики качества обслуживания модели M_M_V_L_an")
        print(f"Вероятность потерь: {self.loss}\nИнтенсивность обслуженной нагрузки: {self.serv}")

def MMVLimnew(z, v, nz, seed):
    lib1.M_M_V_L_im.argtypes = [ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib1.M_M_V_L_im.restype = ctypes.c_char_p
    arr = lib1.M_M_V_L_im(z, v, nz, seed).decode().split()
    arr = [float(x) for x in arr]
    return arr

class M_M_V_L_im:
    '''
    Имитационная модель M_M_V_L в символике Кендалла-Башарина
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    nz - количество заявок
    seed - начальное состояние датчика случайных чисел (по умолчанию - 0)
    Свойства-геттеры:
    loss - вероятность потери заявки
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания имитационной модели M_M_V_L
    '''
    def __init__(self, z, v, nz, seed = 0):
        self.__Arr = MMVLimnew(z, v, nz, seed)
    @property
    def loss(self):
        return self.__Arr[0]
    @property
    def serv(self):
        return self.__Arr[1]
    def show(self):
        print("Характеристики качества обслуживания модели M_M_V_L_im")
        print(f"Вероятность потерь: {self.loss}\nИнтенсивность обслуженной нагрузки: {self.serv}")
    
def EngsetTable(z, n, v):
    '''
    Таблица Энгсета
    Аргументы: 
    z - поступающая нагрузка от одного пользователя, [Эрл]
    n - количество пользователей
    v - количество обслуживающих приборов 
    Результат:
    p - вероятность потери заявки
    '''
    lib1.EngsetTable.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double]
    lib1.EngsetTable.restype = ctypes.c_double
    p1 = lib1.EngsetTable(n, v, z)
    return p1

def MiMVLannew(n, v, z):
    lib1.Mi_M_V_L_an.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double]
    lib1.Mi_M_V_L_an.restype = ctypes.c_char_p
    arr = lib1.Mi_M_V_L_an(n, v, z).decode().split()
    arr = [float(x) for x in arr]
    return arr

class Mi_M_V_L_an:
    '''
    Аналитическая модель Mi_M_V_L в символике Кендалла-Башарина
    Аргументы: 
    z - поступающая нагрузка от одного пользователя, [Эрл]
    n - количество пользователей
    v - количество обслуживающих приборов 
    Свойства-геттеры:
    loss - вероятность потери заявки
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели Mi_M_V_L
    '''
    def __init__(self, z, n, v):
        self.__Arr = MiMVLannew(n, v, z)
    @property
    def loss(self):
        return self.__Arr[0]
    @property
    def serv(self):
        return self.__Arr[1]
    def show(self):
        print("Характеристики качества обслуживания модели Mi_M_V_L_an")
        print(f"Вероятность потерь по вызовам: {self.loss}\nИнтенсивность обслуженной нагрузки: {self.serv}")

def MMVLPRAannew(v, arrz):
    ctypes.c_double_array = ctypes.c_double * len(arrz)
    lib1.M_M_V_L_PRA_an.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double_array)]
    lib1.M_M_V_L_PRA_an.restype = ctypes.c_char_p
    arrz = (ctypes.c_double_array)(*arrz)
    arr = lib1.M_M_V_L_PRA_an(len(arrz), v, ctypes.POINTER(ctypes.c_double_array)(arrz)).decode().split()
    arr = [float(x) for x in arr]
    return arr

class VM_M_V_L_PRA_an:
    '''
    Аналитическая модель VM_M_V_L_PRA в символике Кендалла-Башарина
    Аргументы: 
    vz - вектор интенсивностей поступающей нагрузки от группы пользователей каждой категории, [Эрл]
    v - количество обслуживающих приборов 
    Свойства-геттеры:
    vloss - вектор вероятностей потерь заявок каждой категории пользователей
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели VM_M_V_L_PRA
    '''
    def __init__(self, vz, v):
        self.__Arr = MMVLPRAannew(v, vz)
        self.__Arrz = vz
    @property
    def vloss(self):
        list1 = list()
        for i in range(0, len(self.__Arr), 2):
            list1.append(self.__Arr[i])
        return list1
    @property
    def serv(self):
        list2 = list()
        for i in range(1, len(self.__Arr), 2):
            list2.append(self.__Arr[i])
        return list2
    def show(self):
        print("Характеристики качества обслуживания модели VM_M_V_L_PRA_an")
        i = 0
        j = 0
        while i < (2 * len(self.__Arrz)):
            print(f"Вероятность потерь для абонентов {j + 1} категории: {self.__Arr[i]}\nИнтенсивность обслуженной нагрузки для абонентов {j + 1} категории: {self.__Arr[i + 1]}")
            i += 2
            j += 1

def MGVLannew(ts, tbr, trec, v, lmb):
    lib1.M_G_V_L_an.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int]
    lib1.M_G_V_L_an.restype = ctypes.c_char_p
    arr = lib1.M_G_V_L_an(ts, tbr, trec, v, lmb).decode().split()
    arr = [float(x) for x in arr]
    return arr

class M_G_V_L_an:
    '''
    Аналитическая модель M_G_V_L в символике Кендалла-Башарина
    Аргументы: 
    ts - среднее время обслуживания
    tbr - среднее время исправной работы обслуживающего прибора
    trec - среднее время восстановления обслуживающего прибора
    lmb - интенсивность поступления заявок
    v - количество обслуживающих приборов 
    Свойства-геттеры:
    loss - вероятность потери заявки
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели M_G_V_L
    '''
    def __init__(self, ts, tbr, trec, lmb, v):
        self.__Arr = MGVLannew(ts, tbr, trec, v, lmb)
    @property
    def loss(self):
        return self.__Arr[0]
    @property
    def serv(self):
        return self.__Arr[1]
    def show(self):
        print("Характеристики качества обслуживания модели M_G_V_L_an")
        print(f"Вероятность потерь: {self.loss}\nИнтенсивность обслуженной нагрузки: {self.serv}")

def ErlangFormula2(z, v):
    '''
    Вторая формула Эрланга
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    Результат:
    p - вероятность потери заявки
    '''
    lib1.ErlangFormula2.argtypes = [ctypes.c_int, ctypes.c_double]
    lib1.ErlangFormula2.restype = ctypes.c_double
    p1 = lib1.ErlangFormula2(v, z)
    return p1

def MMVWFFRannew(ta, ts, v, z):
    lib1.M_M_V_W_FF_R_an.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double]
    lib1.M_M_V_W_FF_R_an.restype = ctypes.c_char_p
    arr = lib1.M_M_V_W_FF_R_an(ta, ts, v, z).decode().split()
    arr = [float(x) for x in arr]
    return arr

class M_M_V_W_FF_R_an:
    '''
    Аналитическая модель M_M_V_W_FF_R в символике Кендалла-Башарина
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    ta - допустимое время ожидания
    ts - среднее время обслуживания
    Свойства-геттеры:
    wait - вероятность ожидания
    over_wait - вероятность ожидания свыше допустимого времени
    avr_time - среднее время ожидания
    avr_time_wait - среднее время ожидания только для ожидающих заявок
    queue - вероятность наличия очереди
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели M_M_V_W_FF_R
    '''
    def __init__(self, z, v, ta, ts):
        self.__Arr = MMVWFFRannew(ta, ts, v, z)
    @property
    def wait(self):
        return self.__Arr[0]
    @property
    def over_wait(self):
        return self.__Arr[1]
    @property
    def avr_time(self):
        return self.__Arr[2]
    @property
    def avr_time_wait(self):
        return self.__Arr[3]
    @property
    def queue(self):
        return self.__Arr[4]
    def show(self):
        print("Характеристики качества обслуживания модели M_M_V_W_FF_R_an")
        print("Основные характеристики")
        print(f"Вероятность ожидания: {self.wait}\nВероятность ожидания больше допустимого времени: {self.over_wait}")
        print("Дополнительные характеристики")
        print(f"Среднее время ожидания для всех вызовов: {self.avr_time}\nСреднее время ожидания для ждущих вызовов: {self.avr_time_wait}\nСредняя длина очереди: {self.queue}")

def MMVWFFRimnew(z, v, nz, ta, seed):
    lib1.M_M_V_W_FF_R_im.argtypes = [ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_int]
    lib1.M_M_V_W_FF_R_im.restype = ctypes.c_char_p
    arr = lib1.M_M_V_W_FF_R_im(z, v, nz, ta, seed).decode().split()
    arr = [float(x) for x in arr]
    return arr

class M_M_V_W_FF_R_im:
    '''
    Имитационная модель M_M_V_W_FF_R в символике Кендалла-Башарина
    Аргументы: 
    z - поступающая нагрузка от группы пользователей, [Эрл]
    v - количество обслуживающих приборов 
    nz - количество заявок
    ta - допустимое время ожидания (по умолчанию - 0)
    seed - начальное состояние датчика случайных чисел (по умолчанию - 0)
    Свойства-геттеры:
    wait - вероятность ожидания
    over_wait - вероятность ожидания свыше допустимого времени
    avr_time - среднее время ожидания
    avr_time_wait - среднее время ожидания только для ожидающих заявок
    queue - вероятность наличия очереди
    Методы:
    show - вывод характеристик качества обслуживания имитационной модели M_M_V_W_FF_R
    '''
    def __init__(self, z, v, nz, ta = 0.0, seed = 0):
        self.__Arr = MMVWFFRimnew(z, v, nz, ta, seed)
    @property
    def wait(self):
        return self.__Arr[0]
    @property
    def over_wait(self):
        return self.__Arr[1]
    @property
    def avr_time(self):
        return self.__Arr[2]
    @property
    def avr_time_wait(self):
        return self.__Arr[3]
    @property
    def queue(self):
        return self.__Arr[4]
    def show(self):
        print("Характеристики качества обслуживания модели M_M_V_W_FF_R_im")
        print("Основные характеристики")
        print(f"Вероятность ожидания: {self.wait}\nВероятность ожидания больше допустимого времени: {self.over_wait}")
        print("Дополнительные характеристики")
        print(f"Среднее время ожидания для всех вызовов: {self.avr_time}\nСреднее время ожидания для ждущих вызовов: {self.avr_time_wait}\nСредняя длина очереди: {self.queue}")

def VMVMlVLannew(vz, vb, kc, f):
    ctypes.c_double_array = ctypes.c_double * len(vz)
    vz = (ctypes.c_double_array)(*vz)
    vb = (ctypes.c_double_array)(*vb)
    lib1.VM_VMl_V_L_an.argtypes = [ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.c_int]
    lib1.VM_VMl_V_L_an.restype = ctypes.c_char_p
    arr = lib1.VM_VMl_V_L_an(ctypes.POINTER(ctypes.c_double_array)(vz), len(vz), ctypes.POINTER(ctypes.c_double_array)(vb), kc, f).decode().split()
    arr = [float(x) for x in arr]
    return arr

class VM_VMl_V_L_an:
    '''
    Аналитическая модель VM_VMl_V_L в символике Кендалла-Башарина (мультисервисная система обслуживания с полнодоступным включением групп единиц канального ресурса)
    Аргументы: 
    vz - вектор интенсивностей поступающих потоков заявок, [Эрл]
    vb - вектор требований к числу ЕКР для обслуживания заявок каждого потока, [ЕКР]
    kc - количество нагрузочных групп
    f - емкость нагрузочной группы, [ЕКР]
    Свойства-геттеры:
    vloss - вектор вероятностей потерь заявок каждого потока
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели VM_VMl_V_L
    '''
    def __init__(self, vz, vb, kc, f):
        self.__Arr = VMVMlVLannew(vz, vb, kc, f)
    @property
    def vloss(self):
        list1 = list()
        for i in range(0, len(self.__Arr), 2):
            list1.append(self.__Arr[i])
        return list1
    @property
    def serv(self):
        list2 = list()
        for i in range(1, len(self.__Arr), 2):
            list2.append(self.__Arr[i])
        return list2
    def show(self):
        print("Характеристики качества обслуживания модели VM_VMl_V_L_an")
        i = 0
        j = 1
        while i < len(self.__Arr):
            print(f"Вероятность потерь для {j} потока: {self.__Arr[i]}\nИнтенсивность обслуженной нагрузки для {j} потока: {self.__Arr[i + 1]}")
            i += 2
            j += 1

def VMVMlVDgLannew(vz, vb, kc, f, kd):
    ctypes.c_double_array = ctypes.c_double * len(vz)
    vz = (ctypes.c_double_array)(*vz)
    vb = (ctypes.c_double_array)(*vb)
    lib1.VM_VMl_VDg_L_an.argtypes = [ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib1.VM_VMl_VDg_L_an.restype = ctypes.c_char_p
    arr = lib1.VM_VMl_VDg_L_an(ctypes.POINTER(ctypes.c_double_array)(vz), len(vz), ctypes.POINTER(ctypes.c_double_array)(vb), kc, f, kd).decode().split()
    arr = [float(x) for x in arr]
    return arr

class VM_VMl_VDg_L_an:
    '''
    Аналитическая модель VM_VMl_VDg_L в символике Кендалла-Башарина (мультисервисная система обслуживания с неполнодоступным включением групп единиц канального ресурса)
    Аргументы: 
    vz - вектор интенсивностей поступающих потоков заявок, [Эрл]
    vb - вектор требований к числу ЕКР для обслуживания заявок каждого потока, [ЕКР]
    kc - количество нагрузочных групп
    f - емкость нагрузочной группы, [ЕКР]
    kd - количество нагрузочных групп, доступных каждому потоку заявок
    Свойства-геттеры:
    vloss - вектор вероятностей потерь заявок каждого потока
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания аналитической модели VM_VMl_VDg_L
    '''
    def __init__(self, vz, vb, kc, f, kd):
        self.__Arr = VMVMlVDgLannew(vz, vb, kc, f, kd)
    @property
    def vloss(self):
        list1 = list()
        for i in range(0, len(self.__Arr), 2):
            list1.append(self.__Arr[i])
        return list1
    @property
    def serv(self):
        list2 = list()
        for i in range(1, len(self.__Arr), 2):
            list2.append(self.__Arr[i])
        return list2
    def show(self):
        print("Характеристики качества обслуживания модели VM_VMl_VDg_L_an")
        i = 0
        j = 1
        while i < len(self.__Arr):
            print(f"Вероятность потерь для {j} потока: {self.__Arr[i]}\nИнтенсивность обслуженной нагрузки для {j} потока: {self.__Arr[i + 1]}")
            i += 2
            j += 1

def VMVMlVDgLimnew(vz, vb, kc, f, kd, n_з, СтрЗанСвКан):
    ctypes.c_double_array = ctypes.c_double * len(vz)
    Str1 = СтрЗанСвКан.encode()
    vz = (ctypes.c_double_array)(*vz)
    vb = (ctypes.c_double_array)(*vb)
    lib1.VM_VMl_VDg_L_im.argtypes = [ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.POINTER(ctypes.c_double_array), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    lib1.VM_VMl_VDg_L_im.restype = ctypes.c_char_p
    arr = lib1.VM_VMl_VDg_L_im(ctypes.POINTER(ctypes.c_double_array)(vz), len(vz), ctypes.POINTER(ctypes.c_double_array)(vb), kc, f, kd, n_з, Str1).decode().split()
    arr = [float(x) for x in arr]
    return arr

class VM_VMl_VDg_L_im:
    '''
    Имитационная модель VM_VMl_VDg_L в символике Кендалла-Башарина (мультисервисная система обслуживания с неполнодоступным включением групп единиц канального ресурса)
    Аргументы: 
    vz - вектор интенсивностей поступающих потоков заявок, [Эрл]
    vb - вектор требований к числу ЕКР для обслуживания заявок каждого потока, [ЕКР]
    kc - количество нагрузочных групп
    f - емкость нагрузочной группы, [ЕКР]
    kd - количество нагрузочных групп, доступных каждому потоку заявок
    nz - количество заявок
    СтрЗанСвКан - стратегия занятия свободного канального ресурса ('МаксСвоб', 'МинСвоб', 'ПервСвоб')
    Свойства-геттеры:
    vloss - вектор вероятностей потерь заявок каждого потока
    serv - обслуженная нагрузка, [Эрл]
    Методы:
    show - вывод характеристик качества обслуживания имитационной модели VM_VMl_VDg_L
    '''
    def __init__(self, vz, vb, kc, f, kd, nz, СтрЗанСвКан):
        self.__Arr = VMVMlVDgLimnew(vz, vb, kc, f, kd, nz, СтрЗанСвКан)
    @property
    def vloss(self):
        list1 = list()
        for i in range(0, len(self.__Arr), 2):
            list1.append(self.__Arr[i])
        return list1
    @property
    def serv(self):
        list2 = list()
        for i in range(1, len(self.__Arr), 2):
            list2.append(self.__Arr[i])
        return list2
    def show(self):
        print("Характеристики качества обслуживания модели VM_VMl_VDg_L_im")
        i = 0
        j = 1
        while i < len(self.__Arr):
            print(f"Вероятность потерь для {j} потока: {self.__Arr[i]}\nИнтенсивность обслуженной нагрузки для {j} потока: {self.__Arr[i + 1]}")
            i += 2
            j += 1