# from FScontroller import Controller
import webview
import json
from FS.useful import get_indicator,formate_sttime,get_filemode,filemode_readable
from FS.icon import known_file_types
import pyperclip


class TaskPerformer:
    def __init__(self, fs):
        self.fs = fs


    def show_list(self):   
        data= self.fs.show_list()
        result = []
        for node in data:
            # print(node.name,node.indicator)
            result.append({
                "path":node.path,
                "name":node.name,
                "mdate":formate_sttime(node.modified_time),
                "cdate":formate_sttime(node.created_time),
                "mode":filemode_readable(get_filemode(node.mode)),
                "tags":node.tags,
                "type":node.type,
                "size":node.size,
                "indicator":get_indicator(node.indicator),
                "filetype":known_file_types.get(f'.{node.details['ext']}',"unknown"),
                "islock":node.islocked,
                "ishidden":node.details['ishidden'],
                "icon":'<svg xmlns="http://www.w3.org/2000/svg" height="30px" viewBox="0 -960 960 960" width="30px" fill="#fff"><path d="m484-288 89-68 89 68-34-109.15L717-468H607.56L573-576l-34 108H429l89 70.85L484-288Zm-316 96q-29 0-50.5-21.5T96-264v-432q0-29.7 21.5-50.85Q139-768 168-768h216l96 96h312q29.7 0 50.85 21.15Q864-629.7 864-600v336q0 29-21.15 50.5T792-192H168Zm0-72h624v-336H450l-96-96H168v432Zm0 0v-432 432Z"/></svg>' if node.type == 'd' else '<svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="#e3e3e3"><path d="M263.72-96Q234-96 213-117.15T192-168v-624q0-29.7 21.15-50.85Q234.3-864 264-864h312l192 192v504q0 29.7-21.16 50.85Q725.68-96 695.96-96H263.72Zm.28-72h432v-456H528v-168H264v624Zm203.54-24q65.52 0 110.99-45.5T624-348v-132h-72v132q0 34.65-24.5 59.33Q503-264 467.51-264q-34.45 0-58.98-24.67Q384-313.35 384-348v-180q0-10 7.2-17t16.8-7q10 0 17 7t7 17v192h72v-192q0-40.32-27.77-68.16-27.78-27.84-68-27.84Q368-624 340-596.16q-28 27.84-28 68.16v180q0 65 45.5 110.5T467.54-192ZM264-792v189-189 624-624Z"/></svg>'
            })
        return result

    def open(self,name):
        self.fs.go_to(name)


    def backward(self):
        self.fs.go_back()
       

    def forward(self):
        self.fs.go_forward()
       

    def go_root(self):
        self.fs.go_to_root()
       

    def go_to_address(self,path):
        isDone,msg = self.fs.go_to_address(path)
        return {
            "isdone":isDone,
            "msg":msg
        }
       

    def rename(self,old,new):
        
        result = self.fs.rename(old,new)
       
        return result
        

    def cut(self,data):
        
        self.fs.unselect_all()
        for filename in data:
            self.fs.select_name(filename)
        self.fs.cut()
       

    def copy(self,data):
        
        self.fs.unselect_all()
        for filename in data:
            self.fs.select_name(filename)
        self.fs.copy()
       
        
    def paste(self):
        
        result = self.fs.paste()
       
        return result

    def delete(self,data):
        
        self.fs.unselect_all()
        for filename in data:
            self.fs.delete(filename)
       

    def create_folder(self,name):
        
        dict_ = self.fs.create_dir(name)
       
        return dict_['name']

    def create_file(self,filename,content=""):
        
        dict_ = self.fs.create_file(filename,content)
       
        return dict_['name']

    def path_breaker(self):
        
        result = self.fs.path_break_cwd()
        return result
    
    def get_cwd(self):
        
        path = self.fs.cwd.path
       
        return path

    def get_quick(self):
        
        result = [(key,path)for key,lst in self.fs.quick_access.data.items()for path in lst] 
       
        return result
        

    def pin_to_quick(self,path):
        
        lst = self.fs.path_breaker(path)
        if lst:
            self.fs.quick_access.add(lst[0],path)
       
    
    def unpin_to_quick(self,path):
        
        lst = self.fs.path_breaker(path)
        if lst:
            self.fs.quick_access.remove(lst[0],path)
       

    # def new_window(self):
        
    #     w1 = webview.create_window(
    #         title="FS Manager",
    #         url="frontend/main-window.html",
    #         width=1200,
    #         height=700,
    #         resizable=True,
    #         fullscreen=False,
    #         js_api=self
    #     )
       

    
    def open_search(self):
        
        w2 = webview.create_window(
            title="FS Manager",
            url="frontend/file-search.html",
            width=550,
            height=755,
            resizable=False,
            fullscreen=False,
            js_api=self
        )
       

    def ultra_search(self,search_for,search_where,prifix,extension,substring):
        
        result = self.fs.ultra_search(search_for,search_where,prifix,extension[1:] if extension.startswith('.') else extension ,substring)
       
        return result

    # hash
    def get_duplicates(self):
        
        data = self.fs.search_duplicate_files()
        results=[]
        for hash_,paths in data.items():
            results.append([[path.split('/')[-1],path] for path in paths])

       
        return results
    
    def find_dup(self,path):
        
        hash_= self.fs.search_hash_by_path(path)
        paths= self.fs.search_paths_by_hash(hash_)
        
       
        return {
            "paths":list(paths)
        }

    def copy_text(self,text):
        
        pyperclip.copy(text)
       

    def tag_search(self,tags):
        
        print(tags)
        paths = self.fs.mrvec.search_by_query(tags)
        results=[{"name":path.split('/')[-1],"path":path} for path in paths]
       
        return results

    def lock_files(self,paths):
        
        for path in paths:
            data = self.fs.get_node_by_path(path)
            node =  data.get("result",None)
            if node:
                self.fs.lock_file(node)
               

    def unlock_files(self,paths):
        
        for path in paths:
            data = self.fs.get_node_by_path(path)
            node =  data.get("result",None)
            if node:
                self.fs.unlock_file(node)
       

     
