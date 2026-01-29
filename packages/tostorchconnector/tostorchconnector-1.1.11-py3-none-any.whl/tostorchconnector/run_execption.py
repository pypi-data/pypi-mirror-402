class StreamWriteExecption(Exception):
    def __init__(self, msg=""):
        self.msg = msg
        super(StreamWriteExecption, self).__init__(self, self.msg)

class StreamReadExecption(Exception):
    def __init__(self, msg=""):
        self.msg = msg
        super(StreamReadExecption, self).__init__(self, self.msg)