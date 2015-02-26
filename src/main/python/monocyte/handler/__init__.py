

def make_registrar():
    registry = set()

    def registrar(cls):
        registry.add(cls)
        # print("registering aws service %s" % cls.SERVICE_NAME)
        return cls

    registrar.all = registry
    return registrar

aws_handler = make_registrar()


class Resource(object):
    def __init__(self, resource, region=None):
        self.wrapped = resource
        self.region = region