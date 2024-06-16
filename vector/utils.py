import random

from pygame.image import load
from pygame.math import Vector2
from pygame.mixer import Sound
from pygame import Color

# A file for helper functions


# Helper function to load sprites from the assets folder
def load_sprite(name, with_alpha=True):
    path = f"assets/sprites/{name}.png"
    loaded_sprite = load(path)

    if with_alpha:
        return loaded_sprite.convert_alpha()
    else:
        return loaded_sprite.convert()


# When objects leave the screen, have them come back on the opposite side
def wrap_position(position, surface):
    x, y = position
    w, h = surface.get_size()
    return Vector2(x % w, y % h)


# Function for generating a random location on the screen
def get_random_position(surface):
    return Vector2(
        random.randrange(surface.get_width()),
        random.randrange(surface.get_height())
    )


# Generates random speed and direction
def get_random_velocity(min_speed, max_speed):
    speed = random.randint(min_speed, max_speed)
    angle = random.randrange(0, 360)
    return Vector2(speed, 0).rotate(angle)


# Helper function for loadign sounds from the assets folder
def load_sound(name):
    path = f'assets/sounds/{name}.wav'
    return Sound(path)


# A function for drawing text on the screen
def print_text(surface, text, font, position, color=Color("tomato")):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()

    # Collect the position of the high score
    x = 0
    if position[:6] == "score_":
        x = int(position[6:])

    # Preset positions used to display different types of text
    if position == "center":
        rect.center = Vector2(surface.get_size()) / 2
    elif position == "top":
        rect.center = (surface.get_width() / 2, 20)
    elif position == "scoreboard":
        rect.center = Vector2(surface.get_size()) / 2
        rect.center += Vector2(0, 50)
    elif position == ("score_" + str(x)):
        rect.center = Vector2(surface.get_size()) / 2
        rect.center += Vector2(0, 60 + 20 * x)
    elif position == "volume":
        rect.center = (surface.get_width() / 2, 50)
    surface.blit(text_surface, rect)


# A helper function to help deceleration stop at 0
def approach_zero(x, deceleration):
    if abs(x) < deceleration:
        x = 0
    else:
        if x > 0:
            x -= deceleration
        else:
            x += deceleration
    return x


# A helper function to read the options file
def read_file(name):
    with open(name + ".txt", 'r') as f:
        text = f.readlines()
    return text


# A helper function to update the high scores
def score_update(scores, score):
    new_scores = []
    changed = False
    for s in scores:
        s = int(s)
        if score > s:
            if not changed:
                new_scores.append(score)
                new_scores.append(s)
                changed = True
            else:
                new_scores.append(s)
        else:
            new_scores.append(s)
    new_scores = new_scores[:5]
    return new_scores


# A helper function to write updated scores to the options file
def write_file(name, scores):
    with open(name + ".txt", 'r') as f:
        text = f.readlines()

    for x in range(1, 6):
        text[x] = ("score_" + str(x) + " = " + str(scores[x - 1]) + "\n")

    with open(name + ".txt", 'w') as f:
        f.writelines(text)


# A helper function to write updated volume to the options file
def write_volume(volume):
    with open("options.txt", 'r') as f:
        text = f.readlines()

    text[0] = ("volume = " + str(volume) + "\n")

    with open("options.txt", 'w') as f:
        f.writelines(text)
