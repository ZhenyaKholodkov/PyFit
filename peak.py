class Point:
    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.index = index

    def set_x(self, x):
        self.x = x

    def get_x(self):
        return self.x

    def set_y(self, y):
        self.y = y

    def get_y(self):
        return self.y

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index


class Peak:
    def __init__(self, point, data_index):
        self.points = []
        self.points.append(point)
        self.data_index = data_index
        self.model = None

    def append_point(self, point):
        self.points.append(point)

    def set_model(self, model):
        self.model = model
