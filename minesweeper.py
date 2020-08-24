import numpy as np
import random
import datetime
from itertools import product
from typing import List, Tuple
import requests
from io import BytesIO
import os

from tkinter import *
from tkinter import messagebox

from PIL import Image  # overrides tkinter Image

WIDTH = 15
HEIGHT = 15
BOMBS = 30


class SmartButton(Button):
    """Button that stores position and whether it was clicked"""

    def __init__(self, master, row, col, clicked=False, **kwargs):
        super().__init__(master=master, **kwargs)
        self.row = row
        self.col = col
        self.clicked = clicked

    def get_row(self):
        return self.row

    def get_col(self):
        return self.col

    def get_clicked(self):
        return self.clicked

    def click(self):
        self.clicked = True

    def unclick(self):
        self.clicked = False


class MineSweeper(Frame):
    """Minesweeper"""

    def __init__(self, master: Tk, height: int, width: int, bombs: int) -> None:
        """Plays a game of Minesweeper

        Args:
            master (Tk): Tk
            height (int): height of board
            width (int): width of board
            bombs (int): number of bombs
        """

        super().__init__(master)
        self.grid()

        self.root = master

        self.width = width
        self.height = height

        self.gameover = False

    # generate list of bomb coordinates
        bombs = area if (bombs > (area := width * height)) else bombs
        self.bombs = random.sample(list(product(range(height), range(width))), bombs)

    # create a board of SmartButtons
        self.board = np.empty((height, width), dtype=SmartButton)

        for row in range(height):
            for col in range(width):
                button = SmartButton(self, row, col, width=2, height=1)
                button.config(command=lambda button=button: self.reveal(button))

                self.board[row][col] = button
                self.board[row][col].bind('<Button-3>', lambda event, button=button: self.flag(event, button=button))
                self.board[row][col].grid(row=row + 1, column=col, rowspan=1, columnspan=1)

    # generate a 2D list of nearest bomb values
        self.nearby = np.zeros((height, width), dtype=int)
        for row in range(height):
            for col in range(width):
                if ((row, col) in self.bombs):
                    self.nearby[row][col] = -1
                else:
                    nearby = MineSweeper.vicinity(row, col, width, height)

                    bomb_counter = 0
                    for coord in nearby:
                        if (coord in self.bombs):
                            bomb_counter += 1

                    self.nearby[row][col] = bomb_counter

                    self.color_map = {-1: 'black', 0: 'gray', 1: 'blue', 2: 'darkgreen', 3: 'red', 4: 'purple',
                                 5: 'maroon', 6: 'cyan', 7: 'black', 8: 'dim gray'}

                    self.board[row][col].config(fg=self.color_map[bomb_counter])

    # bombs left to be flagged
        self.remaining = bombs
        self.flagLabel = Label(self, text=str(self.remaining), font=('Helvetica', 12))
        self.flagLabel.grid(row=height + 1, columnspan=width)
    
    # new game
        self.newGameButton = Button(self, text='New Game', command=self.new_game)
        self.newGameButton.grid(row=height + 1, columnspan=4)
    
    # stopwatch
        self.started = False
        self.now = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
        self.stopwatch = Label(self, text=self.now.strftime('%S:%f')[:-4])
        self.stopwatch.grid(row=height + 1, column=width - 3 if width > 3 else 0, columnspan=3)

    @staticmethod
    def vicinity(row: int, col: int, width: int, height: int) -> List[Tuple[int]]:
        """returns the coordinates within the radius of a point and on the board

        Args:
            x (int): x coordinate
            y (int): y coordinate

        Returns:
            List[Tuple[int]]: list of points that are on the board
        """

        row_possible = [row - 1, row, row + 1]
        col_possible = [col - 1, col, col + 1]

        result = list(product(row_possible, col_possible))
        result.remove((row, col))

        result = [(row, col) for row, col in result if (not(min((row, col)) < 0 or row >= height or col >= width))]

        return result

    def reveal(self, button: SmartButton) -> None:
        """reveals the number of bombs in a square's vicinity

        Args:
            button (SmartButton): Tkinter button that stores extra information
        """

        if (not(self.gameover)):
            if (not(self.started)):
                self.start_stopwatch()
            else:
                self.started = True

            row, col = button.get_row(), button.get_col()
            square = self.board[row][col]

            if ((text := square['text']) != '🚩' and text != '?'):
                if (not(square.get_clicked())):  # if the button has not been clicked
                    square.click()
                    square.config(relief=SUNKEN)
                    square.config(bg='#BCBCBC')

                    if (self.nearby[row][col] == -1):  # if the button clicked is a bomb
                        for bomb in self.bombs:
                            row, col = bomb
                            self.board[row][col].config(bg='red', text='🚩')
                        
                        self.reveal_all(lose=True)
                        self.gameover = True

                    # notify player
                        again = messagebox.askyesno("Game Over", 'KABOOM! You lose.\nWould you like to play again?')
                        self.new_game() if again else self.root.destroy()
                    
                    else: # if the button clicked wasn't a bomb
                        if (self.nearby[row][col] != 0): # if there are bombs in the square's vicinity
                            square['text'] = self.nearby[row][col] # reveal the number of bombs
                        else:  # recursively reveal zeros
                            for neighbor_row, neighbor_col in MineSweeper.vicinity(row, col, self.width, self.height):
                                self.reveal(self.board[neighbor_row][neighbor_col])

    def flag(self, _: tuple, button: SmartButton) -> None:
        """flags a square to mark a bomb

        Args:
            _ (tuple): coordinates of mouse
            button (SmartButton): a button in self.board
        """

        if (not(self.gameover)):
            if (not(self.started)):
                self.start_stopwatch()
            else:
                self.started = True

            row, col = button.get_row(), button.get_col()
            square = self.board[row][col]

        # toggles the flag
            if (square['relief'] == RAISED):
                if ((text := square['text']) == '🚩'):
                    square.config(text='?', fg='black')
                    self.remaining += 1

                elif (text == '?'):
                    square.config(text='', fg=self.color_map[self.nearby[row][col]])

                elif (self.remaining > 0):
                    square.config(text='🚩', fg='black')
                    self.remaining -= 1
                
                self.flagLabel.config(text=str(self.remaining))

        # check win
            flagged = [tuple(i) for i in np.array(np.where([[btn['text'] == '🚩' for btn in row] for row in self.board]), dtype=tuple).transpose()]

            if (set(list(flagged)) == set(self.bombs)):
                # reveal all squares
                self.reveal_all(lose=False)
                self.gameover = True

                again = messagebox.askyesno('You Win!', 'Congratulations! You Win!\nWould you like to play again?')
                self.new_game() if again else self.root.destroy()
    
    def reveal_all(self, lose: bool):
        """clicks open all squares after game is over

        Args:
            lose (bool): whether the player won or lost
        """

        for row in self.board:
            for square in row:
                if (not((square.get_row(), square.get_col()) in self.bombs)):
                    self.reveal(self.board[square.get_row()][square.get_col()])
                else:
                    color = 'red' if lose else 'light green'

                    self.board[square.get_row()][square.get_col()].config(bg=color, text='💣')

    def start_stopwatch(self):
        """start stopwatch on first click
        """

        if(not(self.gameover)):
            self.started = True
            self.increment()

    def increment(self):
        """increment the stopwatch by 1 second
        """

        self.now += datetime.timedelta(microseconds=1000)
        self.stopwatch.after(1, self.start_stopwatch)
        if (int((string_time := self.now.strftime('%H:%M:%S:%f')[:-4].split(':'))[0]) > 0): # if more than 1 hour has passed
            self.stopwatch.config(text=':'.join(string_time[:2]))
        elif (int(string_time[1]) > 0): # if more than one minute has passed
            self.stopwatch.config(text=':'.join(string_time[1:3]))
        else:
            self.stopwatch.config(text=':'.join(string_time[2:]))

    def new_game(self):
        """plays a new game of MineSweeper on the same board
        """

        [button.destroy() for row in self.board for button in row]
        self.flagLabel.destroy()
        self.stopwatch.destroy()

        self.gameover = False

    # generate list of bomb coordinates
        self.bombs = random.sample(list(product(range(self.height), range(self.width))), len(self.bombs))

    # create a board of SmartButtons
        self.board = np.empty((self.height, self.width), dtype=SmartButton)

        for row in range(self.height):
            for col in range(self.width):
                button = SmartButton(self, row, col, width=2, height=1)
                button.config(command=lambda button=button: self.reveal(button))

                self.board[row][col] = button
                self.board[row][col].bind('<Button-3>', lambda event, button=button: self.flag(event, button=button))
                self.board[row][col].grid(row=row + 1, column=col, rowspan=1, columnspan=1)

    # generate a 2D list of nearest bomb values
        self.nearby = np.zeros((self.height, self.width), dtype=int)
        for row in range(self.height):
            for col in range(self.width):
                if ((row, col) in self.bombs):
                    self.nearby[row][col] = -1
                else:
                    nearby = MineSweeper.vicinity(row, col, self.width, self.height)

                    bomb_counter = 0
                    for coord in nearby:
                        if (coord in self.bombs):
                            bomb_counter += 1

                    self.nearby[row][col] = bomb_counter

                    self.color_map = {-1: 'black', 0: 'gray', 1: 'blue', 2: 'darkgreen', 3: 'red', 4: 'purple',
                                 5: 'maroon', 6: 'cyan', 7: 'black', 8: 'dim gray'}

                    self.board[row][col].config(fg=self.color_map[bomb_counter])

    # bombs left to be flagged
        self.remaining = len(self.bombs)
        self.flagLabel = Label(self, text=str(self.remaining), font=('Arial', 12))
        self.flagLabel.grid(row=self.height + 1, columnspan=self.width)
    
    # reset stopwatch
        self.started = False
        self.now = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
        self.stopwatch = Label(self, text=self.now.strftime('%S:%f')[:-4])
        self.stopwatch.grid(row=self.height + 1, column=self.width - 3 if self.width > 3 else 0, columnspan=3)


def minesweeper(width: int, height: int, bombs: int):
    """plays a game of minesweeper

    Args:
        width (int): width of board
        height (int): height of board
        bombs (int): number of bombs
    """

    root = Tk()

    root.title('Minesweeper')

# set favicon
    icon = Image.open(BytesIO(requests.get('https://cdn.pixabay.com/photo/2017/01/31/16/59/bomb-2025548_960_720.png').content))
    icon.save('icon.ico')
    root.iconbitmap('icon.ico')
    os.remove('icon.ico')

    game = MineSweeper(root, width, height, bombs)
    game.mainloop()

if __name__ == "__main__":
    minesweeper(WIDTH, HEIGHT, BOMBS)
