import bottle
import os
import random

directions = ['up', 'down', 'left', 'right']


@bottle.route('/')
def static():
    return "the server is running"


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data.get('game_id')
    board_width = data.get('width')
    board_height = data.get('height')

    head_url = '%s://%s/static/dwight.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#ffcc00',
        'head_url': head_url,
        'name': 'Dwight Snake',
        'taunt': 'Bears, Beets, Battlestar Galactica',
        'head_type': 'safe',
        'tail_type': 'round-bum'
    }


@bottle.post('/move')
def move():
    global directions
    directions = ['up', 'down', 'left', 'right']
    taunt = 'Bears, Beets, Battlestar Galactica'
    data = bottle.request.json

    snakes = data['snakes']
    height = data['height']
    width = data['width']
    # food = data['food']

    me = data['you']['body']['data']

    donthitsnakes(me[0], snakes)
    donthitwalls(me, width, height)
    donthittail(me)

    selftouchpoint = istouchingself(me[0], me)

    matrix = [[0] * height for _ in range(width)]
    board = buildboard(matrix, me, snakes)
    printmatrix(board)
    zeros = countmatrix0(matrix)
    print('zeros: ' + str(zeros))
    if selftouchpoint and len(directions) == 2:
        leftsize = rightsize = upsize = downsize = 0
        for dir in directions:
            if dir == 'left':
                leftmatrix = floodfill(board, getleft(me[0]))
                leftsize = zeros - leftmatrix
            if dir == 'right':
                rightmatrix = floodfill(board, getright(me[0]))
                rightsize = zeros - rightmatrix
            if dir == 'up':
                upmatrix = floodfill(board, getup(me[0]))
                upsize = zeros - upmatrix
            if dir == 'down':
                downmatrix = floodfill(board, getdown(me[0]))
                downsize = zeros - downmatrix

        if leftsize < len(me) + 2 and 'left' in directions:
            directions.remove('left')
            print('removing left, size: ' + str(leftsize))
        if rightsize < len(me) + 2 and 'right' in directions:
            directions.remove('right')
            print('removing right, size: ' + str(rightsize))
        if upsize < len(me) + 2 and 'up' in directions:
            directions.remove('up')
            print('removing up, size: ' + str(upsize))
        if downsize < len(me) + 2 and 'down' in directions:
            directions.remove('down')
            print('removing down, size: ' + str(downsize))


    if directions:
        direction = random.choice(directions)
    else:
        print('Goodbye cruel world')
        taunt = 'MICHAEL!!!!!!'
        direction = 'up'

    return {
        'move': direction,
        'taunt': taunt
    }


def printmatrix(matrix):
    for x in range(len(matrix)):
        print(matrix[x])


def floodfill(matrix, point):
    y = point['x']
    x = point['y']
    count = 0
    if matrix[x][y] == 0:
        matrix[x][y] = 1

        if x > 0 and matrix[x-1][y] != 1:
            count += 1
            return floodfill(matrix, getup(point))
        if x < len(matrix)-1 and matrix[x+1][y] != 1:
            count += 1
            return floodfill(matrix, getdown(point))
        if y > 0 and matrix[x][y-1] != 1:
            count += 1
            return floodfill(matrix, getleft(point))
        if y < len(matrix[0])-1 and matrix[x][y+1] != 1:
            count += 1
            return floodfill(matrix, getright(point))

    if count == 0:
        print('matrix after floodfill')
        printmatrix(matrix)
        print('matrix 0 count after fill: ' + str(countmatrix0(matrix)))
        return countmatrix0(matrix)


def countmatrix0(matrix):
    count = 0
    for x in range(len(matrix)):
        for y in range(len(matrix[x])):
            if matrix[x][y] == 0:
                count += 1

    return count


def buildboard(matrix, me, snakes):
    for point in me:
        x = point['x']
        y = point['y']
        matrix[y][x] = 1

    for snake in snakes['data']:
        for bodypart in snake['body']['data']:
            x = bodypart['x']
            y = bodypart['y']
            matrix[y][x] = 1

    return matrix



# # TODO This is still picking up non dangerous things as danger, and the diagonal stuff isn't working
# def adjacenttodanger(point, me, snakes, width, height):
#     """Checks if point is adjacent to snakes, edge of board, or itself(not neck/head) including diagonally"""
#     if istouchingwall(point, width, height):
#         print('touching wall')
#         return True
#     if istouchingsnake(point, me, snakes):
#         print('touching snake')
#         return True
#     if istouchingself(point, me):
#         print('touching self')
#         return True


def donthitsnakes(head, snakes):
    """goes through entire snake array and stops it from directly hitting any snakes"""
    global directions

    for snake in snakes['data']:
        for bodypart in snake['body']['data']:
            adj = findadjacentdir(head, bodypart)
            if adj and adj in directions:
                directions.remove(adj)


def donthittail(me):
    """Stops the snake from hitting it's own tail(anything past its head and neck)"""
    global directions
    head = me[0]

    for x in me:
        adj = findadjacentdir(head, x)
        if adj and adj in directions:
            directions.remove(adj)


def donthitwalls(me, width, height):
    """Stops the snake from hitting any walls"""
    global directions
    head = me[0]

    if head['x'] == 0:
        directions.remove('left')
    if head['x'] == width-1:
        directions.remove('right')
    if head['y'] == 0:
        directions.remove('up')
    if head['y'] == height-1:
        directions.remove('down')

#
#
# Below here are utility functions
#
#



def dirtouchingsnake(point, me, snakes):
    """checks if the point is touching a snake, not including this snakes head or neck"""
    head = me[0]
    neck = me[1]

    dirs = []

    for snake in snakes['data']:
        for bodypart in snake['body']['data']:
            if bodypart not in me:
                adj = findadjacentdir(point, bodypart)
                if adj:
                    dirs.append(adj)

    return dirs


def istouchingself(point, me):
    """checks if a point is touching this snake, not including head or neck"""
    self = me[2:]

    for x in self:
        if isadjacentdiagonal(point, x):
            return x

    return False


def dirtouchingself(point, me):
    """checks if a point is touching this snake, not including head or neck"""
    dirs = []

    for x in me:
        dir = findadjacentdir(point, x)
        if dir:
            dirs.append(dir)

    return dirs


def dirtouchingwall(point, width, height):
    """returns direction of wall if any"""
    walls = []
    if point['x'] == 0:
        walls.append('left')
    if point['x'] == width - 1:
        walls.append('right')
    if point['y'] == 0:
        walls.append('up')
    if point['y'] == height - 1:
        walls.append('down')

    return walls


def findadjacentdir(a, b):
    """Gives direction from a to b if they are adjacent(not diagonal), if they are not adjacent returns false"""
    ax = a['x']
    ay = a['y']
    bx = b['x']
    by = b['y']
    xdiff = ax - bx
    ydiff = ay - by

    if (xdiff in range(-1, 2) and ydiff == 0) or (ydiff in range(-1, 2) and xdiff == 0):
        if xdiff != 0:
            if xdiff > 0:
                return 'left'
            else:
                return 'right'
        if ydiff != 0:
            if ydiff > 0:
                return 'up'
            else:
                return 'down'
    else:
        return False


def isadjacentdiagonal(a, b):
    """Returns true if a is adjacent to be(with diagonal), if they are not adjacent returns false"""
    ax = a['x']
    ay = a['y']
    bx = b['x']
    by = b['y']
    xdiff = ax - bx
    ydiff = ay - by

    if xdiff in range(-1, 2) and ydiff in range(-1, 2):
        return True
    else:
        return False


def getleft(point):
    point['x'] -= 1
    return point


def getright(point):
    point['x'] += 1
    return point


def getup(point):
    point['y'] -= 1
    return point


def getdown(point):
    point['y'] += 1
    return point


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '127.0.0.1'),
        port=os.getenv('PORT', '8080'))
