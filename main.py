from math import fabs, sqrt, cos, sin, pi, floor, ceil
from random import uniform, randint, choice
from nameGen import getName
from vector import *
import pygame
#from pygame import gfxdraw
pygame.init()

pygame.font.init()
myfont = pygame.font.Font("fonts\pixelFont.ttf", 12)

fpsClock = pygame.time.Clock()
fps = 60

winWidth = 800
winHeight = 500
win = pygame.display.set_mode((winWidth, winHeight))
whiteBuff = pygame.Surface((winWidth, winHeight)).convert_alpha()

##
# ideas:
# deliveries 
# paid by distance
# enemies
# money in asteroids
# powerups?
# gas cost moneys
# most planets can refill gas

##
# to do:
# fix asteroids

# macros
BLACK = (0,0,0); WHITE = (255,255,255); EMPTY = (0,0,0,0)
DISC = [(0,0), (0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,1), (1,-1), (-1,-1)]
CLICK_PERIOD = fps * 10
DIAGONAL = sqrt(winWidth * winWidth + winHeight * winHeight)
# digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
# letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
CHUNK_SIZE = 1000
CHUNK_BORDER = 0.1 * CHUNK_SIZE
# game parameters
gravityConst = 400
fuelMult = 0.4

# variables
cam = Vector()
phys = []
globalTime = 0
wakeChunks = []
currentPlayerChunk = (-555, -555)

################################################################################ funcs

def isOutside(pos, border = 10):
	if pos[0] < upLeft()[0] - border or pos[0] > downRight()[0] + border or pos[1] < upLeft()[1] - border or pos[1] > downRight()[1] + border:
		return True
	return False

def point2screen(pos, parallax = 1):
	return Vector(pos[0] - cam[0]/parallax, pos[1] - cam[1]/parallax)
	
def point2screeni(pos, parallax = 1):
	return Vector(pos[0] + cam[0]/parallax, pos[1] + cam[1]/parallax)

def camStep(obj):
	global cam
	cam[0] = obj.pos[0] - winWidth/2
	cam[1] = obj.pos[1] - winHeight/2

def pos2chunk(pos):
	return (floor(pos[0]/CHUNK_SIZE), floor(pos[1]/CHUNK_SIZE))

def timeClick():
	return floor(globalTime / CLICK_PERIOD)  

def chunkDist(x,y):
	return int(sqrt((x[0] - y[0]) * (x[0] - y[0]) + (x[1] - y[1]) * (x[1] - y[1])))

def fuelFormula(cost):
	global fuel
	return ((100 - fuel)/100) * (3 * cost + 40) + (fuel / 100)*(cost + 10)

def explossion(pos, amount=15, power=1):
	for i in range(amount):
		Smoke(vectorCopy(pos), vectorUnitRandom()*power)

def string2tup(string):
	num1, num2 = "", ""
	numFlag = 1
	for c in string:
		if c == "(":
			continue
		elif c == ")":
			continue
		elif c == ",":
			numFlag = 2
		else:
			if numFlag == 1:
				num1 += c
			else:
				num2 += c
	return (int(num1), int(num2))

def loadChunks():
	global fuel, money
	file = open("chunks.txt")
	currentChunk = None
	planets = []
	world = {}
	for line in file:
		if len(line) <= 1:
			return {}
		words = line.split()
		if words[0] == "<chunk>":
			lineType, arg1 = line.split()
			currentChunk = string2tup(arg1)
		elif words[0] == "<mass>":
			m = Planet(tup2vec(string2tup(words[1])), int(words[2]), words[3])
			m.location = currentChunk
			planets.append(m)
		elif words[0] == "<\chunk>":
			c = Chunk()
			c.Id = currentChunk
			for i in planets:
				c.planets.append(i)
			world[currentChunk] = c
			planets = []
		elif words[0] == "<player>":
			r.reposition(Vector(float(words[1]), float(words[2])))
			fuel = float(words[3]); money = int(words[4])
	return world

def saveChunks():
	file = open("chunks.txt", "w")
	for key in worldChunks:
		file.write("<chunk>" + " ")
		file.write("(" + str(key[0]) + "," + str(key[1]) + ")" + " ")
		file.write("\n")
		for p in worldChunks[key].planets:
			file.write("<mass>" + " ")
			file.write("(" + str(p.pos[0]) + "," + str(p.pos[1]) + ")" + " ")
			file.write(str(p.radius) + " ")
			file.write(p.name)
			file.write("\n")
		file.write("<\chunk>\n")
	file.write("<player>" + " ")
	file.write(str(r.pos[0]) + " " + str(r.pos[1]) + " ")
	file.write(str(fuel) + " " + str(money))
	file.close()
		
def closestFive(x):
	return CHUNK_SIZE * round(x / CHUNK_SIZE)

def drawChunkBorder():
	x = closestFive(upLeft()[0])
	while x < downRight()[0]:
		pygame.draw.line(win, (200,200,200), point2screen((x,upLeft()[1])), point2screen((x,downRight()[1])))
		x += CHUNK_SIZE
	y = closestFive(upLeft()[1])
	while y < downRight()[1]:
		pygame.draw.line(win, (200,200,200), point2screen((upLeft()[0],y)), point2screen((downRight()[0],y)))
		y += CHUNK_SIZE

def isDiscovered(Id):
	if Id in worldChunks.keys():
		return True
	else:
		return False

def discover(Id):
	newChunk = Chunk()
	newChunk.new(Id)
	worldChunks[Id] = newChunk

def discoverAround(Id):
	result = []
	for i in DISC:
		Id2discover = (Id[0] + i[0], Id[1] + i[1])
		if isDiscovered(Id2discover):
			continue
		discover(Id2discover)
		result.append(Id2discover)
	return result

def actionJobAccept():
	global currentMenu, jobSurf
	job = r.docked.job
	r.currentJob[0] = job
	r.currentJob[1] = chunkDist(currentPlayerChunk, job.location) * 10
	currentMenu.destroy()
	jobSurf = myfont.render("job: " + r.docked.job.name + " " + str(r.docked.job.location), False, WHITE)

def actionJobDeliver():
	global jobSurf
	addMoney(r.currentJob[1])
	r.currentJob[0] = None
	r.currentJob[1] = 0
	currentMenu.destroy()
	jobSurf = None

def actionRefuel():
	global fuel
	decMoney(int(fuelFormula(r.docked.fuelCost)))
	fuel = 100
	
def decMoney(amount):
	global money, moneySurf
	money -= amount
	moneySurf = myfont.render(str(money), False, WHITE)

def addMoney(amount):
	global money, moneySurf
	money += amount
	moneySurf = myfont.render(str(money), False, WHITE)

def drawHud():
	win.blit(gpsStringSurf, (5, winHeight - 15))
	win.blit(playerChunkSurf, (5 + gpsStringSurf.get_width() + 5, winHeight - 15))
	win.blit(moneyStringSurf, (150, winHeight - 15))
	win.blit(moneySurf, (150 + moneyStringSurf.get_width() + 5, winHeight - 15))
	pygame.draw.line(win, WHITE, (winWidth - 400 - 2, winHeight - 15), (winWidth - 400 - 2, winHeight - 6))
	pygame.draw.line(win, WHITE, (winWidth - 300 + 1, winHeight - 15), (winWidth - 300 + 1, winHeight - 6))
	pygame.draw.rect(win, WHITE, ((winWidth - 400, winHeight - 15), (fuel, 10)))	
	if jobSurf:
		win.blit(jobSurf, (winWidth - 300 + 15, winHeight - 15))

def upLeft(parralax = 1):
	return Vector(0,0) + cam/parralax

def downRight(parallax = 1):
	return Vector(winWidth, winHeight) + cam/parallax

################################################################################ Classes
class Smoke:
	def __init__(self, pos, vel):
		phys.append(self)
		self.pos = pos
		self.vel = vel*2
		self.vel.rotate(uniform(-0.5,0.5))
		self.radius = randint(1,5)
	def step(self):
		self.pos += self.vel
		self.radius -= 0.25
		if self.radius <= 0:
			phys.remove(self)
	def draw(self):
		pygame.draw.circle(whiteBuff, WHITE, point2screen(self.pos), self.radius)

class Planet:
	#_reg = []
	def __init__(self, pos, radius = -1, name = ""):
		#Mass._reg.append(self)
		#phys.append(self)
		self.pos = pos
		if radius == -1:
			radius = randint(40, 70)
		self.mass = max(1,radius/50)
		self.radius = radius
		self.selected = False
		if name == "":
			self.name = getName(randint(3,7))
		else:
			self.name = name
		self.location = None
		self.fuelCost = randint(1,10)
		self.job = None
		self.ring = True if randint(0, 10) == 0 else False
	def step(self):
		pass
	def makeJob(self):
		chunk = choice(list(worldChunks.values()))
		while len(chunk) == 0:
			chunk = choice(list(worldChunks.values()))
		planet = choice(chunk.planets)
		self.job = planet
		
	def draw(self):
		if self.ring:
			pygame.draw.ellipse(whiteBuff, WHITE, (point2screen(self.pos + Vector(-self.radius * 2, -self.radius/2)), (self.radius * 4, self.radius)))
			pygame.draw.ellipse(whiteBuff, BLACK, (point2screen(self.pos + Vector(-self.radius * 2, -self.radius/2)*(3/4)), (self.radius * 3, self.radius * (3/4))))
		pygame.draw.circle(whiteBuff, WHITE, point2screen(self.pos), self.radius)
		
		if self.selected:
			pygame.draw.circle(whiteBuff, BLACK, point2screen(self.pos), 10)
		if self == r.currentJob[0] and floor(globalTime/(fps/2) % 2) == 0:
			pygame.draw.circle(whiteBuff, BLACK, point2screen(self.pos), 10)
			
	def __str__(self):
		return self.name + " " + str(self.location)
	def __repr__(self):
		return str(self)
		
class Rocket:	
	def __init__(self):
		self.pos = Vector(winWidth/2, winHeight/2+100)
		self.vel = Vector()
		self.acc = Vector()
		self.dir = Vector(0,-1)
		self.bulletOverHeat = 0
		self.time = 0
		self.docked = None
		self.currentJob = [None, 0]
	def step(self):
		self.time += 1
		
		force = Vector()
		for p in worldChunks[currentPlayerChunk].planets:
			distance = dist(self.pos, p.pos)
			if distance < p.radius:
				continue
			direction = normalize(p.pos - self.pos)
			force += direction * ((gravityConst * p.mass) / (distance * distance))
		self.acc += force
		
		self.vel += self.acc
		self.vel *= 0.99
		
		count = 0
		for p in worldChunks[currentPlayerChunk].planets:
			distance = dist(self.pos, p.pos)
			if distance < p.radius + 5:
				overlap = distance - p.radius - 5
				self.pos -= ((self.pos - p.pos) / distance) * overlap
				r2p = p.pos - self.pos
				velMag = self.vel.getMag()
				if velMag > 3:
					pass
				r2p.setMag(velMag)
				velResp = self.vel - r2p
				self.vel = velResp * 0.2
			p.selected = False
			if distance < p.radius + 10:
				self.prepareDocking(p)
				self.docked = p
				p.selected = True
				count += 1
		if count == 0:
			self.docked = None
			global currentMenu
			if currentMenu:
				currentMenu.destroy()
				currentMenu = None

		self.pos += self.vel
		self.bulletOverHeat -= 1
		if self.bulletOverHeat < 0:
			self.bulletOverHeat = 0
		self.acc *= 0
	def prepareDocking(self, planet):
		global currentMenu, fuel
		if self.docked and currentMenu:
			return
		menu = Menu(Vector(winWidth - 200, winHeight - 200))
		currentMenu = menu
		menu.addString("planet: " + planet.name)
		if planet.job and not self.currentJob[0]:
			menu.addString("jobs:")
			menu.addString(planet.job.name + " " + str(planet.job.location))
			menu.addString("payment: " + str(chunkDist(planet.job.location, planet.location) * 10) + "$")
			menu.addButton("accept", "a", actionJobAccept)
		if planet is self.currentJob[0]:
			menu.addButton("deliver", "a", actionJobDeliver)
		
		menu.addButton("refuel: " + str(int(fuelFormula(planet.fuelCost))), "f", actionRefuel)
	
	def reposition(self, pos):
		self.pos[0] = pos[0]
		self.pos[1] = pos[1]
	
	def draw(self):
		points = [Vector(0,5), Vector(0,-5), Vector(15,0)]
		angle = self.dir.getAngle()
		for point in points:
			point.rotate(angle)
			point += self.pos
		pygame.draw.polygon(whiteBuff, WHITE, [point2screen(i) for i in points])

class Asteroid:
	_reg = []
	def __init__(self, pos, vel=None, radius = -1):
		phys.append(self)
		Asteroid._reg.append(self)
		self.pos = pos
		if vel:
			self.vel = vel
		else:
			self.vel = r.pos - self.pos + vectorUnitRandom() * randint(0, 100)
		self.vel.setMag(1)
		if radius == -1:
			self.radius = choice([15 ,25, 35])
		else:
			self.radius = radius
		self.reshape()
		self.angle = choice([0.01, -0.01])
	def step(self):
		self.pos += self.vel
		for p in self.points:
			p.rotate(self.angle)
		if isOutside(self.pos, 100):
			Asteroid._reg.remove(self)
			phys.remove(self)
		for p in worldChunks[pos2chunk(self.pos)].planets:
			distance = dist(self.pos, p.pos)
			if distance < self.radius + p.radius:
				overlap = distance - p.radius - self.radius
				self.pos -= ((self.pos - p.pos) / distance) * overlap
				r2p = p.pos - self.pos
				velMag = self.vel.getMag()
				r2p.setMag(velMag)
				velResp = self.vel - r2p
				self.vel = velResp
	def reshape(self):
		self.points = [Vector(cos(2*pi*i/9),sin(2*pi*i/9)) * (self.radius + randint(0,10)) for i in range(10)]
	def destroy(self):
		Asteroid._reg.remove(self)
		phys.remove(self)
	def hit(self):
		self.radius -= 10
		if self.radius <= 0:
			self.destroy()
			return
		self.reshape()
		velMag = self.vel.getMag()
		self.vel = vectorUnitRandom()
		self.vel.setMag(velMag)
		a = Asteroid(vectorCopy(self.pos), self.vel * -1, self.radius)
	def draw(self):
		points = [point2screen(self.pos + p) for p in self.points]
		pygame.draw.polygon(whiteBuff, WHITE, points)

class Bullet:
	def __init__(self, pos, vel):
		phys.append(self)
		self.pos = pos
		self.vel = vel*2
	def step(self):
		self.pos += self.vel
		if isOutside(self.pos):
			phys.remove(self)
			return
		for a in Asteroid._reg:
			if dist(self.pos, a.pos) < a.radius + 5:
				a.hit()
				phys.remove(self)
				explossion(self.pos)
				return
		for p in worldChunks[pos2chunk(self.pos)].planets:
			if dist(self.pos, p.pos) < p.radius:
				phys.remove(self)
				explossion(self.pos)
				return
	def draw(self):
		pygame.draw.line(whiteBuff, WHITE, point2screen(self.pos - self.vel), point2screen(self.pos + self.vel))

class Chunk:
	def __init__(self):
		self.Id = None
		self.planets = []
		self.timeUpdate = timeClick()
	def new(self, Id):
		self.Id = Id
		self.planetise()
	def planetise(self):
		chance = randint(0, 100)
		if chance >= 0 and chance < 70:
			amount = randint(2,8)
		elif chance >= 70 and chance < 80:
			amount = randint(1,4)
		else:
			amount = randint(0,2)
		
		for i in range(amount):
			goodPlace = False
			while not goodPlace:
				goodPlace = True
				x = randint(self.Id[0] * CHUNK_SIZE + CHUNK_BORDER, self.Id[0] * CHUNK_SIZE + CHUNK_SIZE - CHUNK_BORDER)
				y = randint(self.Id[1] * CHUNK_SIZE + CHUNK_BORDER, self.Id[1] * CHUNK_SIZE + CHUNK_SIZE - CHUNK_BORDER)
				radius = randint(40, 70)
				for planet in self.planets:
					if dist(Vector(x,y), planet.pos) < planet.radius + radius:
						goodPlace = False
						break
			m = Planet(Vector(x, y))
			m.location = self.Id
			self.planets.append(m)
		
	def wake(self):
		for p in self.planets:
			phys.append(p)
		wakeChunks.append(self)
		if self.timeUpdate != timeClick() or timeClick() == 0:
			self.timeUpdate = timeClick()
			for p in self.planets:
				p.makeJob()
	def __len__(self):
		return len(self.planets)
	def sleep(self):
		for p in self.planets:
			phys.remove(p)
	def __str__(self):
		return str(self.Id) + ", " + str(len(self.planets)) + " planets"
	def __repr__(self):
		return str(self)

class Menu:
	def __init__(self, winPos):
		self.winPos = winPos
		self.elements = []
		self.buttons = []
		self.currentHeight = 5
		self.dims = [0,0]
		self.rect = [winPos, self.dims]
	def addString(self, string):
		self.elements.append(MenuString(string, self.winPos + Vector(5, self.currentHeight)))
		self.currentHeight += self.elements[-1].height + 5
		self.dims[0] = max(self.dims[0], self.elements[-1].width + 15)
		self.dims[1] = self.currentHeight + 5
	def addButton(self, text, key, action):
		b = Button(text, key, self.winPos + Vector(5, self.currentHeight), action)
		self.elements.append(b)
		self.buttons.append(b)
		self.currentHeight += self.elements[-1].height + 5
		self.dims[0] = max(self.dims[0], self.elements[-1].width + 20)
		self.dims[1] = self.currentHeight
	def draw(self):
		pygame.draw.rect(win, WHITE, self.rect)
		for e in self.elements:
			e.draw()
	def destroy(self):
		for b in self.buttons:
			b.destroy()
		global currentMenu
		currentMenu = None
	
class MenuString:
	def __init__(self, string, winPos):
		self.winPos = winPos
		self.surf = myfont.render(string, False, BLACK)
		self.width = self.surf.get_width()
		self.height = self.surf.get_height()
	def draw(self):
		win.blit(self.surf, self.winPos)
	
class Button:
	_reg = []
	def __init__(self, text, key ,winPos, action = None):
		Button._reg.append(self)
		self.text = text
		self.selected = False
		self.action = action
		self.winPos = Vector()
		self.key = key
		self.surf = myfont.render(text + " " + "(" + key + ")", False, WHITE)
		self.width = self.surf.get_width()
		self.height = self.surf.get_height() + 10
		self.winPos = winPos
	def activate(self):
		print("action")
		if self.action:
			self.action()
	def step(self):
		pass
	def draw(self):
		pygame.draw.rect(win, BLACK, (self.winPos, (self.width + 10, self.height)))
		win.blit(self.surf, self.winPos + Vector(5,5))
	def destroy(self):
		Button._reg.remove(self)

################################################################################ Managers
starField = []#star = (pos, parallax, radius)

def starFieldManager():
	if randint(0,4) == 1:
		if len(starField) > 40:
			return
		parallax = uniform(1,6)#choice([2,3,4])
		radius = randint(1,3)
		place = randint(0,3)
		if place == 0:
			pos = Vector(downRight(parallax)[0], randint(int(upLeft(parallax)[1]), int(downRight(parallax)[1])))
		if place == 1:
			pos = Vector(randint(int(upLeft(parallax)[0]), int(downRight(parallax)[0])), upLeft(parallax)[1])
		if place == 2:
			pos = Vector(upLeft(parallax)[0], randint(int(upLeft(parallax)[1]), int(downRight(parallax)[1])))
		if place == 3:
			pos = Vector(randint(int(upLeft(parallax)[0]), int(downRight(parallax)[0])), downRight(parallax)[1])
		starField.append((pos, parallax, radius))

def drawStarField():
	for s in starField:
		pygame.draw.circle(whiteBuff, WHITE, point2screen(s[0], s[1]), s[2])
		if s[0][0] < upLeft(s[1])[0] - 10 or s[0][0] > downRight(s[1])[0] + 10 or s[0][1] < upLeft(s[1])[1] - 10 or s[0][1] > downRight(s[1])[1] + 10:
			starField.remove(s)

def asteroidManager():
	if globalTime % 60 == 0 and randint(0,10) == 1:
		if len(Asteroid._reg) > 10:
			return
		place = randint(0,3)
		if place == 0:
			pos = Vector(downRight()[0] + 50, randint(int(upLeft()[1]), int(downRight()[1])))
		if place == 1:
			pos = Vector(randint(int(upLeft()[0]), int(downRight()[0])), upLeft()[1] - 50)
		if place == 2:
			pos = Vector(upLeft()[0] - 50, randint(int(upLeft()[1]), int(downRight()[1])))
		if place == 3:
			pos = Vector(randint(int(upLeft()[0]), int(downRight()[0])), downRight()[1] + 50)
		Asteroid(pos)

################################################################################ Setup

r = Rocket()
phys.append(r)
money = 100
fuel = 100

worldChunks = loadChunks()

currentMenu = None
playerChunkSurf = None
moneyStringSurf = myfont.render("money: ", False, WHITE)
gpsStringSurf = myfont.render("gps: ", False, WHITE)
moneySurf = myfont.render(str(money), False, WHITE)
jobSurf = None
################################################################################ Main Loop
run = True
while run:
	fpsClock.tick(fps)
	#pygame.time.delay(1)
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		#mouse pressed once(MOUSEBUTTONUP for release):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			#mouse position:
			mouse_pos = pygame.mouse.get_pos()
			# print("mouse pressed once")
		if event.type == pygame.KEYDOWN:
			# key pressed once:
			if event.key == pygame.K_r:
				decMoney(money)
				addMoney(100)
				fuel = 100
			if event.key == pygame.K_a:
				for button in Button._reg:
					if button.key == "a":
						button.activate()
						break
			if event.key == pygame.K_f:
				for button in Button._reg:
					if button.key == "f":
						button.activate()
						break
			if event.key == pygame.K_s:
				print("current job:", r.currentJob)
				# print("ref:", fuelFormula(r.docked.fuelCost))
				# print("time click:", timeClick())
				# print(len(Button._reg))
				# print("chunk", currentPlayerChunk)
				# print("phys:", len(phys))
				# print("wake:", len(wakeChunks))
				# print("aste:", len(Asteroid._reg))
	keys = pygame.key.get_pressed()
	if keys[pygame.K_ESCAPE]:
		run = False
	#key hold:
	if keys[pygame.K_RIGHT]:
		r.dir.rotate(0.1)
	if keys[pygame.K_LEFT]:
		r.dir.rotate(-0.1)
	if keys[pygame.K_UP]:
		r.acc += r.dir * 0.05
		Smoke(vectorCopy(r.pos), r.dir * -1)
		fuel -= 0.05 * fuelMult
		if fuel <= 0:
			fuel = 0
	if keys[pygame.K_z]:
		r.acc += r.dir * 0.2
		Smoke(vectorCopy(r.pos), r.dir * -1)
		fuel -= 0.2 * fuelMult
		if fuel <= 0:
			fuel = 0	
	if keys[pygame.K_SPACE]:
		if r.bulletOverHeat == 0:
			Bullet(vectorCopy(r.pos), r.dir*5)
			r.bulletOverHeat = 10
	# step:
	globalTime += 1
	camStep(r)
	
	playerChunk = pos2chunk(r.pos)
	if playerChunk != currentPlayerChunk:
		# switch chunk
		currentPlayerChunk = playerChunk
		playerChunkSurf = myfont.render(str(currentPlayerChunk), False, WHITE)
		
		# discover around:
		discovered = discoverAround(currentPlayerChunk)
		for i in discovered:
			print("new chunk: ", i)
		# sleep all
		for i in wakeChunks:
			i.sleep()
		wakeChunks = []
		# wake in disc
		for d in DISC:
			Id2wake = (currentPlayerChunk[0] + d[0], currentPlayerChunk[1] + d[1])
			worldChunks[Id2wake].wake()
	
	for i in phys:
		i.step()
	starFieldManager()
	asteroidManager()
	
	# draw:
	whiteBuff.fill(EMPTY)
	drawStarField()
	for i in phys:
		i.draw()
	win.fill(BLACK)
	sPos = Vector(0,0)
	win.blit(whiteBuff, sPos)
	# drawChunkBorder()
	
	if currentMenu:
		currentMenu.draw()
	
	drawHud()
	
	pygame.display.update()
pygame.quit()

saveChunks()








