import platform
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep

from libsrg_log2web import FlaskApp, Log2Web
from libsrg.LoggingAppBase import LoggingAppBase

class Main(LoggingAppBase):

    def __init__(self):


        fmt = "%(asctime)s %(levelname)-8s %(lineno)4d %(name) 20s.%(funcName)-22s %(threadName)-12s-- %(message)s"
        self.file0 = Path(__file__)
        self.project_path = self.file0.parent
        self.node = platform.node()
        self.node0 = self.node.split(".")[0]

        logfile_path = Path.home() / "Log2Web.log"
        logfile_path.unlink(missing_ok=True)
        self.logfile_name = str(logfile_path)
        super().__init__(logfile=self.logfile_name, format=fmt)

        self.bridge= Log2Web.Bridge(self.run, FlaskApp.app, title="Log2Web Demo",
                                    headertext="Log2Web Demo Threads")
        self.bridge.run()


    def run(self)->None:
        self.logger.info("callback to application")

        executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="POOL_")
        futures = [executor.submit(self.app_thread_target,i ) for i in range(10)]

        # sleep(10)
        executor.shutdown(wait=True)


        self.logger.debug("Bye")
        # """Raises a signal to main thread which is WebGUI to shut down."""
        # signal.raise_signal(2)

    def app_thread_target(self,n:int)->None:

        Log2Web.send_log_op(Log2Web.LogOps.NEW_THREAD)
        self.logger.info(f"app {n} starting")
        for i in range(20):
                match i:
                    case 3:
                        Log2Web.send_log_op(Log2Web.LogOps.BG_COLOR, 'pink')
                        Log2Web.send_log_op(Log2Web.LogOps.FG_COLOR, 'blue')
                    case 5:
                        Log2Web.send_log_op(Log2Web.LogOps.BG_COLOR, 'black')
                        Log2Web.send_log_op(Log2Web.LogOps.FG_COLOR, 'white')
                    case 7:
                        Log2Web.send_log_op(Log2Web.LogOps.BG_COLOR, 'cyan')
                        Log2Web.send_log_op(Log2Web.LogOps.FG_COLOR, 'red')

                if i == n:
                    self.logger.warning(f"app {n=} cycle {i=}")
                else:
                    self.logger.info(f"app {n=} cycle {i=}")

                sleep(1+n/10.)

        Log2Web.send_log_op(Log2Web.LogOps.THREAD_EXIT)

if __name__=="__main__":
    main = Main()
