import dis
from pprint import pprint


class ServerMaker(type):
    def __init__(cls, clsname, bases, clsdict):

        methods = []
        methods_2 = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods_2:
                            methods_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        print(20*'-', 'methods', 20*'-')
        pprint(methods)
        print(20*'-', 'methods_2', 20*'-')
        pprint(methods_2)
        print(20*'-', 'attrs', 20*'-')
        pprint(attrs)
        print(50*'-')
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе!')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета!')
        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода!')
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, которые работают с сокетами!')
        super().__init__(clsname, bases, clsdict)

