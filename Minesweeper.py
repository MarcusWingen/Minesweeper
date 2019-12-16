import pygame as pg
from datetime import datetime
import random as rnd


# Game settings:
Num_Mines = 10
Columns = 10
Rows = 10
# -----------------------------

# Display settings
Info_Height = 40  # Height of info area displaying number of mines and time
Tile_size = 30
Width = Columns * Tile_size
Height = Rows * Tile_size + Info_Height
Screen_Size = (Width, Height)

# Values of tiles, also used in file names of the images
# IDs 1-8 are used for mine-counting
Empty_ID = 0
Mine_ID = 9
Cover_ID = 10
Flag_ID = 11
Question_mark_ID = 12
Explosion_ID = 13
False_Flag = 14

# Variables for filling the field:
X = 0
Y = Info_Height  # start below the info field
Screen_Filled = False
Start_time_saved = False
End_time_saved = False

# General variables
Mines_Found = 0
Go = True
Game_Lost = False
Game_Won = False
Game_Over = False
Final_Filled = False
Score_Saved = False
Player_Name = "Player"
Tile_list = pg.sprite.Group()

Date_Time = datetime.now()
Date_Time_out = Date_Time.strftime("%d/%m/%Y")

# Default values for variables used later
Start_Time = datetime.now()
End_time = datetime.now()
Completion_Time = End_time - Start_Time
Completion_Time_out = Completion_Time.total_seconds()


class Tile(pg.sprite.Sprite):
    """A tile is one part of the game field.
    Each tile has x,y coordinates, a picture_id from 0-12 and a size.
    """

    def __init__(self, x, y, pic_id, size=Tile_size):
        super().__init__()  # Call the parent class (Sprite) constructor
        self.image = pg.transform.scale(pg.image.load(f"./tiles/MS_{pic_id}.png"), (size, size))

        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


def next_to_field(index1, index2):
    """Check if the position of index1 is next to index2 on the game filed."""
    # x,y pos of fields in question:
    index1_x = (index1 % Columns) * Tile_size
    index1_y = (index1 // Columns) * Tile_size
    index2_x = (index2 % Columns) * Tile_size
    index2_y = (index2 // Columns) * Tile_size

    if index2_x in range(index1_x - Tile_size, index1_x + Tile_size + 1) and \
            index2_y in range(index1_y - Tile_size, index1_y + Tile_size + 1):
        return True
    else:
        return False


def create_field():
    """place mines in the field list"""
    field = [Empty_ID for n in range(Columns * Rows)]

    # randomly place mines:
    while sum(field) < Num_Mines * Mine_ID:
        field[rnd.randrange(len(field))] = Mine_ID

    # Define all possible positions of neighbouring fields relative to one field, 8 in total:
    neighbour_fields = [-Columns - 1, -Columns, -Columns + 1, -1, 1, Columns - 1, Columns, Columns + 1]

    # place numbers next to mines as hints for the player:
    for m in range(len(field)):
        for n in neighbour_fields:
            if field[m] == Mine_ID:  # if there is a mine at this position
                if m + n in range(len(field)):  # i.e. m + 1, m - 1, m + 10 etc. is a valid list index
                    if next_to_field(m, m + n):  # if m+n is next to m in terms of x,y coordinates
                        if field[m + n] != Mine_ID:  # if field next to m does not contain a mine itself
                            field[m + n] += 1  # set value +1 -> mine-marker, adds up for multiple mines
    return field


def clear_tile(cover_list, field_list):
    """Uncover empty tile and all connected empty tiles. Set value of
    neighbours to uncovered value.
    Continues as long as new fields are uncovered,
    i.e. the checksum decreases.
    """
    # list of checksums, starting with highest possible value, followed by current value:
    checksums = [Columns * Rows * 12, sum(Cover)]
    iterations = 1  # keep track of how many times the loop has been performed
    cleared_fields = []  # Store all indices of uncovered fields, used to draw the tiles
    # Define all possible positions of neighbouring fields relative to one field, 8 in total:
    neighbour_fields = [-Columns - 1, -Columns, -Columns + 1, -1, 1, Columns - 1, Columns, Columns + 1]

    while checksums[iterations] < checksums[iterations - 1]:  # while number of uncovered tiles increases
        for i in range(len(cover_list)):
            for n in neighbour_fields:
                if cover_list[i] == Empty_ID:
                    if i + n in range(len(cover_list)):
                        if next_to_field(i, i + n):
                            if i + n not in cleared_fields and cover_list[i + n] > Mine_ID:
                                cleared_fields.append(i + n)  # store it to show it later
                            cover_list[i + n] = field_list[i + n]

        # Go through list in reverse order, too. This way tiles at low index
        # positions will be uncovered in less iterations, if the first tile is
        # at at higher index position.
        for i in reversed(range(len(cover_list))):
            for n in neighbour_fields:
                if cover_list[i] == Empty_ID:
                    if i + n in range(len(cover_list)):
                        if next_to_field(i, i + n):
                            if i + n not in cleared_fields and cover_list[i + n] > Mine_ID:
                                cleared_fields.append(i + n)
                            cover_list[i + n] = field_list[i + n]

        # For each iteration append the sum of the Cover tiles to check
        # if more tiles are uncovered.
        checksums.append(sum(Cover))
        iterations += 1

    # Draw new tiles:
    for n in cleared_fields:
        n_x = (n % Columns) * Tile_size
        n_y = (n // Columns) * Tile_size + Info_Height
        new_tile = Tile(n_x, n_y, cover_list[n])
        Tile_list.add(new_tile)
    Tile_list.draw(screen)


def fill_screen(list1, list2=None):
    """initially draw the full field with pic_id = Cover_ID.
    If game is lost reveal the screen.
    For initial drawing one list is required.
    For revealing the field two are used to show marked mines and the one
    that was hit, as marked in the Cover list."""

    for n in range(len(list1)):
        if list2 is not None:  # only provided if the game is lost
            if list2[n] != Flag_ID:  # leave flags in place
                n_x = (n % Columns) * Tile_size
                n_y = (n // Columns) * Tile_size + Info_Height
                new_tile = Tile(n_x, n_y, list1[n])
                Tile_list.add(new_tile)
                if list2[n] == Explosion_ID:  # show mine that was hit
                    n_x = (n % Columns) * Tile_size
                    n_y = (n // Columns) * Tile_size + Info_Height
                    new_tile = Tile(n_x, n_y, list2[n])
                    Tile_list.add(new_tile)
            if list2[n] == Flag_ID and list1[n] != Mine_ID:  # remove false flags
                n_x = (n % Columns) * Tile_size
                n_y = (n // Columns) * Tile_size + Info_Height
                new_tile = Tile(n_x, n_y, False_Flag)  # mark false flag
                Tile_list.add(new_tile)

        else:  # this is used at the start of the game
            n_x = (n % Columns) * Tile_size
            n_y = (n // Columns) * Tile_size + Info_Height
            new_tile = Tile(n_x, n_y, list1[n])
            Tile_list.add(new_tile)

    Tile_list.draw(screen)


# Num of list pos with val ==11 - marked as mines
def count_mines(cover_list):
    """Count how many fields in the cover_list are flagged as mines"""
    count = Num_Mines
    for i in range(len(cover_list)):
        if cover_list[i] == Flag_ID:
            count -= 1
    return count


def timer(curr_time):
    """calc timedelta from start of game and return the total seconds as int"""
    game_time = curr_time - Start_Time
    return int(game_time.total_seconds())


# ------------------------------------------
# Start the game
# ------------------------------------------
pg.init()
clock = pg.time.Clock()

# Create the field and the cover:
Field = create_field()
Cover = [Cover_ID for n in range(Columns * Rows)]

screen = pg.display.set_mode(Screen_Size)
pg.display.set_caption("Minesweeper")
pg.display.set_icon(pg.image.load("MS_icon.png"))

# Main loop:
while Go:
    clock.tick(60)

    # Display mine counter and timer in top row:
    if not Game_Over:
        screen.fill((0, 0, 0), (0, 0, Width, Info_Height))  # Fill screen black at x,y = 0; width, height to update text
        textsurface = pg.font.SysFont("Arial", 30).render("Mines: " + str(count_mines(Cover)), False, (255, 255, 255))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) - 80, 0))
        textsurface = pg.font.SysFont("Arial", 30).render("T[s]: " + str(timer(datetime.now())), False, (255, 255, 255))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) + 80, 0))

    # Drawing the Field/Cover on screen:
    while not Screen_Filled and not Game_Over:
        fill_screen(Cover)
        Screen_Filled = True

    if not Start_time_saved:
        Start_Time = datetime.now()
        Start_time_saved = True

    for event in pg.event.get():
        if event.type == pg.QUIT:
            Go = False

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # 1=left click, 2=middle, 3=right 4=scroll up 5=scroll down
                pos = pg.mouse.get_pos()  # get x,y of mouse
                if pos[1] > Info_Height:  # if click is below the Info row; [1] = y pos
                    xpart = pos[0] // Tile_size  # calculate index from mouse x and y
                    ypart = (pos[1] - Info_Height) // Tile_size
                    index = xpart + (Columns * ypart)
                    Cover[index] = Field[index]  # to uncover a Tile
                    new_field = Tile(xpart * Tile_size, ypart * Tile_size + Info_Height, Cover[index])
                    Tile_list.add(new_field)
                    Tile_list.draw(screen)
                    if Cover[index] == Empty_ID:
                        clear_tile(Cover, Field)  # if tile is empty show surrounding ones
                    if Cover[index] == Mine_ID:  # Hit a Mine
                        Cover[index] = Explosion_ID
                        Game_Lost = True  # after Mine is drawn Game Over

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 3:  # 3 = right click
                pos_r = pg.mouse.get_pos()
                if pos_r[1] > Info_Height:
                    tile_reset = False
                    xpart_r = pos_r[0] // Tile_size
                    ypart_r = (pos_r[1] - Info_Height) // Tile_size
                    index_r = xpart_r + (Columns * ypart_r)
                    if Cover[index_r] == Question_mark_ID:  # reset from '?' to empty tile
                        Cover[index_r] = Cover_ID
                        tile_reset = True
                    if Cover[index_r] == Flag_ID:  # go from flag to '?'
                        Cover[index_r] = Question_mark_ID
                        if Field[index_r] == Mine_ID:  # mine un-flagged -> mine counter - 1
                            Mines_Found -= 1
                    if Cover[index_r] == Cover_ID and not tile_reset:
                        Cover[index_r] = Flag_ID  # Picture marking a mine
                    if Field[index_r] == Mine_ID and Cover[index_r] == Flag_ID:  # correctly located a mine
                        Mines_Found += 1
                    new_field = Tile(xpart_r * Tile_size, ypart_r * Tile_size + Info_Height, Cover[index_r])
                    Tile_list.add(new_field)
                    Tile_list.draw(screen)

    if Mines_Found == Num_Mines and Cover_ID not in Cover:  # all mines marked an no cover tile left
        Game_Won = True
        if not End_time_saved:
            End_time = datetime.now()
            End_time_saved = True

    if End_time_saved:
        Completion_Time = End_time - Start_Time
        Completion_Time_out = int(Completion_Time.total_seconds())

    # Display Game Over message:
    if Game_Lost:
        Game_Over = True
        if not Final_Filled:
            fill_screen(Field, Cover)  # Fill screen again, but this time include the Filed list to reveal everything
            Final_Filled = True
        textsurface = pg.font.SysFont("Arial", 30).render("You loose!", False, (255, 255, 255), (0, 0, 0))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2), Height - 2 * Tile_size))

    if Game_Won:
        Game_Over = True
        textsurface = pg.font.SysFont("Arial", 30).render("You win!", False, (255, 255, 255), (0, 0, 0))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2), Height - 2 * Tile_size))
        pg.display.flip()

        # Save score:
        Highscore = []
        Printed_scores = 0
        if not Score_Saved:
            with open("MS Highscore.txt", "a") as Score_File:
                Score_File.write(Date_Time_out + ", " + Player_Name + ", " + str(Completion_Time_out) + "\n")
                Score_Saved = True
            with open("MS Highscore.txt", "r") as Score_File:
                for score in Score_File:
                    d = score.split(", ")[0]  # split the string to get Date, Name and Completion_Time seperated
                    n = score.split(", ")[1]
                    s = score.split(", ")[2]
                    s1 = int(s.strip())
                    Highscore.append((d, n, s1))
                    Highscore.sort(key=lambda tup: tup[2])

        # Display Highscore in black on white background:
        textsurface = pg.font.SysFont("Arial", 30).render("Date", False, (0, 0, 0), (255, 255, 255))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) - 80, Info_Height + 10))
        textsurface = pg.font.SysFont("Arial", 30).render("Time [s]", False, (0, 0, 0), (255, 255, 255))
        screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) + 80, Info_Height + 10))

        y_pos = 50  # pos increment for displaying Highscore
        for n in range(len(Highscore)):
            if Printed_scores < len(Highscore):
                if Printed_scores < Rows // 2:
                    textsurface = pg.font.SysFont("Arial", 25).render(str(Highscore[n][0]), False, (0, 0, 0),
                                                                         (255, 255, 255))
                    screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) - 80, Info_Height + y_pos))
                    textsurface = pg.font.SysFont("Arial", 25).render(str(Highscore[n][2]), False, (0, 0, 0),
                                                                         (255, 255, 255))
                    screen.blit(textsurface, ((Width // 2 - textsurface.get_width() // 2) + 90, Info_Height + y_pos))
                    y_pos += 40
                    Printed_scores += 1

    pg.display.flip()

pg.quit()
