class Collision:
    """Base class for collisions"""
    name = "collision"
    kind = 0
    def __init__(self, name = "coll", kind = 1):
        self.name = name
        self.kind = kind

class B(Collision):
    def __init__(self):
        pass

class MyColl(Collision, B):
    def __init__(self):
        self.post = foo("boo")

def foo(string):
    return string

