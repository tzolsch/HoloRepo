import pygame as pg
from nltk.corpus import udhr
from main_reader import TextKneter
from kneter import parse_txt_file, make_translation, mapped_sents_2_words

pg.init()

class TextSpawn:
    def __init__(self, screen_rect, speed=1):
        self.srect = screen_rect
        self.size = 40
        self.color = (255, 0, 0)
        self.font = pg.font.SysFont('Arial', self.size)
        self.spawny = self.srect.centery
        self.spacing = 50
        self.timer = 0.0
        self.delay = 1
        self.px_speed = speed
        self.spawns = []
        self.space_width = 0
        self.measure_space()
        self.spoken = True

    def measure_space(self):
        space = self.font.render(' ', True, self.color)
        self.space_width = space.get_rect().width

    def spawn_text(self, txt='dummy'):
        spawn = self.make_text(txt)
        self.spawns.append(spawn)

    def make_text(self, message):
        text = self.font.render(message, True, self.color)
        if len(self.spawns) > 0:
            lag = max(self.spawns[-1][1].left + self.spawns[-1][1].width + self.space_width - self.srect.width, 0)
        else:
            lag = 0
        rect = text.get_rect(bottomleft=(self.srect.right + lag, self.spawny))
        return text, rect

    def update(self):
        if pg.time.get_ticks() - self.timer > self.delay:
            off_screen = 0
            self.timer = pg.time.get_ticks()
            for text, rect in self.spawns:
                rect.x -= self.px_speed
                if rect.bottom < -1:
                    off_screen += 1
            if len(self.spawns) > 0:
                if (self.spawns[-1][1].right < self.srect.right) & ~self.spoken:
                    self.spoken = True
                else:
                    self.spoken = False
            if off_screen > 0:
                self.spawns = self.spawns[off_screen:]

    def render(self, surf):
        for text, rect in self.spawns:
            surf.blit(text, rect)

#w_list = udhr.words('German_Deutsch-Latin1')
#w_list2 = udhr.words('English-Latin1')
w_list = parse_txt_file('/home/luenensc/PyPojects/TextKneter/texts/Constitution.txt', mode='words')
s_list = parse_txt_file('/home/luenensc/PyPojects/TextKneter/texts/Constitution.txt', mode='sents')
translated_s_list = make_translation(s_list, src='de', dest='en')
translated_w_list = mapped_sents_2_words(translated_s_list)[0]

reader = TextKneter([w_list,translated_w_list])

screen = pg.display.set_mode((800, 600))
screen_rect = screen.get_rect()
clock = pg.time.Clock()
done = False
cred = TextSpawn(screen_rect)

while not done:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            done = True
        if event.type == pg.KEYDOWN:
            if event.key in range(pg.K_0, pg.K_9 + 1):
                in_val = event.key%pg.K_0
                reader.alter_gprob(p=0.1*in_val)
                #print(reader.glitch_prob)
            if event.key == pg.K_x:
                reader.alter_corpus()

    if cred.spoken:
        reader.read_step()
        cred.spawn_text(reader.nxt_word)

    screen.fill((0, 0, 0))
    cred.update()
    cred.render(screen)
    pg.display.update()
    clock.tick(60)