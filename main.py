import pygame
import os
import time
import random

pygame.font.init()

# Setup game window
WIDTH = 750
HEIGHT = 750
GAME_WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# load space ship images
RED_SPACESHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACESHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
YELLOW_SPACESHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))
BLUE_SPACESHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))  # Players ship

# Load laser images
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))

# Load background image
BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))


class Laser:
    def __init__(self, x, y, laser_img):
        self.x = x
        self.y = y
        self.laser_img = laser_img
        self.mask = pygame.mask.from_surface(self.laser_img)

    def draw(self, window):
        window.blit(self.laser_img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, HEIGHT):
        return not self.y <= HEIGHT and self.y >= 0

    def collision(self, obj):
        return collide(obj, self)


# Abstract ship class. It's abstract because we want to inherit from it.
class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, velocity, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):  # If laser moves off the screen.
                self.lasers.remove(laser)
            elif laser.collision(obj):  # if a collision occurs, decrement the health by 25.
                obj.health -= 25
                self.lasers.remove(laser)

            # Ensures the ships doesn't shoot too many lasers

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


# Player class inherits from Ship() class above
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)  # Super to instruct to use Ship() initialisation method
        self.ship_img = YELLOW_SPACESHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)  # Tells us where the pixels are for the ship
        self.max_health = health  # Used to decrement the players health

    def move_lasers(self, velocity, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):  # If laser moves off the screen.
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)

    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (
            self.x, self.y + self.ship_img.get_height() + 10,
            self.ship_img.get_width() * (self.health / self.max_health),
            10))


# Enemy ships class from Ship() class
class Enemy(Ship):
    COLOUR_MAP = {
        "red": (RED_SPACESHIP, RED_LASER),
        "green": (GREEN_SPACESHIP, GREEN_LASER),
        "blue": (BLUE_SPACESHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOUR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


# Collision function
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


# Main loop
def main():
    game_start = True
    FPS = 60  # Frames Per Second
    game_level = 0
    player_lives = 3
    main_game_font = pygame.font.SysFont("comicsans", 50)
    game_over_font = main_game_font = pygame.font.SysFont("comicsans", 60)
    player_win_font = main_game_font = pygame.font.SysFont("comicsans", 60)

    enemies = []  # Stores where the enemies are
    wave_length = 5
    enemy_velocity = 1  # Move slowly down the screen from the top

    player_velocity = 5
    laser_velocity = 4
    player = Player(300, 630)

    clock = pygame.time.Clock()

    game_over = False

    player_win = False

    game_over_counter = 0

    player_win_counter = 0

    # Function inside main() function so we can use local variables instead of having to pass arguments.
    def redraw_window():
        GAME_WINDOW.blit(BACKGROUND, (0, 0))
        lives_label = main_game_font.render(f"Lives: {player_lives}", 1, (255, 255, 255))
        level_label = main_game_font.render(f"Level: {game_level}", 1, (255, 255, 255))

        GAME_WINDOW.blit(lives_label, (10, 10))  # Print the amount of lives onto the left-hand corner of the screen.
        GAME_WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10,
                                       10))  # Print the current game level onto the right-hand corner of the screen.
        for enemy in enemies:
            enemy.draw(GAME_WINDOW)

        player.draw(GAME_WINDOW)

        # Player wins message
        if player_win == True:
            player_win_label = player_win_font.render("You win! Congratulations!", 1, (255, 255, 255))
            GAME_WINDOW.blit(player_win_label, (WIDTH / 2 - player_win_label.get_width() / 2, 350))           

        # Player loses message
        if game_over == True:
            game_over_label = game_over_font.render("You lose. GAME OVER", 1, (255, 255, 255))
            GAME_WINDOW.blit(game_over_label, (WIDTH / 2 - game_over_label.get_width() / 2, 350))

        pygame.display.update()  # Refreshes the display

    while game_start:
        clock.tick(FPS)  # Keeps the game running consistently on different systems.
        redraw_window()

        # Checks if the players lives is less-than or equal to 0 or if the player's health bar is less-than or equal to 0.
        if player_lives <= 0 or player.health <= 0:
            game_over = True
            game_over_counter += 1

        if game_over:
            if game_over_counter > FPS * 3:
                game_start = False
            else:
                continue

        # Checks if the player has completed game level 3 and wins
        if game_level == 3:
            player_win = True
            player_win_counter += 1

        if player_win:
            if player_win_counter > FPS * 3:
                game_start = False
            else:
                continue

        if len(enemies) == 0:
            game_level += 1  # When enemies reaches 0, increment level
            wave_length += 5  # Increase enemies by 5 on each level
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                              random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Checks if the user has closed the screen.
                game_start = False  # Terminate the game.

                # Key Mapping
        keys = pygame.key.get_pressed() 
        if keys[pygame.K_UP] and player.y - player_velocity > 0:
            player.y -= player_velocity  # Move 1 pixel upwards
        if keys[pygame.K_DOWN] and player.y + player_velocity + player.get_height() + 20 < HEIGHT:
            player.y += player_velocity  # Move 1 pixel downwards
        if keys[pygame.K_LEFT] and player.x - player_velocity > 0:
            player.x -= player_velocity  # Move 1 pixel to the left
        if keys[pygame.K_RIGHT] and player.x + player_velocity + player.get_width() < WIDTH:
            player.x += player_velocity  # Move 1 pixel to the right
        # Fire lasers
        if keys[pygame.K_SPACE]:
            player.shoot()

        # Move the enemies
        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player)

            if random.randrange(0, 4 * 60) == 1:
                enemy.shoot()
                # If a collision occurs between player and enemy, reduce player health by 10 and remove the enemy.
            if collide(enemy, player): 
                player.health -= 10
                enemies.remove(enemy)

            if enemy.y + enemy.get_height() > HEIGHT:
                player_lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_velocity, enemies)  # Check if laser has collided with enemies.

def main_menu():
    title_font = pygame.font.SysFont("comicsans", 70)
    game_start = True

    while game_start:
        GAME_WINDOW.blit(BACKGROUND, (0, 0))
        title_label = title_font.render("Click mouse to begin...", 1, (255, 255, 255))
        GAME_WINDOW.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, 350))
        pygame.display.update()

        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                game_start = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

    pygame.quit()


main_menu()
