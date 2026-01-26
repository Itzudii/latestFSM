import threading
import time
from queue import Queue
import os
import tkinter as tk

from FSTags import TagGenerator
from FSmain import FSManager
from FSCLI import CLI

from FSvector import MrVectorExpert
from FSlog_config import setup_logger

from FSgui import FSProjectGUI


if __name__ == "__main__":

    logger = setup_logger()
    logger.info("FS System started")


    logger.info("MRVector init...")
    vec = MrVectorExpert()

  
    vec.load_model()
    logger.info("vectormaster.pkl loading")
    vec.load()
    logger.info("MRVector full loaded correctly")


    logger.info("TagGenerator init")
    tag = TagGenerator()
    
    logger.info("FSManager init..")
    fs = FSManager(tag,vec)
    fs.load()


    logger.info("CLI init..")
    cli = CLI(fs)

    guiroot = tk.Tk()
    app = FSProjectGUI(guiroot,fs)

    logger.info("both thread init..")
    # t1 = threading.Thread(target=cli.input_listener, daemon=True)
    t2 = threading.Thread(target=cli.background_worker, daemon=True)
    

    logger.info("both thread started")
    # t1.start()
    t2.start()
   
    # logger.info("both thread join")
    # t1.join()
    # t2.join()

    guiroot.mainloop()

    