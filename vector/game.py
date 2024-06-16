import pygame
import time
import random

from models import Spaceship, Asteroid, Shield, ShipSpeed, BulletSpeed, MultiShot
from utils import load_sprite, get_random_position, print_text, load_sound, read_file, score_update, write_file, \
    write_volume


class Vector:
    # How close asteroids can spawn to your ship
    MIN_ASTEROID_DISTANCE = 300

    def __init__(self):
        self._init_pygame()
        self.screen = pygame.display.set_mode((1200, 600))
        self.background = load_sprite("space", False)
        self.clock = pygame.time.Clock()
        self.paused = False

        # These will be used to display text on the screen
        self.font_big = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.message = ""
        self.score = 0

        options = read_file("options")
        self.volume = int(options[0][9:])
        self.h_scores = []
        for line in options[1:]:
            self.h_scores.append(line[10:-1])

        self.ship_explosion = load_sound("ship_explosion")
        self.rock_break = load_sound("rock_break")

        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.effects = []
        self.effect_timers = []
        self.spaceship = Spaceship((600, 300), self.bullets.append)

        self.gen_asteroids(6)

    def main_loop(self):
        while True:
            self._handle_input()
            self._process_game_logic()
            self._draw()
            if not self.spaceship or (self.spaceship and not self.asteroids):
                time.sleep(4)
                break

    def _init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Vector")

    def _handle_input(self):

        # Quit the game if escape or the x is pressed
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                quit()

            # Fire bullets if space is pressed
            elif (
                self.spaceship and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
            ):
                self.spaceship.shoot(self.volume)
            elif (
                event.type == pygame.KEYDOWN and event.key == pygame.K_p
            ):
                self.paused = not self.paused
            elif (
                self.paused and event.type == pygame.KEYDOWN and event.key == pygame.K_UP
            ):
                if self.volume < 10:
                    self.volume += 1
                    write_volume(self.volume)
            elif (
                self.paused and event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN
            ):
                if self.volume > 0:
                    self.volume -= 1
                    write_volume(self.volume)

        is_key_pressed = pygame.key.get_pressed()

        # Turn the ship if right or left is pressed, accelerate if up
        if self.spaceship:
            if is_key_pressed[pygame.K_RIGHT]:
                self.spaceship.rotate(clockwise=True)
            elif is_key_pressed[pygame.K_LEFT]:
                self.spaceship.rotate(clockwise=False)
            if is_key_pressed[pygame.K_UP]:
                self.spaceship.accelerate()
            elif is_key_pressed[pygame.K_DOWN]:
                self.spaceship.reverse()
            else:
                self.spaceship.decelerate()

    # Returns a list of objects in the game
    def _get_game_objects(self):
        game_objects = [*self.asteroids, *self.bullets, *self.powerups]

        if self.spaceship:
            game_objects.append(self.spaceship)
        return game_objects

    def _process_game_logic(self):
        if not self.paused:
            # Move current game objects
            for game_object in self._get_game_objects():
                game_object.move(self.screen)

            # Game ends if ship hits an asteroid
            if self.spaceship:
                for asteroid in self.asteroids[:]:
                    if asteroid.collides_with(self.spaceship):
                        if "shield" in self.effects:
                            del self.effect_timers[self.effects.index("shield")]
                            self.effects.remove("shield")
                            self.asteroids.remove(asteroid)
                            key = {3: 700, 2: 300, 1: 100}
                            self.score += key[asteroid.size]
                        else:
                            self.spaceship = None
                            self.message = "You Lost!"
                            self.ship_explosion.play()
                            self.h_scores = score_update(self.h_scores, self.score)
                            write_file("options", self.h_scores)
                            break

            if self.spaceship:
                for powerup in self.powerups[:]:
                    if powerup.collides_with(self.spaceship):
                        powerup.pickup_sound(self.volume)
                        if type(powerup) == Shield:
                            if "shield" in self.powerups:
                                self.effect_timers[self.effects.index("shield")] = 600
                            else:
                                self.effects.append("shield")
                                self.effect_timers.append(600)
                        elif type(powerup) == ShipSpeed:
                            self.spaceship.acceleration += .1
                        elif type(powerup) == BulletSpeed:
                            self.spaceship.bullet_speed += .5
                        elif type(powerup) == MultiShot:
                            if "multi" in self.powerups:
                                self.effect_timers[self.effects.index("multi")] = 200
                            else:
                                self.spaceship.bullet_amount = 3
                                self.effects.append("multi")
                                self.effect_timers.append(200)
                        self.powerups.remove(powerup)

            if self.spaceship.bullet_speed > 6:
                self.spaceship.bullet_speed = 6

            # Handles asteroids splitting if hit with a bullet
            for bullet in self.bullets[:]:
                for asteroid in self.asteroids[:]:
                    if asteroid.collides_with(bullet):
                        self.asteroids.remove(asteroid)
                        self.bullets.remove(bullet)
                        self.rock_break.play()
                        asteroid.split()
                        if self.spaceship:
                            self.score += 100
                        chance = random.randint(1, 10)
                        if chance <= 1:
                            chance = random.randint(1, 4)
                            if chance == 1:
                                self.powerups.append(MultiShot(bullet.position))
                            elif chance == 2:
                                self.powerups.append(ShipSpeed(bullet.position))
                            elif chance == 3:
                                self.powerups.append(BulletSpeed(bullet.position))
                            else:
                                self.powerups.append(Shield(bullet.position))
                        break

            # Remove bullets that have left the screen
            for bullet in self.bullets[:]:
                if not self.screen.get_rect().collidepoint(bullet.position):
                    self.bullets.remove(bullet)

            if not self.asteroids and self.spaceship:
                self.message = "You Won!"
                self.h_scores = score_update(self.h_scores, self.score)
                write_file("options", self.h_scores)

            if self.volume > 0:
                self.ship_explosion.set_volume(self.volume / 100)
                self.rock_break.set_volume(self.volume / 100)
            else:
                self.ship_explosion.set_volume(0)
                self.rock_break.set_volume(0)

            for x in range(len(self.effects)):
                x -= 1
                count = self.effect_timers[x]
                if count > 0:
                    self.effect_timers[x] -= 1
                elif count == 0:
                    if self.effects[x] is "multi":
                        self.spaceship.bullet_amount = 1
                    del self.effects[x]
                    del self.effect_timers[x]

            if len(self.asteroids) < 8:
                self.gen_asteroids(3)

    def _draw(self):
        if not self.paused:
            # Draw the background and all current game objects
            self.screen.blit(self.background, (0, 0))
            for game_object in self._get_game_objects():
                if type(Spaceship):
                    if "shield" in self.effects:
                        game_object.draw(self.screen, 2)
                    else:
                        game_object.draw(self.screen, 1)
                else:
                    game_object.draw(self.screen, 1)

            # If a message exists, draw it
            if self.message:
                print_text(self.screen, self.message, self.font_big, "center")

            print_text(self.screen, "Score: " + str(self.score), self.font_small, "top", "ghostwhite")

            if not self.spaceship or (self.spaceship and not self.asteroids):
                print_text(self.screen, "Highscores:", self.font_medium, "scoreboard", "ghostwhite")
                for x in range(5):
                    print_text(self.screen, (str(x+1) + ": " + str(self.h_scores[x])), self.font_small, ("score_" + str(x+1)), "ghostwhite")

            pygame.display.flip()
            self.clock.tick(60)
        else:
            self.screen.blit(self.background, (0, 0))
            print_text(self.screen, "Paused", self.font_big, "center", "darkblue")
            print_text(self.screen, "Score: " + str(self.score), self.font_small, "top", "ghostwhite")
            print_text(self.screen, "Highscores:", self.font_medium, "scoreboard", "ghostwhite")
            for x in range(5):
                print_text(self.screen, (str(x + 1) + ": " + str(self.h_scores[x])), self.font_small,
                           ("score_" + str(x + 1)), "ghostwhite")
            print_text(self.screen, "Volume: " + str(self.volume), self.font_small, "volume", "ghostwhite")

            pygame.display.flip()
            self.clock.tick(60)

    def gen_asteroids(self, num):
        # Generate asteroids at random location, far enough from the spaceship
        for _ in range(num):
            while True:
                position = get_random_position(self.screen)
                if (
                        position.distance_to(self.spaceship.position) >
                        self.MIN_ASTEROID_DISTANCE
                ):
                    break

            self.asteroids.append(Asteroid(position, self.asteroids.append))
