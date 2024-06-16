import pygame
import time
import random

from models import Spaceship, Asteroid, Shield, ShipSpeed, BulletSpeed, MultiShot
from utils import load_sprite, get_random_position, print_text, load_sound, read_file, score_update, write_file, \
    write_volume


# This is the main class that will handle inputs, process game logic, and draw the sprites
class Vector:
    # How close asteroids can spawn to your ship
    MIN_ASTEROID_DISTANCE = 300

    def __init__(self):
        # Initialize the screen, load the background, and initialize the clock.
        self._init_pygame()
        self.screen = pygame.display.set_mode((1200, 600))
        self.background = load_sprite("space", False)
        self.clock = pygame.time.Clock()

        # A boolean to track if the game is paused
        self.paused = False

        # These will be used to display text and scores on the screen
        self.font_big = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.message = ""
        self.score = 0

        # Open the options file to get the current high scores and sound volume
        options = read_file("options")
        # Volume is on the first line, after the text "volume: "
        self.volume = int(options[0][9:])
        self.h_scores = []
        for line in options[1:]:
            # Scores are displayed on the next 5 lines after the text "score_x = "
            self.h_scores.append(line[10:-1])

        # Load general game sounds
        self.ship_explosion = load_sound("ship_explosion")
        self.rock_break = load_sound("rock_break")

        # Initialize list to hold various types of objects and initialize the spaceship in the center of the screen
        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.effects = []
        self.effect_timers = []

        # self.bullets.append is being passed as a callback function
        self.spaceship = Spaceship((600, 300), self.bullets.append)

        # The game starts with 6 asteroids on the screen
        self.gen_asteroids(6)

    # This main loop calls each of the functions to run the game
    def main_loop(self):
        while True:
            self._handle_input()
            self._process_game_logic()
            self._draw()

            # If the game is over or the player has won, wait a few seconds and then restart the game
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

            # If the P key is pressed pause or unpause the game
            elif (
                event.type == pygame.KEYDOWN and event.key == pygame.K_p
            ):
                self.paused = not self.paused

            # If the game is paused the player can use the arrow keys to adjust the volume
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

        # Turn the ship if right or left is pressed, accelerate if up, reverse if down, decelerate if nothing is pressed
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

    # Main logic is processed here every frame
    def _process_game_logic(self):
        # No logic is processed if the game is paused
        if not self.paused:

            # Move current game objects
            for game_object in self._get_game_objects():
                game_object.move(self.screen)

            # Game ends if ship hits an asteroid
            if self.spaceship:
                for asteroid in self.asteroids[:]:
                    if asteroid.collides_with(self.spaceship):

                        # Check to see if the player has a shield, if yer, remove it and provide points
                        if "shield" in self.effects:
                            del self.effect_timers[self.effects.index("shield")]
                            self.effects.remove("shield")
                            self.asteroids.remove(asteroid)
                            key = {3: 700, 2: 300, 1: 100}
                            self.score += key[asteroid.size]

                        # If there is no shield, display lose message, update scores, and end the function
                        else:
                            self.spaceship = None
                            self.message = "You Lost!"
                            self.ship_explosion.play()
                            self.h_scores = score_update(self.h_scores, self.score)
                            write_file("options", self.h_scores)
                            break

            # Applies different powerups when the ship touches them
            if self.spaceship:
                for powerup in self.powerups[:]:
                    if powerup.collides_with(self.spaceship):
                        powerup.pickup_sound(self.volume)
                        if type(powerup) == Shield:
                            if "shield" in self.powerups:
                                self.effect_timers[self.effects.index("shield")] = 600

                            # If the player already has a shield, extend its duration
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

                        # Once picked up, remove the powerup from the screen
                        self.powerups.remove(powerup)

            # Limit max bullet speed
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

                        # Chance to randomly generate a powerup when an asteroid is hit
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

            # If the player manages to destroy all asteroid, they win.
            # This is legacy code from before the game generated new asteroids over time
            # This could be removed, or changed to trigger a win state when a certain score is triggered
            if not self.asteroids and self.spaceship:
                self.message = "You Won!"
                self.h_scores = score_update(self.h_scores, self.score)
                write_file("options", self.h_scores)

            # Updates game volume
            if self.volume > 0:
                self.ship_explosion.set_volume(self.volume / 100)
                self.rock_break.set_volume(self.volume / 100)
            else:
                self.ship_explosion.set_volume(0)
                self.rock_break.set_volume(0)

            # Decrease the time remaining on powerups and remove them if time is up
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

            # Generate new asteroids if there are less than 8 on the screen
            if len(self.asteroids) < 8:
                self.gen_asteroids(3)

    # Draws all objects
    def _draw(self):

        # Different objects display if the game is paused
        if not self.paused:
            # Draw the background and all current game objects
            self.screen.blit(self.background, (0, 0))
            for game_object in self._get_game_objects():

                # An alternate sprite is displayed for the spaceship if it has a shield
                if type(Spaceship):
                    if "shield" in self.effects:
                        game_object.draw(self.screen, 2)
                    else:
                        game_object.draw(self.screen, 1)
                else:
                    game_object.draw(self.screen, 1)

            # If a message exists, draw it (Used for win and lose messages)
            if self.message:
                print_text(self.screen, self.message, self.font_big, "center")

            # Display the score at the top of the screen
            print_text(self.screen, "Score: " + str(self.score), self.font_small, "top", "ghostwhite")

            # If the game is over, display the high scores
            if not self.spaceship or (self.spaceship and not self.asteroids):
                print_text(self.screen, "Highscores:", self.font_medium, "scoreboard", "ghostwhite")
                for x in range(5):
                    print_text(self.screen, (str(x+1) + ": " + str(self.h_scores[x])),
                               self.font_small, ("score_" + str(x+1)), "ghostwhite")

            # Move the clock forward
            pygame.display.flip()
            self.clock.tick(60)

        # Draw these if the game is paused
        else:
            self.screen.blit(self.background, (0, 0))
            print_text(self.screen, "Paused", self.font_big, "center", "darkblue")
            print_text(self.screen, "Score: " + str(self.score), self.font_small, "top", "ghostwhite")
            print_text(self.screen, "Highscores:", self.font_medium, "scoreboard", "ghostwhite")
            for x in range(5):
                print_text(self.screen, (str(x + 1) + ": " + str(self.h_scores[x])), self.font_small,
                           ("score_" + str(x + 1)), "ghostwhite")

            # Display the volume so that it can be changed by the player
            print_text(self.screen, "Volume: " + str(self.volume), self.font_small, "volume", "ghostwhite")

            pygame.display.flip()
            self.clock.tick(60)

    # A helper function to regenerate random asteroid positions
    # until they are far enough away from the ship to be spawned
    def gen_asteroids(self, num):
        for _ in range(num):
            while True:
                position = get_random_position(self.screen)
                if (
                        position.distance_to(self.spaceship.position) >
                        self.MIN_ASTEROID_DISTANCE
                ):
                    break

            self.asteroids.append(Asteroid(position, self.asteroids.append))
