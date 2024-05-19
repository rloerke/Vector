from pygame.math import Vector2
from pygame.transform import rotozoom

from utils import load_sprite, wrap_position, get_random_velocity, load_sound

UP = Vector2(0, -1)


# A class for game objects to inherit from
class GameObject:
    def __init__(self, position, sprite, velocity):
        self.position = Vector2(position)
        self.sprite = sprite
        self.radius = sprite.get_width() / 2

        # To keep track of speed and direction
        self.velocity = Vector2(velocity)

    # Draws the object based on its size and the size of the screen
    def draw(self, surface):
        blit_position = self.position - Vector2(self.radius)
        surface.blit(self.sprite, blit_position)

    # Make objects that leave the screen re-appear on the opposite side
    def move(self, surface):
        self.position = wrap_position(self.position + self.velocity, surface)

    # Checks if object has collided with another game object
    def collides_with(self, other_obj):
        distance = self.position.distance_to(other_obj.position)
        return distance < self.radius + other_obj.radius


class Spaceship(GameObject):

    # Sets some default values for the spaceship class
    MANEUVERABILITY = 3
    ACCELERATION = 0.25
    BULLET_SPEED = 3
    MAX_SPEED = 6

    def __init__(self, position, create_bullet_callback):

        # Allows you to pass bullet objects back to the game.py file
        self.create_bullet_callback = create_bullet_callback

        # Setup sound for firing a bullet
        self.laser_sound = load_sound("laser")
        self.laser_sound.set_volume(0.1)

        self.direction = Vector2(UP)
        super().__init__(position, load_sprite("spaceship"), Vector2(0))

    def rotate(self, clockwise=True):
        sign = 1 if clockwise else -1
        angle = self.MANEUVERABILITY * sign
        self.direction.rotate_ip(angle)

    # If the ship is not at the max speed, accelerate
    def accelerate(self):
        x = self.velocity + (self.direction * self.ACCELERATION)
        if x.length() < self.MAX_SPEED:
            self.velocity += self.direction * self.ACCELERATION

    def shoot(self):
        bullet_velocity = self.direction * self.BULLET_SPEED + self.velocity
        bullet = Bullet(self.position, bullet_velocity)
        self.create_bullet_callback(bullet)
        self.laser_sound.play()

    def draw(self, surface):
        angle = self.direction.angle_to(UP)
        rotated_surface = rotozoom(self.sprite, angle, 1.0)
        rotated_surface_size = Vector2(rotated_surface.get_size())
        blit_position = self.position - rotated_surface_size * 0.5
        surface.blit(rotated_surface, blit_position)


class Asteroid(GameObject):
    def __init__(self, position, create_asteroid_callback, size=3):
        self.create_asteroid_callback = create_asteroid_callback
        self.size = size

        # Set up the 3 possible sizes of asteroid
        size_to_scale = {3: 1, 2: 0.5, 1: 0.25, }
        scale = size_to_scale[size]
        sprite = rotozoom(load_sprite("asteroid"), 0, scale)

        super().__init__(position, sprite, get_random_velocity(1, 3))

    # Splits into smaller asteroids when hit with a bullet
    def split(self):
        if self.size > 1:
            for _ in range(2):
                asteroid = Asteroid(self.position, self.create_asteroid_callback, self.size - 1)
                self.create_asteroid_callback(asteroid)


class Bullet(GameObject):
    def __init__(self, position, velocity):
        super().__init__(position, load_sprite("bullet"), velocity)

    # Overload the move class to stop bullets from wrapping around the screen
    def move(self, surface):
        self.position = self.position + self.velocity
