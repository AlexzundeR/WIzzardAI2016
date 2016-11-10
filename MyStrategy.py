import math
import random as rnd

from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from model.LaneType import LaneType
from model.Faction import Faction

class MyStrategy:
    def move(self, me: Wizard, world: World, game: Game, move: Move):
        self.initializeStrategy(me, game)
        self.initializeTick(me, world, game, move)

        # Постоянно двигаемся из-стороны в сторону, чтобы по нам было сложнее попасть.
        # Считаете, что сможете придумать более эффективный алгоритм уклонения? Попробуйте! ;)
        move.strafe_speed = game.wizard_strafe_speed if rnd.getrandbits(1) == 0 else -game.wizard_strafe_speed

        # Если осталось мало жизненной энергии, отступаем к предыдущей ключевой точке на линии.
        if (me.life < me.max_life * self.low_hp_factor):
            self.goTo(self.getPreviousWaypoint(),move)
            return


        nearestTarget = self.getNearestTarget()

        # Если видим противника ...
        if nearestTarget:
            distance = me.get_distance_to_unit(nearestTarget)

            # ... и он в пределах досягаемости наших заклинаний, ...
            if distance <= me.cast_range:
                angle = me.get_angle_to_unit(nearestTarget)

                # ... то поворачиваемся к цели.
                move.turn = angle

                # Если цель перед нами, ...
                if abs(angle) < game.staff_sector / 2.0:
                    # ... то атакуем.
                    move.action = ActionType.MAGIC_MISSILE
                    move.cast_angle = angle
                    move.min_cast_distance = distance - nearestTarget.radius + game.magic_missile_radius


                return

        # Если нет других действий, просто продвигаемся вперёд.
        self.goTo(self.getNextWaypoint(),move)

    waypoint_radius = 100.0
    low_hp_factor = 0.25

    waypointsByLane = {}
    waypoints = None
    random = None

    def initializeStrategy(self, me: Wizard, game: Game):
        if (self.random is None):
            self.random = 1
            rnd.seed(game.random_seed)

            mapSize = game.map_size

            self.waypointsByLane[LaneType.MIDDLE] = [(100.0, mapSize - 100.0),
                                                (600.0, mapSize - 200.0) if rnd.getrandbits(1) == 0 else (200.0, mapSize - 600.0),
                                                (800.0, mapSize - 800.0),
                                                (mapSize - 600.0, 600.0)
                                                ]


            self.waypointsByLane[LaneType.TOP] =[
                (100.0, mapSize - 100.0),
                (100.0, mapSize - 400.0),
                (200.0, mapSize - 800.0),
                (200.0, mapSize * 0.75),
                (200.0, mapSize * 0.5),
                (200.0, mapSize * 0.25),
                (200.0, 200.0),
                (mapSize * 0.25, 200.0),
                (mapSize * 0.5, 200.0),
                (mapSize * 0.75, 200.0),
                (mapSize - 200.0, 200.0)
            ]

            self.waypointsByLane[LaneType.BOTTOM] = [
                    (100., mapSize - 100.0),
                    (400., mapSize - 100.0),
                    (800., mapSize - 200.0),
                    (mapSize * 0.25, mapSize - 200.0),
                    (mapSize * 0.5, mapSize - 200.0),
                    (mapSize * 0.75, mapSize - 200.0),
                    (mapSize - 200., mapSize - 200.0),
                    (mapSize - 200.0, mapSize * 0.75),
                    (mapSize - 200.0, mapSize * 0.5),
                    (mapSize - 200.0, mapSize * 0.25),
                    (mapSize - 200.0, 200.0)
            ]

            switcher = {
                1:LaneType.TOP,
                2:LaneType.TOP,
                6:LaneType.TOP,
                7:LaneType.TOP,
                3:LaneType.MIDDLE,
                8:LaneType.MIDDLE,
                4:LaneType.BOTTOM,
                5:LaneType.BOTTOM,
                9:LaneType.BOTTOM,
                10:LaneType.BOTTOM
            }
            lane = switcher.get(int(me.id),"")
            self.waypoints = self.waypointsByLane.get(lane)

            # Наша стратегия исходит из предположения, что заданные нами ключевые точки упорядочены по убыванию
            # дальности до последней ключевой точки. Сейчас проверка этого факта отключена, однако вы можете
            # написать свою проверку, если решите изменить координаты ключевых точек.

            #Point2D lastWaypoint = waypoints[waypoints.length - 1];

            #Preconditions.checkState(ArrayUtils.isSorted(waypoints, (waypointA, waypointB) -> Double.compare(
            #        waypointB.getDistanceTo(lastWaypoint), waypointA.getDistanceTo(lastWaypoint)
            #)));

    #/**
    # * Сохраняем все входные данные в полях класса для упрощения доступа к ним.
    # */
    def initializeTick(self,me:Wizard, world:World, game: Game, move: Move):
        self.me = me
        self.world = world
        self.game = game


    #/**
    #* Данный метод предполагает, что все ключевые точки на линии упорядочены по уменьшению дистанции до последней
    # * ключевой точки. Перебирая их по порядку, находим первую попавшуюся точку, которая находится ближе к последней
    # * точке на линии, чем волшебник. Это и будет следующей ключевой точкой.
    # * <p>
    # * Дополнительно проверяем, не находится ли волшебник достаточно близко к какой-либо из ключевых точек. Если это
    # * так, то мы сразу возвращаем следующую ключевую точку.
    # */
    def getNextWaypoint(self):
        lastWaypointIndex = len(self.waypoints) - 1
        lastWaypoint = self.waypoints[lastWaypointIndex]

        for waypointIndex in range(0, lastWaypointIndex):
            waypoint = self.waypoints[waypointIndex]

            if (self.me.get_distance_to(*waypoint) <= self.waypoint_radius):
                return self.waypoints[waypointIndex + 1]


            if (self.getDistanceTo(waypoint,lastWaypoint) < self.me.get_distance_to(*lastWaypoint)):
                return waypoint

        return lastWaypoint

    #/**
    # * Действие данного метода абсолютно идентично действию метода {@code getNextWaypoint}, если перевернуть массив
    # * {@code waypoints}.
    # */
    def getPreviousWaypoint(self):
        firstWaypoint = self.waypoints[0]

        for waypointIndex in reversed(range(0,len(self.waypoints) - 1)):
            waypoint = self.waypoints[waypointIndex];

            if (self.me.get_distance_to(*waypoint) <= self.waypoint_radius):
                return self.waypoints[waypointIndex - 1]

            if (self.getDistanceTo(firstWaypoint,waypoint) < self.me.get_distance_to(*firstWaypoint)):
                return waypoint

        return firstWaypoint

    #/**
    # * Простейший способ перемещения волшебника.
    # */
    def goTo(self,point,move) :
        angle = self.me.get_angle_to(point[0], point[1])

        move.turn = angle

        if (abs(angle) < self.game.staff_sector / 4.0):
            move.speed = self.game.wizard_forward_speed

    #/**
    # * Находим ближайшую цель для атаки, независимо от её типа и других характеристик.
    # */
    def getNearestTarget(self):
        targets = []
        targets.extend(self.world.buildings)
        targets.extend(self.world.wizards)
        targets.extend(self.world.minions)

        nearestTarget = None
        nearestTargetDistance = 999999999

        for target in targets:
            if (target.faction == Faction.NEUTRAL or target.faction == self.me.faction):
                continue

            distance = self.me.get_distance_to_unit(target)

            if (distance < nearestTargetDistance) :
                nearestTarget = target
                nearestTargetDistance = distance

        return nearestTarget

    def getDistanceTo(self,fr, to):
        return math.hypot(fr[0]-to[0],fr[1] - to[1])

