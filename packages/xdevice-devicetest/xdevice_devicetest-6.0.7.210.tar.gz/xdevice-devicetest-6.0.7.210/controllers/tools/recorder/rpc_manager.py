try:
    import grpc
    from devicetest.controllers.tools.recorder.proto import scrcpy_pb2, scrcpy_pb2_grpc
except Exception:
    pass


class RpcManager(object):

    def __init__(self, device, host, port):
        self.device = device
        # max 10M
        self.channel = grpc.insecure_channel(target="{}:{}".format(host, port),
                                             options=[('grpc_max_receive_message_length', 10485760)])
        self.stub = scrcpy_pb2_grpc.ScrcpyServiceStub(self.channel)
        self.scrcpy_server = True

    def start_scrcpy(self):
        """
        start screen copy
        """
        if not self.scrcpy_server:
            self.device.log.debug("scrcpy server not response. skip scrcpy!")
            return False
        try:
            responses = self.stub.onStart(scrcpy_pb2.Empty(), timeout=5)
            for response in responses:
                self.device.log.info("start scrcpy response: {}".format(response))
            return True
        except grpc.RpcError as e:
            self.device.log.error("start scrcpy error: {}".format(e))
            self.scrcpy_server = False
            return False

    def stop_scrcpy(self):
        """
        stop screen copy
        """
        frame_count = 0
        if not self.scrcpy_server:
            return frame_count
        try:
            msg = self.stub.onEnd(scrcpy_pb2.Empty(), timeout=5)
            frame_count = msg.result
            self.device.log.debug("frame_count: {}".format(frame_count))
            return frame_count
        except grpc.RpcError as e:
            self.device.log.error("stop scrcpy error: {}".format(e))
            return frame_count
