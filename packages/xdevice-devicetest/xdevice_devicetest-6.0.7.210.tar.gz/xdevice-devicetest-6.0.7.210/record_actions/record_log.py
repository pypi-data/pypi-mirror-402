from devicetest.log.logger import DeviceTestLog


class AdaptiveLOG:

    @classmethod
    def info(cls, message: str):
        DeviceTestLog.info(
            "<div class='aw3' id='rainbowText'>{}</div>".format(message))

    @classmethod
    def debug(cls, message: str):
        DeviceTestLog.info(
            "<div class='aw3' id='rainbowText'>{}</div>".format(message))
