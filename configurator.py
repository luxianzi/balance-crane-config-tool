import json
from tkinter import *
import tkinter.filedialog as fdialog    
import tkinter.simpledialog as sdialog
import tkinter.messagebox as msgbox
from tkinter.ttk import Treeview
from ctypes import *
import os
import paramiko
from paramiko import SSHClient
from scp import SCPClient

class LogWindow(sdialog.Dialog):
    def __init__(self, parent, filename):
        self.log = self.load_log(filename)
        super(LogWindow, self).__init__(parent, title = "日志")
    
    def body(self, master):
        vlayout_expanding = {"fill" : BOTH, "expand" : True, "padx" : 8, "pady" : 8}
        vlayout_no_padding_expanding = {"fill" : BOTH, "expand" : True}

        frame_log = Frame(master)
        scrollbar_log = Scrollbar(frame_log)
        scrollbar_log.pack(side = RIGHT, fill = Y)
        text_log = Text(frame_log, state = NORMAL, yscrollcommand = scrollbar_log.set)
        text_log.insert(INSERT, self.log)
        text_log.config(state = DISABLED)
        scrollbar_log.config(command = text_log.yview)
        text_log.pack(vlayout_no_padding_expanding)
        self.text_log = text_log
        frame_log.pack(vlayout_expanding)

    def get_strerror(self, error):
        if len(error.args) > 1:
            return error.args[1]
        else:
            return error.args[0]

    def load_log(self, filename = ""):
        try:
            with open(filename, "r") as file:
                return file.read()
        except Exception as error:
            msgbox.showerror("错误", self.get_strerror(error))

class MainWindow():
    def __init__(self):
        self.config = self.get_config("config.json")
        self.build_ui(self.config)
        
    def get_config(self, filename = ""):
        config = {}
        with open(filename, encoding = "utf-8") as json_file:
            config = json.load(json_file)
        return config

    def get_param(self, filename = ""):
        filesize = os.path.getsize(filename)
        try:
            with open(filename, "rb") as file:
                for param in self.config["params"]:
                    if file.seek(param["offset"]) >= filesize:
                        data = 0
                    elif param["type"] == "unsigned char" or param["type"] == "char":
                        data = ord(c_char.from_buffer(bytearray(file.read(1))).value)
                    elif param["type"] == "unsigned short" or param["type"] == "short":
                        data = c_short.from_buffer(bytearray(file.read(2))).value
                    elif param["type"] == "unsigned int" or param["type"] == "int":
                        data = c_int.from_buffer(bytearray(file.read(4))).value
                    elif param["type"] == "unsigned long" or param["type"] == "long":
                        data = c_long.from_buffer(bytearray(file.read(4))).value
                    elif param["type"] == "unsigned long long" or param["type"] == "long long":
                        data = c_longlong.from_buffer(bytearray(file.read(8))).value
                    elif param["type"] == "double":
                        data = c_double.from_buffer(bytearray(file.read(8))).value
                    else:
                        print("Unknown data type: " + param["type"])
                    self.treeview_configuration.set(param["name"], "#4", data)
        except EnvironmentError as error:
            msgbox.showerror("错误", "解析文件错误: " + self.get_strerror(error))
            return False
        return True

    def save_param(self, filename = ""):
        try:
            with open(filename, "wb") as file:
                for param in self.config["params"]:
                    file.seek(param["offset"])
                    value = self.treeview_configuration.item(param["name"], "values")[3]
                    if type(value) is str:
                        value = eval(value)
                    if param["type"] == "unsigned char" or param["type"] == "char":
                        data = bytes(c_char(value))
                    elif param["type"] == "unsigned short" or param["type"] == "short":
                        data = bytes(c_short(value))
                    elif param["type"] == "unsigned int" or param["type"] == "int":
                        data = bytes(c_int(value))
                    elif param["type"] == "unsigned long" or param["type"] == "long":
                        data = bytes(c_long(value))
                    elif param["type"] == "unsigned long long" or param["type"] == "long long":
                        data = bytes(c_longlong(value))
                    elif param["type"] == "double":
                        data = bytes(c_double(value))
                    else:
                        print("Unknown data type: " + param["type"])
                    file.write(data)
        except EnvironmentError as error:
            msgbox.showerror("错误", "保存文件错误: " + self.get_strerror(error))
            return False
        return True

    def get_strerror(self, error):
        if len(error.args) > 1:
            return error.args[1]
        else:
            return error.args[0]

    def update_button_state(self, state = ""):
        if state == "connecting":
            self.button_connect["state"] = DISABLED
            self.button_disconnect["state"] = NORMAL
        elif state == "connected":
            self.button_download["state"] = NORMAL
            self.button_upload["state"] = NORMAL
            self.button_view["state"] = NORMAL
        elif state == "disconnected":
            self.button_connect["state"] = NORMAL
            self.button_disconnect["state"] = DISABLED
            self.button_download["state"] = DISABLED
            self.button_upload["state"] = DISABLED
            self.button_view["state"] = DISABLED
    
    def button_connect_clicked(self):
        self.state = "connecting"
        self.update_button_state(self.state)
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.entry_host.get(), username = self.entry_user.get(), password = self.entry_password.get())
        except Exception as error:
            self.state = "disconnected"
            self.update_button_state(self.state)
            msgbox.showerror("错误", "连接错误: " + self.get_strerror(error))
            return
        self.state = "connected"
        self.update_button_state(self.state)
        self.ssh = ssh

    def button_disconnect_clicked(self):
        self.ssh.close()
        self.state = "disconnected"
        self.update_button_state(self.state)
    
    def button_open_clicked(self):
        filename = fdialog.askopenfilename(filetypes = [("所有文件", "*.*"), ("参数文件", "*.txt")])
        if filename:
            self.get_param(filename)
        
    def button_save_clicked(self):
        filename = fdialog.asksaveasfilename(filetypes = [("所有文件", "*.*"), ("参数文件", "*.txt")])
        if filename:
            self.save_param(filename)

    def treeview_configuration_double_clicked(self, event):
        for item in self.treeview_configuration.selection():
            value = self.treeview_configuration.item(item, "values")[3]
        row = self.treeview_configuration.identify_row(event.y)
        input_value = "NULL"
        for param in self.config["params"]:
            if param["name"] == row and param["editable"]:
                if  param["type"] == "unsigned char" or param["type"] == "char" or \
                    param["type"] == "unsigned short" or param["type"] == "short" or \
                    param["type"] == "unsigned int" or param["type"] == "int" or \
                    param["type"] == "unsigned long" or param["type"] == "long" or \
                    param["type"] == "unsigned long long" or param["type"] == "long long":
                    input_value = sdialog.askinteger("输入", "请输入整数值", initialvalue = value)
                elif param["type"] == "double":
                    input_value = sdialog.askfloat("输入", "请输入浮点数值", initialvalue = value)
        if input_value != "NULL":
            self.treeview_configuration.set(row, "#4", input_value)

    def button_download_clicked(self):
        remote_file = self.entry_param_path.get()
        local_path = os.path.dirname(os.path.abspath(__file__))
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.get(remote_file, local_path = local_path)
        except Exception as error:
            msgbox.showerror("错误", self.get_strerror(error))
            return
        self.get_param(os.path.join(local_path, os.path.basename(remote_file)))

    def button_upload_clicked(self):
        if msgbox.askokcancel("问题", "上传后原有参数将被覆盖，请确认。"):
            remote_file = self.entry_param_path.get()
            remote_path = os.path.dirname(remote_file)
            local_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(remote_file))
            if self.save_param(local_file):
                try:
                    with SCPClient(self.ssh.get_transport()) as scp:
                        scp.put(local_file, remote_path = remote_path)
                except Exception as error:
                    msgbox.showerror("错误", self.get_strerror(error))
                    return

    def button_view_clicked(self):
        remote_file = self.entry_log_path.get()
        local_path = os.path.dirname(os.path.abspath(__file__))
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.get(remote_file, local_path = local_path)
        except Exception as error:
            msgbox.showerror("错误", self.get_strerror(error))
            return
        filename = os.path.join(local_path, os.path.basename(remote_file))
        LogWindow(self.main_window, filename = filename)

    def build_ui(self, config = {}):
        hlayout = {"side": LEFT, "padx" : 8, "pady" : 8}
        vlayout = {"fill": X, "padx" : 8, "pady" : 8}
        vlayout_no_padding = {"fill": X}
        vlayout_expanding = {"fill" : BOTH, "expand" : True, "padx" : 8, "pady" : 8}
        vlayout_no_padding_expanding = {"fill" : BOTH, "expand" : True}
        
        main_window = Tk();
        main_window.title("配置工具")
        frame_connection = LabelFrame(main_window, text = "连接设置")
        Label(frame_connection, text = "主机:").pack(hlayout)
        entry_host = Entry(frame_connection)
        entry_host.insert(0, config["remote"]["host"])
        entry_host.pack(hlayout)
        self.entry_host = entry_host
        Label(frame_connection, text = "用户名:").pack(hlayout)
        entry_user = Entry(frame_connection, width = 10)
        entry_user.insert(0, config["remote"]["username"])
        entry_user.pack(hlayout)
        self.entry_user = entry_user
        Label(frame_connection, text = "密码:").pack(hlayout)
        entry_password = Entry(frame_connection, show = "*", width = 10)
        entry_password.insert(0, config["remote"]["password"])
        entry_password.pack(hlayout)
        self.entry_password = entry_password
        button_connect = Button(frame_connection, text = "连接", command = self.button_connect_clicked)
        button_connect.pack(hlayout)
        self.button_connect = button_connect
        button_disconnect = Button(frame_connection, text = "断开", state = DISABLED, command = self.button_disconnect_clicked)
        button_disconnect.pack(hlayout)
        self.button_disconnect = button_disconnect
        frame_connection.pack(vlayout)
        
        frame_configuration = LabelFrame(main_window, text = "配置")
        frame_configuration_control = Frame(frame_configuration)
        Label(frame_configuration_control, text = "远程路径:").pack(hlayout)
        entry_params_path = Entry(frame_configuration_control, width = 30)
        entry_params_path.insert(0, config["remote"]["params_path"])
        entry_params_path.pack(hlayout)
        self.entry_param_path = entry_params_path
        button_open = Button(frame_configuration_control, text = "打开", command = self.button_open_clicked)
        button_open.pack(hlayout)
        self.button_open = button_open
        button_save = Button(frame_configuration_control, text = "保存", command = self.button_save_clicked)
        button_save.pack(hlayout)
        self.button_save = button_save
        button_download = Button(frame_configuration_control, text = "下载", state = DISABLED, command = self.button_download_clicked)
        button_download.pack(hlayout)
        self.button_download = button_download
        button_upload = Button(frame_configuration_control, text= "上传", state = DISABLED, command = self.button_upload_clicked)
        button_upload.pack(hlayout)
        self.button_upload = button_upload
        frame_configuration_control.pack(vlayout_no_padding)
        frame_configuration_data = Frame(frame_configuration)
        scrollbar_configuration = Scrollbar(frame_configuration_data)
        scrollbar_configuration.pack(side = RIGHT, fill = Y)
        treeview_configuration = Treeview(frame_configuration_data, columns = ("index", "name", "description", "value"), show = "headings", yscrollcommand = scrollbar_configuration.set)
        treeview_configuration.heading("index", text = "序号")
        treeview_configuration.column("index", width = 50)
        treeview_configuration.heading("name", text = "参数名")
        treeview_configuration.heading("description", text = "描述")
        treeview_configuration.heading("value", text = "值")
        index = 0
        for param in config["params"]:
            data = (index, param["name"], param["description"], 0)
            index += 1
            treeview_configuration.insert("", "end", param["name"], values = data)
        treeview_configuration.pack(vlayout_no_padding_expanding)
        treeview_configuration.bind("<Double-1>", self.treeview_configuration_double_clicked)
        self.treeview_configuration = treeview_configuration
        scrollbar_configuration.config(command = treeview_configuration.yview)
        frame_configuration_data.pack(vlayout_expanding)
        frame_configuration.pack(vlayout_expanding)
        frame_log = LabelFrame(main_window, text = "日志")
        Label(frame_log, text = "远程路径:").pack(hlayout)
        entry_log_path = Entry(frame_log, width = 30)
        entry_log_path.insert(0, config["remote"]["log_path"])
        entry_log_path.pack(hlayout)
        self.entry_log_path = entry_log_path
        button_view = Button(frame_log, text = "查看", state = DISABLED, command = self.button_view_clicked)
        button_view.pack(hlayout)
        self.button_view = button_view
        frame_log.pack(vlayout)
        
        self.state = ""
        self.main_window = main_window
        main_window.mainloop()

def main():
    main_window = MainWindow() 
    
if __name__ == "__main__":
    main()