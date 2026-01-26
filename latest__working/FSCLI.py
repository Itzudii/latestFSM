import threading
import time
from queue import Queue
import os
import logging
logger = logging.getLogger("FS")
class CLI:
    def __init__(self,fs) -> None:
        self.fs = fs
        self.isRunning = True
        self.last_input = None

        self.task_queue = Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

    def clear(self):
        os.system('cls')

    

    def process_user_task(self,command):# all work put robustness//////////////////////////



        if command == 'quit':
            self.isRunning = False
        elif command.startswith('cd '):
            _,name = command.split(' ',1)
            self.fs.go_to(name)
        elif command == 'back':
            self.fs.go_back()
        elif command == 'root':
            self.fs.go_to_root()
        elif command == 'refresh':
            self.fs.refresh_cwd()
        elif command == 'refreshall':
            self.fs.refresh_root()
        elif command == 'selectall':
            self.fs.select_all()
        elif command.startswith('select'):
            _,name = command.split(' ',1)
            node = self.fs.get_node(name)
            if node:
                self.fs.select(node)
            else:
                print(f"{name} not found in current directory")
        elif command == "unselectall":
            self.fs.unselect_all()
        elif command.startswith('unselect'):
            _,name = command.split(' ',1)
            node = self.fs.get_node(name)
            if node:
                self.fs.unselect(node)
            else:
                print(f"{name} not found in current directory")
        elif command.startswith('open'):
            _,name = command.split(' ',1)
            node = self.fs.get_node(name)
            if node:
                self.fs.open(node)
            else:
                print(f"{name} not found in current directory")
        elif command == 'cut':
            self.fs.cut()
        elif command == 'copy':
            self.fs.copy()
        elif command == 'paste':
            self.fs.paste()
        elif command.startswith('del'):
            _,name = command.split(' ',1)
            node = self.fs.get_node(name)
            if node:
                self.fs.delete(node)
            else:
                print(f"{name} not found in current directory")
        elif command.startswith('mkdir'):
            _,name = command.split(' ',1)
            self.fs.create_dir(name)
        elif command.startswith('mkf'):
            _,name,content = command.split(' ',2)
            self.fs.create_file(name,content) 
        elif command.startswith('rename'):
            _,old_name,new_name = command.split(' ',2)
            node = self.fs.get_node(old_name)
            if node:
                self.fs.rename(new_name,node)
            else:
                print(f"{old_name} not found in current directory")
        elif command.startswith('write'):
            _,name,content = command.split(' ',2)
            node = self.fs.get_node(name)
            if node:
                self.fs.write_to_file(node,content)
            else:
                print(f"{name} not found in current directory")
        elif command.startswith('append'):
            _,name,content = command.split(' ',2)
            node = self.fs.get_node(name)
            if node:
                self.fs.append_to_file(node,content)
            else:
                print(f"{name} not found in current directory")
        elif command.startswith('search'):
            _,typ,mood,content = command.split(' ',3)
            res = []
            if typ == '-p':
                if mood == '-n':
                    res = self.fs.search_prifix(content)
                elif mood == '-a':
                    res = self.fs.search_prifix_all(content)
                else:
                    print("mood is invalid")
            elif typ == '-e':
                if mood == '-n':
                    res = self.fs.search_ext(content)
                elif mood == '-a':
                    res = self.fs.search_ext_all(content)
                else:
                    print("mood is invalid")
            else:
                    print("type is invalid")

        
    
    def  display(self):
        print("=== File Management System ===")
        print("_"*100)
        print(f'|Current Directory: {self.fs.cwd.path:79}|')
        print("_"*100)

        lst = self.fs.show_list()
        for item in lst:
            print(f'{item["name"]:40}{item["type"]:10}{item["size"]:<10}{item['path']}')

        print("_"*100)
        for item in self.fs.selected_nodes:
            print(f'|:       {item.name:90}|')
        print("_"*100)

                
    """
    tread funtions \/
    """
    def input_listener(self):
        """
        Waits for user input and stores it in variable + queue
        """
        while not self.stop_event.is_set():
            self.display()
            user_input = input("FS> ")
            self.clear()
            logger.info(f"[INPUT CAPTURED] -> {user_input}")

            # store user input in variable
            self.last_input = user_input

            # push into task queue
            # self.task_queue.put(user_input)
            self.pause_event.set()
            self.process_user_task(user_input)
            self.pause_event.clear()

            if not self.isRunning:
                self.stop_event.set()
                self.task_queue.put(None)
                break

                
    def background_worker(self):
        refresh_gen = self.fs._refresh(self.fs.root)
    
        while not self.stop_event.is_set():
            
            if self.pause_event.is_set():
                time.sleep(0.01)
                continue
            
            # 1 refresh step
            try:
                next(refresh_gen)
            except StopIteration:
                pass
            
            # 1 index step
            self.fs.background_index_step()
    
            # 1 vector DB maintenance step
            self.fs.mrvec.background_task_step()
    
            time.sleep(0.003)
            # time.sleep(0.1)
