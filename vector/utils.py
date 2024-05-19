import random

from pygame.image import load
from pygame.math import Vector2
from pygame.mixer import Sound
from pygame import Color


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


def load_sound(name):
    path = f'assets/sounds/{name}.wav'
    return Sound(path)


# A function for drawing text on the screen
def print_text(surface, text, font, position, color=Color("tomato")):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()
    if position == "center":
        rect.center = Vector2(surface.get_size()) / 2
    elif position == "top":
        rect.center = (surface.get_width() / 2, 20)
    surface.blit(text_surface, rect)
