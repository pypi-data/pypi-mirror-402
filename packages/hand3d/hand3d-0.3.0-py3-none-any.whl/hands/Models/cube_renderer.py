import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_grid():
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    grid_size = 20
    step = 2
    y_floor = -2.0

    for i in range(-grid_size, grid_size + 1, step):
        glVertex3f(i, y_floor, -grid_size)
        glVertex3f(i, y_floor, grid_size)
        glVertex3f(-grid_size, y_floor, i)
        glVertex3f(grid_size, y_floor, i)
    glEnd()

def draw_cube():
    vertices = [
        [1,1,-1], [1,-1,-1], [-1,-1,-1], [-1,1,-1],
        [1,1,1], [1,-1,1], [-1,-1,1], [-1,1,1]
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7)
    ]

    glColor3f(0.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

def start_renderer(shared_state):
    pygame.init()
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    gluPerspective(45, display[0]/display[1], 0.1, 100.0)
    glTranslatef(0.0, 0.0, -10)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        draw_grid()
        glPopMatrix()
        glPushMatrix()

        glTranslatef(shared_state["pos_x"], shared_state["pos_y"], shared_state["pos_z"])

        glRotatef(shared_state["rot_y"], 0, 1, 0)
        glRotatef(shared_state["rot_x"], 1, 0, 0)

        s = shared_state["zoom"]
        glScalef(s, s, s)
        draw_cube()
        glPopMatrix()

        pygame.display.flip()
        clock.tick(60)
