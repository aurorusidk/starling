class Scope:
    def __init__(self, parent):
        self.parent = parent
        self.children = []
        self.name_map = {}

    def strict_lookup(self, name):
        return self.name_map.get(name)

    def lookup(self, name):
        s = self
        while not (val := s.strict_lookup(name)):
            s = s.parent
            if not s:
                return None
        return val

    def declare(self, name, value):
        self.name_map[name] = value
