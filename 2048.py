import curses
from random import randrange, choice
from collections import defaultdict

actions = ['Up','Left','Down','Right','Restart','Exit']
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']       #curses中的getch必须用ASCII 形式，所以使用ord函数
actions_dict = dict(zip(letter_codes, actions * 2))     #将键盘输入与操作对应起来形成dict

def get_user_action(keyboard):      #获取用户键盘输入
    char = 'N'
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]   #返回actions中的命令


def transpose(field):       #转置，将列变成行
    return [list(row) for row in zip(*field)]

def invert(field):      #翻转，将每行都翻转
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height = 4, width = 4, win = 2048):
        self.height = height
        self.width = width
        self.win_value = 2048
        self.score = 0
        self.highscore = 0
        self.reset()    #棋盘重置

    def reset(self):    #重置棋盘
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):      #棋盘走一步，可以通过矩阵进行转置与逆转置，直接从左移得到其他三个方向的操作
        def move_row_left(row):     #一行向左合并
            def tighten(row):   #把零散的非零单元挤到一起
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range (len(row) - len(new_row))]
                return new_row

            def merge(row):     #对邻近元素进行合并
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i+1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)  
                return new_row
            #先挤到一块再合并再挤到一块
            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(firld)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):       #判断输赢
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):      #全部不能移动则gameover
        return not any(self.move_is_possible(move) for move in actions)


    def draw(self, screen):     #绘制游戏界面

        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '    (R)Restart (Q)Exit'
        gameover_string = '         GAME OVER'
        win_string = '          YOU WIN'

        def cast(string):
            screen.addstr(string + '\n')        #addstr是curses中的应用，为显示一个字符串

        #绘制水平分割线
        def draw_hor_separator():
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')
        screen.clear()

        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


    def spawn(self):        #随机生成一个2或者4
        new_element = 4 if randrange(100) > 89 else 2   #相当于百分之10的概率生成4
        (i,j) = choice([(i,j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element      #生成的4或者2放置在为0的位置


    def move_is_possible(self,direction):       #判断能否移动
        def row_is_left_movable(row):
            def change(i):
                if row[i] == 0 and row[i+1] != 0:   #可以移动
                    return True
                if row[i] != 0 and row[i+1] == row[i]:   #可以合并
                    return True
                return False
            return any(change(i) for i in range(len(row)-1))

        check = {}
        check['Left'] = lambda field: any(row_is_left_movable(row) for row in field)

        check['Right'] = lambda field: check['Left'](invert(field))

        check['Up'] = lambda field: check['Left'](transpose(field))

        check['Down'] = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

def main(stdscr):
    
    def init():

        #重置游戏棋盘
        game_field.reset()
        return 'Game'
    
    def not_game(state):
        #画出GameOver或者Win的界面
        game_field.draw(stdscr)
        #读取用户输入得到action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda:state)   #默认是当前状态，没有行为就会一直处于当前界面循环
        responses['Restart'], responses['Exit'] = 'Init','Exit'     #对应不同的行为转换到不同的状态
        return responses[action]

    def game():
        #画出当前棋盘状态
        game_field.draw(stdscr)
        #读取用户输入得到的action
        action = get_user_action(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):     #成功移动一步
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'GameOver'
        return 'Game'

    state_action = {
            'Init' : init,
            'Win' : lambda: not_game('Win'),
            'GameOver': lambda: not_game('GameOver'),
            'Game' : game
         }
    
    curses.use_default_colors()
    game_field = GameField(win = 32)

    state = 'Init'

    #状态即开始循环
    while state != 'Exit':
        state = state_action[state]()



curses.wrapper(main)
