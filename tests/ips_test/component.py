from ipsframework import Component


class Driver(Component):
    def step(self, timestamp=0.0):
        self.services.call(self.services.get_port('WORKER'), 'step', 0.0)


class Worker(Component):
    def step(self, timestamp=0.0):
        self.services.send_portal_event(event_comment='Hello portal, from Worker')
