from pygame.math import Vector2
from pygame.transform import rotozoom

from utils import load_sprite, wrap_position, get_random_velocity, load_sound, approach_zero

# Create a Vector2 to track the direction UP
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
    def draw(self, surface, s_type):
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
    MAX_SPEED = 6

    def __init__(self, position, create_bullet_callback):

        # Set default values that can be changed through powerups
        self.acceleration = 0.25
        self.bullet_speed = 3
        self.bullet_amount = 1

        # Allows you to pass bullet objects back to the game.py file
        self.create_bullet_callback = create_bullet_callback

        # Setup sound for firing a bullet
        self.laser_sound = load_sound("laser")
        self.sprite_shield = load_sprite("spaceship_shielded")

        self.direction = Vector2(UP)
        super().__init__(position, load_sprite("spaceship"), Vector2(0))

    # Rotates the ship based on the maneuverability constant
    def rotate(self, clockwise=True):
        sign = 1 if clockwise else -1
        angle = self.MANEUVERABILITY * sign
        self.direction.rotate_ip(angle)

    # If the ship is not at the max speed, accelerate
    def accelerate(self):
        x = self.velocity + (self.direction * self.acceleration)
        if x.length() < self.MAX_SPEED:
            self.velocity += self.direction * self.acceleration

    # Slow the ship down by a fraction of its acceleration
    def decelerate(self):
        deceleration = self.acceleration * .3
        x, y = self.velocity

        # Use a helper function to stop deceleration when speed hits 0
        x = approach_zero(x, deceleration)
        y = approach_zero(y, deceleration)
        self.velocity = (x, y)

    # Allows the ship to move backwards
    def reverse(self):
        x = self.velocity - (self.direction * self.acceleration)
        if x.length() < self.MAX_SPEED:
            self.velocity -= self.direction * self.acceleration

    # Fires a bullet from the ship
    def shoot(self, volume):

        # Calculate the bullet velocity, create a bullet object, and pass it back with the callback function
        bullet_velocity = self.direction * self.bullet_speed + self.velocity
        bullet = Bullet(self.position, bullet_velocity)
        self.create_bullet_callback(bullet)

        # Create two more bullets if multi-shot is active
        if self.bullet_amount == 3:
            dir1 = self.direction.rotate(self.MANEUVERABILITY * 3)
            bullet_velocity = dir1 * self.bullet_speed + self.velocity
            bullet = Bullet(self.position, bullet_velocity)
            self.create_bullet_callback(bullet)

            dir2 = self.direction.rotate(-self.MANEUVERABILITY * 3)
            bullet_velocity = dir2 * self.bullet_speed + self.velocity
            bullet = Bullet(self.position, bullet_velocity)
            self.create_bullet_callback(bullet)

        # Play laser sound based on the current volume
        if volume > 0:
            self.laser_sound.set_volume(volume / 100)
        else:
            self.laser_sound.set_volume(0)
        self.laser_sound.play()

    # Function for drawing the spaceship, overloads the parent function
    def draw(self, surface, s_type):
        angle = self.direction.angle_to(UP)

        # Display an alternative sprite if shielded
        if s_type == 1:
            rotated_surface = rotozoom(self.sprite, angle, 1.0)
        else:
            rotated_surface = rotozoom(self.sprite_shield, angle, 1.0)
        rotated_surface_size = Vector2(rotated_surface.get_size())
        blit_position = self.position - rotated_surface_size * 0.5
        surface.blit(rotated_surface, blit_position)


class Asteroid(GameObject):

    # Asteroids start of at size 3
    def __init__(self, position, create_asteroid_callback, size=3):

        # Callback function
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


# A powerup class for powerups to inherit from
class Powerup(GameObject):
    def __init__(self, position, p_type):
        self.powerup_sound = load_sound("powerup")
        super().__init__(position, load_sprite(p_type), Vector2(0))

    # Plays powerup pickup sound based on the current volume
    def pickup_sound(self, volume):
        if volume > 0:
            self.powerup_sound.set_volume(volume / 100)
        else:
            self.powerup_sound.set_volume(0)
        self.powerup_sound.play()


class Shield(Powerup):
    def __init__(self, position):
        super().__init__(position, "powerup_shield")


class ShipSpeed(Powerup):
    def __init__(self, position):
        super().__init__(position, "powerup_ship_speed")


class BulletSpeed(Powerup):
    def __init__(self, position):
        super().__init__(position, "powerup_bullet_speed")


class MultiShot(Powerup):
    def __init__(self, position):
        super().__init__(position, "powerup_multi_shot")
