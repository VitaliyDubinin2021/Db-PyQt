import logging
logger = logging.getLogger('server_dist')

class Port:
    def __set__(self, instance, value):
        if not 2246 < value < 45271:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 2246 до 45271!')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

