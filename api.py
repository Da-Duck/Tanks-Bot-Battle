import json
import math
import random

class TankAPI:
    def __init__(self, view):
        """Инициализация API с данными поля зрения"""
        self.view = view
        self.self = view.get('self', {})
        self.enemies = view.get('enemies', [])
        self.walls = view.get('walls', [])
        self.water = view.get('water', [])
        self.dest = view.get('dest', [])
        self.bullets = view.get('bullets', [])
        self.map_width = view.get('map_width', 1280)
        self.map_height = view.get('map_height', 720)
    
    def get_position(self):
        """Получить текущую позицию танка"""
        return self.self.get('x', 0), self.self.get('y', 0)
    
    def get_angle(self):
        """Получить текущий угол поворота танка"""
        return math.radians(self.self.get('angle', 0))
    
    def get_health(self):
        """Получить текущее здоровье"""
        return self.self.get('health', 0)
    
    def get_ammo(self):
        """Получить текущее количество патронов"""
        return self.self.get('ammo', 0)
    
    def get_closest_enemy(self):
        """Найти ближайшего врага"""
        if not self.enemies:
            return None
        
        my_x, my_y = self.get_position()
        closest = None
        min_dist = float('inf')
        
        for enemy in self.enemies:
            ex, ey = enemy.get('x', 0), enemy.get('y', 0)
            dist = math.hypot(ex - my_x, ey - my_y)
            if dist < min_dist:
                min_dist = dist
                closest = enemy
        
        return closest
    
    def get_distance_to(self, target_x, target_y):
        """Расстояние до точки"""
        my_x, my_y = self.get_position()
        return math.hypot(target_x - my_x, target_y - my_y)
    
    def angle_to(self, target_x, target_y):
        """Угол до цели в радианах"""
        my_x, my_y = self.get_position()
        dx = target_x - my_x
        dy = target_y - my_y
        return math.atan2(dy, dx)
    
    def angle_diff(self, target_angle):
        """Разница между текущим углом и целевым (в радианах)"""
        current = self.get_angle()
        diff = (target_angle - current + math.pi) % (2 * math.pi) - math.pi
        return diff
    
    def is_enemy_visible(self, enemy):
        """Проверить, находится ли враг в поле зрения"""
        my_x, my_y = self.get_position()
        ex, ey = enemy.get('x', 0), enemy.get('y', 0)
        distance = self.get_distance_to(ex, ey)
        return distance <= 260  # FOV по умолчанию
    
    def should_shoot(self):
        """Решить, стоит ли стрелять"""
        enemy = self.get_closest_enemy()
        if not enemy or self.get_ammo() <= 0:
            return False
        
        ex, ey = enemy.get('x', 0), enemy.get('y', 0)
        return self.is_enemy_visible(enemy) and self.get_distance_to(ex, ey) < 200
    
    def get_command(self):
        """Сгенерировать команду на основе простой логики"""
        command = ""
        
        # Поворачиваемся к ближайшему врагу
        enemy = self.get_closest_enemy()
        if enemy:
            ex, ey = enemy.get('x', 0), enemy.get('y', 0)
            target_angle = self.angle_to(ex, ey)
            diff = self.angle_diff(target_angle)
            
            if abs(diff) > 0.1:  # Если отклонение больше ~5 градусов
                command += "l" if diff < 0 else "r"
            else:
                # Если мы смотрим на врага, двигаемся и пытаемся стрелять
                command += "f"
                if self.should_shoot():
                    command += "s"
        else:
            # Если врагов нет, двигаемся случайным образом
            command += random.choice("fffb")
        
        # Добавляем случайные действия для избежания застреваний
        if random.random() < 0.1:
            command += random.choice("lr")
        
        return command[:5]  # Ограничиваем длину команды 5 символами