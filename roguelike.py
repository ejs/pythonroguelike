# Using libtcodpy - here's the import

import libtcodpy as libtcod

# Need sqrt function

import math

# Using textwrap module

import textwrap

# Some important values, first is the actual size of the window

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# Setting size of map

MAP_WIDTH = 80
MAP_HEIGHT = 43

# Parameters for the dungeon generator

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

FOV_ALGO = 0 # Default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Number of frames to wait after moving/attacking
PLAYER_SPEED = 2
DEFAULT_SPEED = 8
DEFAULT_ATTACK_SPEED = 20

# Sizes and co-ordinates relevant for the GUI

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

# 20 frames per second maximum

LIMIT_FPS = 20

# Colours of tiles when dark

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

class Object:
    
    # This is a generic object; the player, a monster, an item, the stairs...
    # it's always represented by a character on the screen.

    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, speed=DEFAULT_SPEED):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.speed = speed
        self.wait = 0

        self.fighter = fighter
        if self.fighter: # Let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai: # Let the AI component know who owns it
            self.ai.owner = self

    def move(self, dx, dy):

        # Make blocked tiles impassable

        if not is_blocked(self.x + dx, self.y + dy):

            # Move by the given amount

            self.x += dx
            self.y += dy

        self.wait = self.speed

    def draw(self):

        # Now we make sure that objects only show if they're in the player's FOV

        if libtcod.map_is_in_fov(fov_map, self.x, self.y):

        # set the colour and then draw the character that represents this object at it's position.

            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):

        # Erase the character that represents this object

        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def move_towards(self, target_x, target_y):

        # Vector from this object to the target, and distance

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Normalise it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):

        # Return the distance to another object

        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self):

        # Make this object be drawn first, so all others appear above it if they're in the same tile

        global objects
        objects.remove(self)
        objects.insert(0, self)

class Tile:

    # A tile of the map and it's properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # All tiles start unexplored
        self.explored = False

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Rect:

    # A rectangle on the map, used to characterise a room.

    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):

        # Returns true if this rectangle intersects with another one

        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Fighter:

    # Combat related properties and methods (monster, player, NPC)

    def __init__(self, hp, defense, power, death_function=None, attack_speed=DEFAULT_ATTACK_SPEED):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
        self.attack_speed = attack_speed

    def take_damage(self, damage):

        # Apply damage if possible
        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):

        # A simple formula for attack damage
        
        damage = self.power - target.fighter.defense

        if damage > 0:

            # Make the target take some damage
            
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)

        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

        self.owner.wait = self.attack_speed

class BasicMonster:

    # AI for a basic monster.

    def take_turn(self):
        
        # A basic monster takes it's turn. If you can see it, it can see you

        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            # Move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            # If the player is still alive, and the monster is close enough, attack!

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

def player_death(player):

    # the game ended!

    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'

    # For added effect, turn the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):

    # Transform it into a nasty corpse, that doesn't block, can't be attacked and doesn't move

    message(monster.name.capitalize() + ' is dead!', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()

def is_blocked(x, y):

    # First test the map tile

    if map[x][y].blocked:
        return True

    # Now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def create_room(room):
    global map

    # Go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global map

    # Horizontal tunnel

    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global map

    # Vertical tunnel

    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def make_map():
    global map

    # Fill map with "blocked" tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT)  ]
            for x in range(MAP_WIDTH)   ]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):

        # Random width and height

        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)

        # Random position without going out the boundaries of the map

        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        # "Rect" class makes rectangles easier to work with in generation
        new_room = Rect(x, y, w, h)

        # Iterate through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:

            # This means there are no intersections, so this room is valid

            #"paint" it to the map's tiles

            create_room(new_room)

            # Add some objects to this room, such as monsters

            place_objects(new_room)

            # Find center co-ordinates of neww , will be useful later.

            (new_x, new_y) = new_room.center()

            if num_rooms ==0:

                # This is the first room, where the player starts

                player.x = new_x
                player.y = new_y

            else:
                # all rooms after the first - connect it to the previous room with a tunnel

                # Get centre of the previous room

                (prev_x, prev_y) = rooms[num_rooms - 1].center()

                #Draw a coin (random number that is either 0 or 1)

                if libtcod.random_get_int(0, 0, 1) == 1:

                    # First move horizontally, then vertically

                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)

                else:

                    # First move vertically, then horizontally

                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            # Finally append the new room to our list of rooms

            rooms.append(new_room)
            num_rooms += 1

def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute

    if fov_recompute:

        # Recomputes FOV if needed (eg the player moves)

        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)



        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible:

                    # If it's not visible right now, the player can only see it if it's explored

                    if map[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)

                else:

                    # It's visible
                    
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)

                    # Since it's visible, explore it

                    map[x][y].explored = True

    # Draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()
    player.draw()

    # Blitting contents of new console to the root console, in order to display them.

    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    # Prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # Print the game messages, one line at a time

    y=1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    # Show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)

    # Display the names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of the "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def place_objects(room):

    # Choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):

        # Choose random spot for this monster

        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)

        # Only place it if the tile is not blocked

        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80: #80% chance of getting an orc

            # Create an orc
                fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                ai_component = BasicMonster()

                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                    blocks=True, fighter=fighter_component, ai=ai_component)

            else:

            # Create a troll

                fighter_component = Fighter(hp=16, defense=1, power=4, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                    blocks=True, fighter=fighter_component, ai=ai_component)

            objects.append(monster)

def player_move_or_attack(dx, dy):
    global fov_recompute

    # The co-ordinates the player is moving to/attacking

    x = player.x + dx
    y = player.y + dy

    # Try to find an attackable object there

    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    # Attack if target found move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True

def get_names_under_mouse():
    global mouse

    # Return a string with the names of all objects under the mouse

    (x, y) = (mouse.cx, mouse.cy)

    # Create a list with the names of all objects at the mouse co-ordinates and in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names) # join the names, separated by commas
    return names.capitalize()

def handle_keys():
    global fov_recompute
    global keys

    if key.vk == libtcod.KEY_ENTER and key.lalt:

        # Alt+Enter: toggle fullscreen

        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' # Exit game 

    if player.wait > 0: # Don't take a turn yet if still waiting
        player.wait -= 1
        return

    if game_state == 'playing':

    # Movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player_move_or_attack(0, -1)

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player_move_or_attack(0, 1)

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player_move_or_attack(-1, 0)

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player_move_or_attack(1, 0)

        else:
            return 'didnt-take-turn'

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):

    # Render a bar (HP, experience, etc). First calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # Render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # Now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # Finally, some centred text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))


def message(new_msg, color = libtcod.white):

    # Split the message if necessary, among multiple lines

    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:

        # If the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # Add the new line as a tuple, with the text and the colour.

        game_msgs.append( (line, color) )

# Initialisation and Main Loop

# Set the custom font we have in the games directory.

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

# Initialise the window, specifying the size, title, and the boolean at the end tells us if we want fullscreen or not

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python roguelike', False)

# Limit the FPS for real time rather than turn based, no effect if turn based

libtcod.sys_set_fps(LIMIT_FPS)

# Creating a new off screen console that occupies the whole screen

con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

# Creating the object representing the player

fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)

player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component, speed=PLAYER_SPEED)

# The list of objects

objects = [player]

# Create the list of game messages and their colours, starts empty
game_msgs = []

# Generate map (for now it's not drawn to the screen)
make_map()

# Create the FOV map, according to the generated map

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

#FOV will only need to be recomputed if the player moves, or a tile changes.

fov_recompute = True
game_state = 'playing'
player_action = None

panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

mouse = libtcod.Mouse()
key = libtcod.Key()

# Now for the main loop, this logic will keep running as long as the window is not closed.

while not libtcod.console_is_window_closed():

    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)

    # Render the screen
    render_all()

    # Present changes to the screen, i.e. "flushing" the console.

    libtcod.console_flush()

    # Erase all objects at old locations, before they move
    for object in objects:
        object.clear()

    # handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing':
        for object in objects:
            if object.ai:
                if object.wait > 0: # Don't take a turn yet if still waiting
                    object.wait -= 1
                else:
                    object.ai.take_turn()
