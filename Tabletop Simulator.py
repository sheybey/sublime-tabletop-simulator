import sublime
import sublime_plugin
import socket
import socketserver
import threading
import json

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer): pass

class Global:
    server = None
    views = {}

def open_script(script, window):
    view = Global.views.get(script["guid"], None)
    if view is not None:
        view.run_command("erase_buffer")
    else:
        view = window.new_file()
        Global.views[script["guid"]] = view
        view.set_syntax_file("Packages/Lua/Lua.sublime-syntax")
    if script["guid"] != "-1":
        view.set_name(script["name"] + " - " + script["guid"])
    else:
        view.set_name(script["name"])
    view.run_command("append_to_buffer", {"text": script["script"]})
    view.window().focus_view(view)

class EditorAPIHandler(socketserver.StreamRequestHandler):
    def handle(self):
        data = json.loads(self.rfile.read().decode("ascii"))
        window = sublime.active_window()
        if data["messageID"] < 2:
            for script in data["scriptStates"]:
                open_script(script, window)
        elif data["messageID"] == 2:
            window.create_output_panel("tts_messages").run_command("append_to_buffer", {
                "text": data["message"] + "\n"
            })
            window.run_command("show_panel", {"panel": "output.tts_messages"})

        elif data["messageID"] == 3:
            view = Global.views.get(data["guid"], None)
            if view is None:
                view = window.active_view()
            else:
                window = view.window()
            window.focus_view(view)
            window.create_output_panel("tts_messages").run_command("append_to_buffer", {
                "text": data["errorMessagePrefix"] + data["error"] + "\n"
            })
            window.run_command("show_panel", {"panel": "output.tts_messages"})

def start_server():
    if Global.server is not None: return
    server = ThreadedTCPServer(("localhost", 39998), EditorAPIHandler)
    Global.server = server
    threading.Thread(target=server.serve_forever).start()

def stop_server():
    if Global.server is None: return
    Global.server.shutdown()
    Global.server.server_close()
    Global.server = None

#def plugin_loaded(): start_server()
def plugin_unloaded(): stop_server()

class EraseBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.size() != 0: self.view.erase(edit, sublime.Region(0, self.view.size()))

class AppendToBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit, text = ""):
        self.view.insert(edit, self.view.size(), text)

def send_data(data):
    view = sublime.active_window().active_view()
    view.erase_status("z_tts_error")
    response = bytes()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(("localhost", 39999))
            client.send(json.dumps(data).encode("ascii"))
            while True:
                r = client.recv(2048)
                if not r: break
                response += r
        if not response:
            return None
        return json.loads(response.decode("ascii"))
    except ConnectionRefusedError:
        print("unable to connect to Tabletop Simulator: Connection refused")
        view.set_status("z_tts_error", "Unable to connect to Tabletop Simulator: Connection refused")
        return None

class GetScriptsCommand(sublime_plugin.WindowCommand):
    def run(self):
        scripts = send_data({"messageID": 0})
        if scripts is not None:
            for script in scripts["scriptStates"]: open_script(script, self.window)

class SendScriptsCommand(sublime_plugin.WindowCommand):
    def run(self):
        scripts = []
        for guid in Global.views.keys():
            scripts.append({
                "guid": guid,
                "script": Global.views[guid].substr(
                    sublime.Region(0, Global.views[guid].size())
                )
            })
        send_data({"messageID": 1, "scriptStates": scripts})
    def is_enabled(self): return len(Global.views) > 0

class StartServerCommand(sublime_plugin.ApplicationCommand):
    def run(self): start_server()
    def is_enabled(self): return Global.server is None

class StopServerCommand(sublime_plugin.ApplicationCommand):
    def run(self): stop_server()
    def is_enabled(self): return Global.server is not None

class CleanUpViews(sublime_plugin.EventListener):
    def on_close(self, view):
        for guid in Global.views.keys():
            if view == Global.views[guid]:
                del Global.views[guid]
                return
