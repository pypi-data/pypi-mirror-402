import ujson


def draw_square(filename : str, n : int) -> None:
    with open(filename, 'w') as file:
        print('*' * n, file=file)
        print((n - 3) * ('*' + ' ' * (n - 2) + '*\n'), file=file, end='')
        print('*' * n, file=file, end='')


def draw_triangle(filename : str, n : int) -> None:
    '''
    n must be positive number
    :param filename:
    :param n:
    :return:
    '''
    with open(filename, 'w') as file:
        print('*\n', end='', file=file)
        for i in range(n - 2):
            print('*' + i * ' ' + '*\n', end='', file=file)
        for i in range(1, n):
            print('*' + (n - i - 1) * ' ' + '*\n', end='', file=file)
        print('*\n', end='', file=file)


def write_ujson(filename : str, data : dict) -> None:
    with open(filename, 'w') as file:
        ujson.dump(data, file, indent=2)


draw_square('salom.sq', 10)
draw_triangle('salom', 20)
write_ujson('salom.json', {'xoshim': 'botir'})