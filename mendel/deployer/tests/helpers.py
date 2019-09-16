from invoke import MockContext


class MockConnection(MockContext):
    """
    The fabric2 testing framework replies on invoke.
    We subclass it to add some functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'host' in kwargs:
            self.host = kwargs['host']

    def local(self, command, *args, **kwargs):
        return self._yield_result("__run", command)