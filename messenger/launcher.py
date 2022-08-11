import subprocess

process = []

while True:
    action = input('Выберите действие: q - выход , s - запустить сервер и клиенты, x - закрыть все текущие окна:')
    if action == 'q':
        break
    elif action == 's':
        clients_count = int(input('Введите количество клиентов для теста для запуска: '))
        process.append(subprocess.Popen('python server_script.py.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(clients_count):
            process.append(subprocess.Popen(f'python client.py -n test{i + 1}', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            process.pop().kill()