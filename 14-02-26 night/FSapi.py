from FScontroller import Controller
import webview
# import json
# from FS.useful import get_indicator,formate_sttime,get_filemode,filemode_readable
# from FS.icon import known_file_types
# import pyperclip

def create_task(name, *args):
    return {
        "for": "TaskPerformer",
        "name": name,
        "args": args
    }


class API:
    def __init__(self, controller: Controller):
        self._ctrl = controller
        self._window = webview.create_window(
                title="FS Manager",
                url="frontend/main-window.html",
                width=1200,
                height=700,
                resizable=True,
                fullscreen=False,
                js_api=self
        )

        self._window.events.closed += self._ctrl.on_close

    

    def show_list(self):
        task = create_task("show_list")
        return self._ctrl.start_task(task)

    def open(self,*args):
        task = create_task("open",*args)
        return self._ctrl.start_task(task)


    def backward(self):
        task = create_task("backward")
        return self._ctrl.start_task(task)
       

    def forward(self):
        task = create_task("forward")
        return self._ctrl.start_task(task)
       
       

    def go_root(self):
        task = create_task("go_root")
        return self._ctrl.start_task(task)
       

    def go_to_address(self,*args):
        task = create_task("go_to_address",*args)
        return self._ctrl.start_task(task)
    

    def navigate_to(self,path):
        path = f'{'/'.join(path.split('/')[:-1])}"'
        self.window1.evaluate_js(f'navigateToBreadcrumb(null,{(path)})')   
       

    def rename(self,old,new):
        task = create_task("rename",*(old,new))
        return self._ctrl.start_task(task)
        

    def cut(self,data):
        task = create_task("cut",data)
        return self._ctrl.start_task(task)
       

    def copy(self,data):
        task = create_task("copy",data)
        return self._ctrl.start_task(task)
       
        
    def paste(self):
        task = create_task("paste")
        return self._ctrl.start_task(task)

    def delete(self,data):
        task = create_task("delete",data)
        return self._ctrl.start_task(task)
       

    def create_folder(self,name):
        task = create_task("create_folder",name)
        return self._ctrl.start_task(task)

    def create_file(self,filename,content=""):
        task = create_task("create_file",*(filename,content))
        return self._ctrl.start_task(task)

    def path_breaker(self):
        task = create_task("path_breaker")
        return self._ctrl.start_task(task)
    
    def get_cwd(self):
        task = create_task("get_cwd")
        return self._ctrl.start_task(task)

    def get_quick(self):
        task = create_task("get_quick")
        return self._ctrl.start_task(task)

    def pin_to_quick(self,path):
        task = create_task("pin_to_quick",path)
        return self._ctrl.start_task(task)
       
    
    def unpin_to_quick(self,path):
        task = create_task("unpin_to_quick",path)
        return self._ctrl.start_task(task)
         

    
    def open_search(self):
        task = create_task("open_search")
        return self._ctrl.start_task(task)
       

    def ultra_search(self,search_for,search_where,prifix,extension,substring):
        task = create_task("ultra_search",search_for,search_where,prifix,extension,substring)
        return self._ctrl.start_task(task)

    # hash
    def get_duplicates(self):
        task = create_task("get_duplicates")
        return self._ctrl.start_task(task)

    
    def find_dup(self,path):
        task = create_task("find_dup",path)
        return self._ctrl.start_task(task)

    def copy_text(self,text):
        task = create_task("copy_text",text)
        return self._ctrl.start_task(task)
       

    def tag_search(self,tags):
        task = create_task("tag_search",tags)
        return self._ctrl.start_task(task)
       

    def lock_files(self,paths):
        task = create_task("lock_files",paths)
        return self._ctrl.start_task(task)
               

    def unlock_files(self,paths):
        task = create_task("unlock_files",paths)
        return self._ctrl.start_task(task)
       

     

if __name__ == '__main__':
    api = API(Controller())
    webview.start(debug=True)
 