import json
import zmq
import trio
import logging

class Socket:

    _waiting_time = 0.1

    def __init__(self, ctx=None, **kwargs):
        if ctx is None:
            ctx = zmq.Context.instance()
        self.ctx = ctx
        self._socket = self._make_socket()
        self._poller = zmq.Poller()
        self._poller.register(self._socket, zmq.POLLIN)

    def connect(self, addr):
        return self._socket.connect(addr)

    def listen(self, addr):
        return self._socket.bind(addr)

    def recv(self):
        while not self._poller.poll(1000*self._waiting_time):
            pass
        msg = self._socket.recv()
        return msg.decode("utf8")

    async def async_recv(self):
        while not self._poller.poll(1000*self._waiting_time):
            await trio.sleep(0)
        msg = self._socket.recv(zmq.DONTWAIT)
        return msg.decode("utf8")

    def recv_json(self):
        msg = self.recv()
        return json.loads(msg)

    async def async_recv_json(self):
        msg = await self.async_recv()
        return json.loads(msg)

    def send(self, msg):
        x = self._socket.send(msg.encode("utf8"))
        return x

    async def async_send(self, msg):
        return self.send(msg)

    def send_json(self, msg):
        msg_serialized = json.dumps(msg)
        r = self.send(msg_serialized)
        return r

    async def async_send_json(self, msg):
        self.send_json(msg)

    def close(self):
        return self._socket.close()


class PushSocket(Socket):
    def _make_socket(self):
        return self.ctx.socket(zmq.PUSH)


class PullSocket(Socket):
    def _make_socket(self):
        return self.ctx.socket(zmq.PULL)


class ReqSocket(Socket):
    def _make_socket(self):
        return self.ctx.socket(zmq.REQ)


class RepSocket(Socket):
    def _make_socket(self):
        return self.ctx.socket(zmq.REP)
