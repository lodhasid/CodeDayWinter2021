from __future__ import division

import random

import cocos
from cocos import collision_model
from cocos.actions import *
from cocos.director import director
from cocos.scene import Scene
from cocos.text import Label
from pyglet import clock
from pyglet.window import key
from cocos.collision_model import CollisionManagerBruteForce
from pygame import Rect
import pyglet
import time


def collision(rect1, rect2):
    rect1 = Rect(rect1)
    rect2 = Rect(rect2)
    return rect1.colliderect(rect2)


def new_level_1():
    global scroller1, fuellayer, fueldisplaylayer
    fuellayer = FuelLayer()
    fueldisplaylayer = FuelDisplayLayer()
    scroller1 = cocos.layer.ScrollingManager()
    scroller1.add(Background1Layer())
    scroller1.add(fuellayer)
    scroller1.add(RockLayer())
    scroller1.add(RoverLayer())
    return Scene(scroller1, fueldisplaylayer)


def point_in_rect(point, rect):
    x = point[0]
    y = point[1]
    rectx = rect[0]
    recty = rect[1]
    rectw = rect[2]
    recth = rect[3]
    if rectx < x < rectx + rectw:
        if recty < y < recty + recth:
            return True
    return False


def new_level_2():
    global scroller2, bulletslayer, playerlayer, alienlayer, background2
    scroller2 = cocos.layer.ScrollingManager()
    background2 = Background2Layer()
    scroller2.add(background2)
    playerlayer = PlayerLayer()
    bulletslayer = BulletsLayer()
    alienlayer = AlienLayer()
    return Scene(scroller2, playerlayer, bulletslayer, alienlayer)


def fuelLose(dt, rover):
    director.replace(new_level_1())


def crash(dt, rover):
    director.replace(new_level_1())


def lvl1win(dt, rover):
    global win
    win = False
    director.replace(Scene(Level2Instructions()))


class Level2Instructions(cocos.layer.ColorLayer):
    is_event_handler = True
    
    def __init__(self):
        super(Level2Instructions, self).__init__(0, 0, 0, 255)
        bg = cocos.sprite.Sprite("instructions2.png")
        bg.scale = 1
        bg.position = self.width // 2, self.height // 2
        self.add(bg)
        clock.schedule_once(self.finish, 8)

    def finish(self, dt):
        director.replace(Scene(new_level_2()))

class SimpleLabel(cocos.text.Label):
    def __init__(self, text, size):
        super().__init__(text, font_name="Calibri", font_size=size, anchor_x="center", anchor_y="center")


class Rover(cocos.sprite.Sprite):
    def __init__(self, **kwargs):
        width, height = director.get_window_size()
        super().__init__("spacerover.png", **kwargs)
        self.position = width // 2, 100
        self.velocity = (0, 800)
        self.fuel = 1000
        self.dead = False
        self.do(RoverMove())


class RoverMove(cocos.actions.Move):
    def step(self, dt):
        rover = self.target
        if rover.dead:
            return
        if rover.fuel >= 1000:
            rover.fuel = 1000
        if rover.fuel <= 0:
            rover.fuel = 0
        fueldisplaylayer.fuelbar.element.text = "Fuel: " + str(int(rover.fuel // 10))
        fueldisplaylayer.fuelbar.draw()
        for fuel in fuels:
            if collision([rover.x, rover.y, rover.width, rover.height], [fuel.x, fuel.y, fuel.width, fuel.height]):
                rover.fuel += 200
                fuellayer.remove(fuel)
                fuels.remove(fuel)
                del fuel
                return
        collisions = [
            collision([rover.x, rover.y, rover.width, rover.height], [rock.x, rock.y, rock.width, rock.height]) for rock
            in rocks]
        if any(collisions):
            rover.velocity = (0, 0)
            
            youlose = Label("You Crashed", font_name="Calibri", font_size=80, anchor_x="center", anchor_y="center")
            youlose.position = (500, rover.position[1] + 300)
            rover.layer.add(youlose)
            rover.image = pyglet.resource.image("crashedrover.png")
            scroller1.set_focus(rover.x, rover.y + 200)
            rover.dead = True
            clock.schedule_once(crash, 2, rover)
        super().step(dt)
        if rover.fuel <= 0:
            rover.velocity = (0, 0)
            scroller1.set_focus(rover.x, rover.y + 200)
            youlose = Label("You Ran out of Fuel", font_name="Calibri", font_size=40, anchor_x="center",
                            anchor_y="center")
            youlose.position = (500, rover.position[1] + 300)
            rover.layer.add(youlose)
            rover.dead = True
            clock.schedule_once(fuelLose, 2, rover)
        elif rover.x < 43:
            rover.x = 43
            rover.velocity = (0, rover.velocity[1])
            rover.fuel -= 1.2
            scroller1.set_focus(rover.x, rover.y + 200)
            return
        elif rover.x > 1000 - 43:
            rover.x = 1000 - 43
            rover.velocity = (0, rover.velocity[1])
            rover.fuel -= 1.2
            scroller1.set_focus(rover.x, rover.y + 200)
            return
        elif rover.y > 16800 and not win:
            rover.y = 16801
            rover.velocity = (0, 0)
            scroller1.set_focus(rover.x, rover.y + 500)
            youwin = Label("Level 1 Complete - You reached the Kriptanium Mine", font_name="Calibri", font_size=30, anchor_x="center",
                           anchor_y="center")
            youwin.position = (500, rover.position[1] + 300)
            rover.layer.add(youwin)
            win = True
            clock.schedule_once(lvl1win, 2, rover)
            return
        else:
            rover.velocity = ((keyboard[key.RIGHT] - keyboard[key.LEFT]) * 500,
                              500 + (int(keyboard[key.UP]) * 2 - int(keyboard[key.DOWN])) * 100)
            rover.fuel -= 1.2
            scroller1.set_focus(rover.x, rover.y + 200)
            # you win! lvl1 end


class PlayerMove(cocos.actions.Move):
    def step(self, dt):
        global win
        print(win)
        super(PlayerMove, self).step(dt)
        plyr = self.target
        if win:
            if plyr.x >= 600: plyr.stateMoving = 1
            if plyr.stateMoving == 1:
                plyr.velocity = (-600, 0)
                plyr.x1 += 10
                if plyr.x1 + 923 > 2000:
                    plyr.velocity = (0, 0)
                    win = False
                    clock.schedule_once(alienlayer.win_display, 2)
            else:
                plyr.velocity = (200, 0)
                plyr.x1 = plyr.x
            scroller2.set_focus(plyr.x1 + 423, 300)
            return
        if plyr.y < plyr.height // 2 + 10:
            plyr.velocity = (0, 0)
            plyr.y = plyr.height // 2 + 10
        elif plyr.y > 600 - plyr.height // 2 - 10:
            plyr.velocity = (0, 0)
            plyr.y = 600 - plyr.height // 2 - 10
        else:
            plyr.velocity = (0, (keyboard[key.UP] - keyboard[key.DOWN]) * 400)


class BulletMove(cocos.actions.Move):
    def step(self, dt):
        super(BulletMove, self).step(dt)
        for alien in aliens:
            if not alien.dead and collision([self.target.x, self.target.y, self.target.width, self.target.height],
                                                 [alien.x, alien.y, alien.width, alien.height]):
                alien.dead = True
                alien.image = pyglet.resource.image("deadalien.png")
                self.target.kill()
                break
        if alienlayer.lose:
            return
        numaliens = 0
        for alien in aliens:
            if not alien.dead:
                numaliens += 1
        if numaliens == 0:
            alienlayer.newwave(alienlayer.wave * 5 + 5)
        self.target.velocity = (750, 0)


class AlienMove(cocos.actions.Move):
    def step(self, dt):
        super(AlienMove, self).step(dt)
        if self.target.dead:
            self.target.velocity = (0, 0)
            return
        if self.target.x < 20:
            for alien in aliens:
                alien.dead = True
            youlose = Label("You Lose - an alien got past you", font_name="Calibri", font_size=50, anchor_x="center", anchor_y="center")
            alienlayer.lose = True
            youlose.position = director.get_window_size()[0] // 2, director.get_window_size()[1] // 2
            alienlayer.add(youlose)
            clock.schedule_once(start_lvl_2, 3)
        self.target.velocity = (random.randint(-120, -60), random.randint(-20, 20))

def start_lvl_2(dt):
    director.replace(new_level_2())

class Menu(cocos.layer.ColorLayer):
    is_event_handler = True
    
    def __init__(self):
        super(Menu, self).__init__(20, 20, 20, 255)
        self.title = cocos.text.Label(
            "Galaxy Hopper!",
            font_name="Calibri",
            font_size=32,
            anchor_x="center",
            anchor_y="center"
        )
        self.title.position = self.width / 2, self.height / 2 + 70
        self.add(self.title)
        self.playBtn = cocos.layer.ColorLayer(200, 200, 200, 255, 220, 70)
        self.playBtn.position = self.width // 2 - 110, self.height // 2 - 75
        self.playBtnText = Label("Play", anchor_x="center", anchor_y="center", font_name="Calibri", font_size=20,
                                 color=(0, 0, 0, 255))
        self.playBtnText.position = (self.width // 2, self.height // 2 - 40)
        self.add(self.playBtn)
        self.add(self.playBtnText)
    
    def on_mouse_motion(self, x, y, dx, dy):
        if point_in_rect([x, y], [self.playBtn.x, self.playBtn.y, self.playBtn.width, self.playBtn.height]):
            self.playBtn.color = (150, 150, 150)
        else:
            self.playBtn.color = (200, 200, 200)
        self.playBtn.draw()
    
    def on_mouse_press(self, x, y, dx, dy):
        if point_in_rect([x, y], [self.playBtn.x, self.playBtn.y, self.playBtn.width, self.playBtn.height]):
            director.replace(Scene(Instructions()))


class Instructions(cocos.layer.ColorLayer):
    is_event_handler = True
    
    def __init__(self):
        super().__init__(30, 30, 30, 255)
        
        self.instructions = cocos.sprite.Sprite("instructions.png")
        self.instructions.position = self.width // 2, self.height // 2 + 90
        self.add(self.instructions)
        
        self.playBtn = cocos.layer.ColorLayer(200, 200, 200, 255, 220, 70)
        self.playBtn.position = self.width // 2 - 110, 90
        self.playBtnText = Label("Play", anchor_x="center", anchor_y="center", font_name="Calibri", font_size=20,
                                 color=(0, 0, 0, 255))
        self.playBtnText.position = (self.width // 2, 125)
        self.add(self.playBtn)
        self.add(self.playBtnText)
    
    def on_mouse_motion(self, x, y, dx, dy):
        if point_in_rect([x, y], [self.playBtn.x, self.playBtn.y, self.playBtn.width, self.playBtn.height]):
            self.playBtn.color = (150, 150, 150)
        else:
            self.playBtn.color = (200, 200, 200)
        self.playBtn.draw()
    
    def on_mouse_press(self, x, y, dx, dy):
        if point_in_rect([x, y], [self.playBtn.x, self.playBtn.y, self.playBtn.width, self.playBtn.height]):
            director.replace(Scene(Level1Instructions()))


class Level1Instructions(cocos.layer.ColorLayer):
    def __init__(self):
        super().__init__(30, 30, 30, 255)
        bg = cocos.sprite.Sprite("instructions1.png")
        bg.scale = 1
        bg.position = self.width // 2, self.height // 2
        self.add(bg)
        clock.schedule_once(self.finish, 8)
    
    def finish(self, dt):
        director.replace(Scene(new_level_1()))


class RoverLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        width, height = director.get_window_size()
        super().__init__()
        self.rover = Rover()
        self.add(self.rover)
        self.rover.layer = self


class FuelDisplayLayer(cocos.layer.ColorLayer):
    is_event_handler = True
    
    def __init__(self):
        super().__init__(0, 0, 0, 0)
        self.fuelbar = Label("Fuel: 100", anchor_x="center", anchor_y="center", font_name="Calibri", font_size=20)
        self.fuelbar.position = 900, 550
        self.add(self.fuelbar)


class RockLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        global rocks
        super().__init__()
        self.px_height = 17400
        self.px_width = 1000
        rocks = []
        for section in range(1, 7):
            for rocknum in range(4):
                min_y = section * 2400
                max_y = (section + 1) * 2400
                y = random.randint(min_y, max_y)
                x = random.randint(20, 980)
                rock = cocos.sprite.Sprite("rock.png", position=(x, y),
                                           scale=0.65)
                rock.cshape = collision_model.AARectShape((x, y), rock.width // 2, rock.height // 2)
                rocks.append(rock)
                self.add(rock)


class FuelLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        global fuels
        super().__init__()
        self.px_height = 17400
        self.px_width = 1000
        fuels = []
        for section in range(7):
            for fuelnum in range(random.choice([1, 1, 2, 2, 2, 2, 3, 3, 3])):
                min_y = section * 2400
                max_y = (section + 1) * 2400
                y = random.randint(min_y, max_y)
                x = random.randint(20, 980)
                fuel = cocos.sprite.Sprite("fuel.png", position=(x, y),
                                           scale=0.2)
                fuels.append(fuel)
                self.add(fuel)


class Background1Layer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        super().__init__()
        bgs = []
        for x in range(7):
            bg = cocos.sprite.Sprite("lvl1bg.png")
            bg.x, bg.y = bg.width // 2, bg.height // 2 + x * 2400
            bgs.append(bg)
            self.add(bg)
        finish = cocos.sprite.Sprite("kriptaniummine.png")
        finish.x, finish.y = finish.width // 2, finish.height // 2 + len(bgs) * 2400
        self.add(finish)
        
        self.px_width = 1000
        self.px_height = 2400 * len(bgs) + finish.height


class Background2Layer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        super(Background2Layer, self).__init__()
        self.bg = cocos.sprite.Sprite("lvl2bg.png")
        self.bg.position = self.bg.width // 2, self.bg.height // 2
        self.add(self.bg)
        
        self.px_width = 2000
        self.px_height = 600


class Player(cocos.sprite.Sprite):
    is_event_handler = True
    
    def __init__(self):
        super(Player, self).__init__("player.png")
        self.position = (100, 300)
        self.velocity = (0, 0)
        self.stateMoving = 0
        self.do(PlayerMove())


class Bullet(cocos.sprite.Sprite):
    is_event_handler = True
    
    def __init__(self, x, y):
        super(Bullet, self).__init__("bullet.png")
        self.position = (x, y)
        self.velocity = (750, 0)
        self.do(BulletMove())


class PlayerLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        global player
        super(PlayerLayer, self).__init__()
        player = Player()
        self.add(player)
    
    def on_key_press(self, symbol, modifiers):
        global lastbullettime
        print("keypress")
        if symbol == key.SPACE:
            timern = time.time()
            if timern - lastbullettime < .28:
                return
            lastbullettime = time.time()
            bullet = Bullet(player.x + player.width, player.y + player.height - 100)
            bullets.append(bullet)
            bulletslayer.add(bullet)


class BulletsLayer(cocos.layer.Layer):
    is_event_handler = True
    
    def __init__(self):
        global bullets
        global lastbullettime
        super().__init__()
        lastbullettime = time.time()
        bullets = []


class AlienLayer(cocos.layer.Layer):
    is_event_handler = True
    
    def __init__(self):
        global aliens
        super(AlienLayer, self).__init__()
        aliens = []
        self.lose = False
        self.wave = 1
        for x in range(5):
            alien = Alien(1000, random.randint(80, 520))
            aliens.append(alien)
            self.add(alien)
    
    def newwave(self, numaliens):
        for alien in aliens:
            alien.image = pyglet.resource.image("nothing.png")
        if self.wave >= 1:
            clock.schedule_once(self.you_win, 3)
            return
        self.wave += 1
        for x in range(numaliens):
            alien = Alien(1000, random.randint(80, 520))
            aliens.append(alien)
            self.add(alien)
            
    def you_win(self, dt):
        global win
        win = True
        
    def win_display(self, dt):
        youwin = Label("Level 2 Complete - You reached the Zaxzium Pool", font_name="Calibri", font_size=30, anchor_x="center",
                       anchor_y="center")
        youwin.position = director.get_window_size()[0]//2, director.get_window_size()[1]//2
        self.add(youwin)
        clock.schedule_once(self.endGame, 3)
    
    def endGame(self, dt):
        print("hihi")
        director.replace(Scene(YouWin()))


class YouWin(cocos.layer.ColorLayer):
    def __init__(self):
        super(YouWin, self).__init__(0, 0, 0, 255)
        youwin = Label("You Win!!!", font_size=50, anchor_x="center", anchor_y="center")
        youwin.position = self.width // 2, self.height // 2
        self.add(youwin)
        clock.schedule_once(self.finishScreen, 3)
        
    def finishScreen(self, dt):
        director.replace(Scene(Finish()))


class Finish(cocos.layer.ColorLayer):
    is_event_handler = True
    
    def __init__(self):
        super(Finish, self).__init__(0, 0, 0, 255)
        
        self.bg = cocos.sprite.Sprite("finish.png")
        self.bg.position = self.width // 2, self.height // 2
        self.add(self.bg)
        
        self.playagainbtn = cocos.sprite.Sprite("blankBtn.png", scale=0.5)
        self.playagainbtn.position = self.width - 200, self.height - 130
        self.playagaintxt = Label("Play Again", font_size=30, color=(0, 0, 0, 255), anchor_x="center", anchor_y="center")
        self.playagaintxt.position = self.playagainbtn.position
        self.add(self.playagainbtn)
        self.add(self.playagaintxt)
    
    def on_mouse_press(self, x, y, dx, dy):
        boxx, boxy, = self.playagainbtn.position
        boxw, boxh = self.playagainbtn.width, self.playagainbtn.height
        if boxx - boxw//2 < x < boxx + boxw//2 and boxy - boxh //2 < y < boxy + boxh//2:
            director.replace(Scene(Level1Instructions()))


class Alien(cocos.sprite.Sprite):
    is_event_handler = True
    
    def __init__(self, x, y, **kwargs):
        super(Alien, self).__init__("alien.png", **kwargs)
        self.position = (x, y)
        self.dead = False
        self.velocity = (250, 0)
        self.do(AlienMove())

win = False
director.init(caption="GALAXY HOPPER!", width=1000, height=600)

keyboard = key.KeyStateHandler()
cocos.director.director.window.push_handlers(keyboard)

director.run(Scene(Level2Instructions()))
