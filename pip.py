import tkinter as tk
from tkinter import messagebox
import random
from collections import Counter

# Размеры поля и параметры
BOARD_SIZE = 10
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
CELL_SIZE = 30

ai_forbidden = set()  # Клетки, в которые ИИ не должен стрелять


def create_board() -> list[list[str]]:
    """
    Создаёт и возвращает пустое игровое поле размером BOARD_SIZE x BOARD_SIZE.
    Клетки обозначаются символом '~'.
    """
    return [['~'] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def draw_board(canvas, board, show_ships, hover_coords=None, hover_valid=True):
    """
        Отрисовывает игровое поле на холсте (canvas).

        Аргументы:
            canvas (tk.Canvas): Холст, на котором рисуется поле.
            board (list[list[str]]): Состояние поля (матрица 10x10 со значениями '~', 'S', 'X', 'O').
            show_ships (bool): Показывать ли корабли на поле (True — для поля игрока).
            hover_coords (list[tuple[int, int]]): Координаты клеток для подсветки при наведении.
            hover_valid (bool): Можно ли здесь разместить корабль (определяет цвет подсветки).
    """
    canvas.delete("all")
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            cell = board[x][y]
            color = 'white'
            if cell == 'S' and show_ships:
                color = 'navy'
            elif cell == 'X':
                color = 'red'
            elif cell == 'O':
                color = 'gray'
            canvas.create_rectangle(y * CELL_SIZE, x * CELL_SIZE, (y + 1) * CELL_SIZE, (x + 1) * CELL_SIZE,
                                    fill=color, outline='black')
    if hover_coords:
        color = 'lightgreen' if hover_valid else 'lightcoral'
        for x, y in hover_coords:
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                canvas.create_rectangle(y * CELL_SIZE, x * CELL_SIZE, (y + 1) * CELL_SIZE, (x + 1) * CELL_SIZE,
                                        fill=color, outline='black')


def toggle_orientation():
    """
    Переключает ориентацию размещения корабля между горизонтальной и вертикальной.
    """
    global orientation
    orientation = 'V' if orientation == 'H' else 'H'
    update_ship_size_label()


def show_instructions():
    """
    Показывает окно с правилами игры и инструкцией по управлению.
    Вызывается при нажатии на кнопку "Правила и инструкция".
    """
    rules = (
        "Правила игры:\n"
        "- Расставьте свои корабли на поле, они не должны касаться друг друга даже по диагонали.\n"
        "- После расстановки начинается бой: вы и ИИ стреляете по очереди.\n"
        "- Попадание обозначается красным, промах — серым.\n"
        "- Цель: первым уничтожить все корабли противника.\n\n"
        "Управление:\n"
        "- ЛКМ по синему полю — разместить корабль.\n"
        "- Кнопка 'Повернуть корабль' — сменить ориентацию.\n"
        "- ЛКМ по серому полю — стрелять по врагу во время боя."
    )
    messagebox.showinfo("Инструкция", rules)


def update_ship_size_label():
    """
    Обновляет текст с размером текущего корабля и количеством оставшихся кораблей такого размера.
    Использует Counter для подсчёта уже размещённых кораблей данного размера.
    """
    if ship_index < len(SHIP_SIZES):
        size = SHIP_SIZES[ship_index]
        remaining = Counter(SHIP_SIZES)[size] - SHIP_SIZES[:ship_index].count(size)
        if orientation == 'H':
            lbl_status.config(text=f"Размер: 1x{size} | Осталось: {remaining}")
        else:
            lbl_status.config(text=f"Размер: {size}x1 | Осталось: {remaining}")


def on_player_board_click(event):
    """
    Обрабатывает клик по полю игрока. Если возможно, размещает корабль в указанной позиции.
    При завершении расстановки переводит игру в фазу боя.

    event: Событие мыши с координатами клика.
    """
    global ship_index, phase
    if phase != 'placement':
        return
    x, y = event.y // CELL_SIZE, event.x // CELL_SIZE
    size = SHIP_SIZES[ship_index]
    if can_place_ship(player_board, x, y, size, orientation):
        place_ship(player_board, x, y, size, orientation)
        ship_index += 1
        if ship_index < len(SHIP_SIZES):
            update_ship_size_label()
        draw_board(canvas_player, player_board, True)
        if ship_index >= len(SHIP_SIZES):
            phase = 'battle'
            lbl_status.config(text="Бой! Кликайте по вражескому полю")
            btn_rotate.grid_forget()
            btn_info.grid(columnspan=2)
            messagebox.showinfo("Бой начинается!", "Все корабли размещены. Начинается бой!")
    else:
        messagebox.showwarning("Ошибка", "Корабль нельзя ставить вплотную или за пределы поля!")


def on_player_board_hover(event):
    """
    Обрабатывает наведение курсора мыши на поле игрока во время расстановки кораблей.
    Показывает подсветку возможного размещения корабля (если допустимо).

    event: Событие мыши, используется для получения координат.
    """
    if phase != 'placement' or ship_index >= len(SHIP_SIZES):
        return
    x, y = event.y // CELL_SIZE, event.x // CELL_SIZE
    size = SHIP_SIZES[ship_index]
    dx, dy = (0, 1) if orientation == 'H' else (1, 0)
    coords = [(x + i * dx, y + i * dy) for i in range(size)]
    valid = can_place_ship(player_board, x, y, size, orientation)
    draw_board(canvas_player, player_board, True, coords, valid)


def on_enemy_board_click(event):
    """
    Обрабатывает клик по полю врага во время боя. Выполняет выстрел, проверяет попадание
    и вызывает ход противника, если игра не окончена.

    Аргументы:
        event: Событие мыши с координатами выстрела.
    """
    global phase
    if phase != 'battle':
        return
    x, y = event.y // CELL_SIZE, event.x // CELL_SIZE
    if enemy_board[x][y] in ('X', 'O'):
        return
    if enemy_ships[x][y] == 'S':
        enemy_board[x][y] = 'X'
    else:
        enemy_board[x][y] = 'O'
    draw_board(canvas_enemy, enemy_board, False)
    if check_victory(enemy_board, enemy_ships):
        messagebox.showinfo("Победа!", "Вы победили!")
        root.quit()
        return
    canvas_enemy.unbind("<Button-1>")
    root.after(random.randint(300, 700), delayed_enemy_turn)


def delayed_enemy_turn():
    """Вызов хода ИИ с задержкой"""
    enemy_turn()
    draw_board(canvas_player, player_board, True)
    if check_victory(player_board, player_board):
        messagebox.showinfo("Поражение", "Противник победил!")
        root.quit()
        return
    canvas_enemy.bind("<Button-1>", on_enemy_board_click)


def enemy_turn():
    """
    Ход ИИ с добиванием кораблей.
    Выполняет выстрел с учётом предыдущих попаданий, если они были.
    """
    global ai_targets
    if ai_targets:
        x, y = smart_ai_target()
    else:
        x, y = random_ai_target()
    if player_board[x][y] == 'S':
        player_board[x][y] = 'X'
        for target in ai_targets:
            if any(abs(x - tx) + abs(y - ty) == 1 for tx, ty in target):
                target.append((x, y))
                break
        else:
            ai_targets.append([(x, y)])
        for target in ai_targets:
            if is_sunk(player_board, target):
                mark_as_sunk(target)
                ai_targets.remove(target)
    else:
        player_board[x][y] = 'O'


def smart_ai_target():
    """
    Стратегия ИИ: пытается стрелять рядом с предыдущими попаданиями.
    Если вокруг нет подходящих клеток — стреляет случайно.
    """
    for target in ai_targets:
        if len(target) == 1:
            x, y = target[0]
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if is_valid_target(nx, ny):
                    return (nx, ny)
        else:
            target.sort()
            (x1, y1), (x2, y2) = target[0], target[1]
            dx, dy = x2 - x1, y2 - y1
            for i in [1, -1]:
                nx = target[-1][0] + i * dx
                ny = target[-1][1] + i * dy
                if is_valid_target(nx, ny):
                    return (nx, ny)
    return random_ai_target()


def is_valid_target(x, y):
    """
    Проверяет, можно ли стрелять в указанную клетку:
    - в пределах поля
    - не стреляли туда раньше
    - не входит в список запретных клеток (вокруг потопленных)
    """
    return (
        0 <= x < BOARD_SIZE and
        0 <= y < BOARD_SIZE and
        player_board[x][y] not in ('X', 'O') and
        (x, y) not in ai_forbidden
    )


def is_sunk(board, coords):
    """
       Проверяет, потоплен ли корабль.

       - Функция получает список координат попаданий (coords) по одному кораблю.
       - Вокруг каждой из этих координат проверяются соседние клетки.
       - Если рядом с одним из попаданий всё ещё есть клетка с 'S', значит корабль ещё не добит.

       Аргументы:
           board (list[list[str]]): Игровое поле игрока, где размещены корабли ('S') и отмечены попадания.
           coords (list[tuple[int, int]]): Координаты всех попаданий по одному кораблю.

       Возвращает:
           bool: True, если рядом с попаданиями не осталось ни одной части корабля ('S')
       """
    for x, y in coords:
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if board[nx][ny] == 'S':
                    return False
    return True


def mark_as_sunk(coords):
    """
    После потопления корабля — добавляет клетки вокруг в список запретных для ИИ выстрелов.
    """
    global ai_forbidden
    for x, y in coords:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    ai_forbidden.add((nx, ny))


def random_ai_target():
    """
    Возвращает координаты случайного выстрела по полю игрока,
    исключая клетки, где уже стреляли и клетки рядом с попаданиями.
    """
    while True:
        x, y = random.randint(0, 9), random.randint(0, 9)
        if is_valid_target(x, y):
            return (x, y)


def can_place_ship(board, x, y, size, orientation):
    """
    Проверяет, можно ли разместить корабль на поле с учётом границ и правила "не впритык".

    Аргументы:
        board (list[list[str]]): Поле размещения.
        x (int): Стартовая строка.
        y (int): Стартовый столбец.
        size (int): Длина корабля.
        orientation (str): 'H' — горизонтально, 'V' — вертикально.

    Возвращает:
        bool: True, если размещение допустимо.
    """
    dx, dy = (0, 1) if orientation == 'H' else (1, 0)
    coords = [(x + i * dx, y + i * dy) for i in range(size)]
    for cx, cy in coords:
        if not (0 <= cx < BOARD_SIZE and 0 <= cy < BOARD_SIZE):
            return False
        if board[cx][cy] != '~':
            return False
    for cx, cy in coords:
        for nx in range(cx - 1, cx + 2):
            for ny in range(cy - 1, cy + 2):
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if board[nx][ny] == 'S' and (nx, ny) not in coords:
                        return False
    return True


def place_ship(board, x, y, size, orientation):
    """
    Размещает корабль на поле по указанным координатам и ориентации.

    Аргументы:
        board (list[list[str]]): Игровое поле.
        x (int): Стартовая строка.
        y (int): Стартовый столбец.
        size (int): Длина корабля.
        orientation (str): Ориентация ('H' или 'V').
    """
    for i in range(size):
        if orientation == 'H':
            board[x][y + i] = 'S'
        else:
            board[x + i][y] = 'S'


def place_enemy_ships():
    """
    Случайным образом размещает все корабли ИИ на его поле,
    соблюдая правила и не допуская пересечений или касаний.
    """
    for size in SHIP_SIZES:
        placed = False
        while not placed:
            x, y = random.randint(0, 9), random.randint(0, 9)
            orient = random.choice(['H', 'V'])
            if can_place_ship(enemy_ships, x, y, size, orient):
                place_ship(enemy_ships, x, y, size, orient)
                placed = True


def check_victory(board, ship_board):
    """
    Проверяет победу: возвращает True, если все корабли на ship_board были подбиты на board.

    Аргументы:
        board: Текущее состояние поля (где видны попадания 'X').
        ship_board: Поле с размещёнными кораблями ('S' показывает расположение).

    Возвращает:
        bool: True — если все клетки с 'S' на ship_board перекрыты 'X' на board.
    """
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if ship_board[x][y] == 'S' and board[x][y] != 'X':
                return False
    return True


# Инициализация игры
root = tk.Tk()
root.title("Морской бой")
root.resizable(False, False)

player_board = create_board()
enemy_board = create_board()
enemy_ships = create_board()
orientation = 'H'
ship_index = 0
phase = 'placement'
ai_targets = []

# Создание интерфейса
canvas_player = tk.Canvas(root, width=BOARD_SIZE * CELL_SIZE, height=BOARD_SIZE * CELL_SIZE, bg='lightblue')
canvas_enemy = tk.Canvas(root, width=BOARD_SIZE * CELL_SIZE, height=BOARD_SIZE * CELL_SIZE, bg='lightgray')
canvas_player.grid(row=0, column=0, padx=10, pady=10)
canvas_enemy.grid(row=0, column=1, padx=10, pady=10)

canvas_player.bind("<Button-1>", on_player_board_click)
canvas_player.bind("<Motion>", on_player_board_hover)
canvas_enemy.bind("<Button-1>", on_enemy_board_click)

btn_rotate = tk.Button(root, text="Повернуть корабль", command=toggle_orientation)
btn_rotate.grid(row=1, column=0, sticky="ew", padx=10)

btn_info = tk.Button(root, text="Правила и инструкция", command=show_instructions)
btn_info.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

lbl_status = tk.Label(root, text="")
lbl_status.grid(row=1, column=1, sticky="ew", padx=10)

update_ship_size_label()
draw_board(canvas_player, player_board, True)
draw_board(canvas_enemy, enemy_board, False)
place_enemy_ships()

root.mainloop()  # Запуск приложения
