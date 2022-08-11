import sys
import json
import socket
import time
import dis
import argparse
import logging
import threading
import logs.config_client_log
from common.variables import *
from common.utils import *
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from decorators import log
from metaclasses import ClientMaker


logger = logging.getLogger('client_dist')


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()


    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        to = input('Пожалуйста введите получателя сообщения: ')
        message = input('Пожалуйста введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Был сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            logger.info(f'Было отправлено сообщение для пользователя {to}')
        except:
            logger.critical('Было потеряно соединение с сервером!')
            exit(1)

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print('Завершение соединения!')
                logger.info('Завершение работы по команде пользователя!')
                time.sleep(0.5)
                break
            else:
                print('Команда была не распознана! Пожалуйста попробуйте снова! help - вывести все поддерживаемые команды!')

    def print_help(self):
        print('Поддерживаемые команды: ')
        print('message - отправить сообщение!')
        print('help - вывести подсказки к командам')
        print('exit - выход из программы!')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\n Получено сообщение от пользователя с именем {message[SENDER]}:\n {message[MESSAGE_TEXT]}')
                    logger.info(f'Получено сообщение от пользователя с именем {message[SENDER]}:\n {message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Было получено не корректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                logger.error(f'Не удалось произвести декодировку полученного сообщения!')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Было потеряно соединение с сервером!')
                break


@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug(f'Было сформировано {PRESENCE} сообщение для пользователя с именем {account_name}')
    return out


@log
def process_response_ans(message):
    logger.debug(f'Разбор сообщения-приветствия от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 2246 < server_port < 45271:
        logger.critical(
            f'Была произведена попытка запуска клиента с неправильным номером порта: {server_port}. Допустимы адреса с 2246 до 45271!')
        exit(1)

    return server_address, server_port, client_name


def main():
    print('Клиентский модуль! Консольный мессенджер!')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Пожалуйста введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен со следующим именем: {client_name}')

    logger.info(
        f'Запущен клиент со следующими парамертами - адрес сервера: {server_address} , '
        f'порт: {server_port}, с именем пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        logger.info(f'Было установлено соединение с сервером! Ответ сервера: {answer}')
        print(f'Было установлено соединение с сервером!')
    except json.JSONDecodeError:
        logger.error('Не получилось декодировать полученную JSON-строку!')
        exit(1)
    except ServerError as error:
        logger.error(f'В процессе установки соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу с именем {server_address}:{server_port}, '
            f'Был отвергнут запрос на подключение!')
        exit(1)
    else:
        module_reciver = ClientReader(client_name, transport)
        module_reciver.daemon = True
        module_reciver.start()
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Были запущены процессы!')
        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
