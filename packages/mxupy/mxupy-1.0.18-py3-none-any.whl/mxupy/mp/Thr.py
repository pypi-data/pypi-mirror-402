import threading


class Thr(threading.Thread):

    def __init__(this, func, args=()):
        super(Thr, this).__init__()
        this.func = func
        this.args = args

    def run(this):
        this.result = this.func(*this.args)

    def getResult(this):
        try:
            return this.result
        except Exception:
            return None
