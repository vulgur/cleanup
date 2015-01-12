class Resource(object):

    def __init__(self, name, path=None):
        self.name = name
        self.path = path
        self.ref = 0

    def add_ref(self):
        self.ref += 1

    def remove_ref(self):
        self.ref -= 1


class Layout(Resource):
    def __init__(self, name, path=None):
        super(Layout, self).__init__(name, path)
        self.drawables = set()
        self.layouts = set()
        self.strings = set()
        self.styles = set()
        self.animations = set()
        self.ids = set()


class Drawable(Resource):
    def __init__(self, name, path=None):
        super(Drawable, self).__init__(name, path)
        self.drawables = set()
        self.ids = set()


class String(Resource):
    def __init__(self, name):
        super(String, self).__init__(name)


class Style(Resource):
    def __init__(self, name):
        super(Style, self).__init__(name)
        self.parent = ""
        self.styles = set()
        self.drawables = set()
        self.animations = set()
        self.strings = set()
        self.layouts = set()
        self.ids = set()


class Animation(Resource):
    def __init__(self, name, path=None):
        super(Animation, self).__init__(name, path)
        self.drawables = set()
        self.animations = set()
        self.ids = set()


class ID(Resource):
    def __init__(self, name):
        super(ID, self).__init__(name)