class ThrPool:

    def __init__(this):

        this.threads = []

    def push(this, thr):
        this.threads.append(thr)

    def start(this):

        for thread in this.threads:
            thread.start()

    def wait(this):

        for thread in this.threads:
            thread.join()

    def getResult(this):

        r = []
        for thread in this.threads:
            r.append(thread.getResult())
        return r
