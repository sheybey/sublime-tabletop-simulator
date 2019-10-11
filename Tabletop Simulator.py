import sublime
import sublime_plugin
import socket
import socketserver
import threading
import json

views = {}


def open_script(script, window):
    view = views.get(script['guid'], None)
    if view is not None:
        view.run_command('erase_buffer')
    else:
        view = window.new_file()
        views[script['guid']] = view
        view.set_syntax_file('Packages/Lua/Lua.sublime-syntax')
    if script['guid'] != '-1':
        view.set_name(script['name'] + ' - ' + script['guid'])
    else:
        view.set_name(script['name'])
    view.run_command('append_to_buffer', {'text': script['script']})
    view.window().focus_view(view)


def show_message_panel(window, message):
    panel = window.create_output_panel('tts_messages')
    panel.run_command('append_to_buffer', {'text': message})
    window.run_command('show_panel', {'panel': 'output.tts_messages'})


class EditorAPIHandler(socketserver.StreamRequestHandler):
    def handle(self):
        data = json.load(self.rfile)
        window = sublime.active_window()
        if data['messageID'] < 2:
            for script in data['scriptStates']:
                open_script(script, window)
        elif data['messageID'] == 2:
            show_message_panel(window, data['message'])

        elif data['messageID'] == 3:
            view = views.get(data['guid'], None)
            if view is None:
                view = window.active_view()
            else:
                window = view.window()
            window.focus_view(view)
            show_message_panel(
                window,
                data['errorMessagePrefix'] + data['error'] + '\n'
            )
        else:
            show_message_panel(
                window,
                'unhandled message:\n' + repr(data) + '\n'
            )


server = socketserver.TCPServer(('localhost', 39998), EditorAPIHandler, False)


def start_server():
    server.server_bind()
    server.server_activate()
    server.serve_forever()


def plugin_loaded():
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()


def plugin_unloaded():
    server.shutdown()
    server.server_close()


class EraseBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.size() != 0:
            self.view.erase(edit, sublime.Region(0, self.view.size()))


class AppendToBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=''):
        self.view.insert(edit, self.view.size(), text)


def send_data(data):
    view = sublime.active_window().active_view()
    view.erase_status('z_tts_error')
    response = bytes()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(('localhost', 39999))
            json.dump(data, client.makefile('w', encoding='ascii'))
            response = client.makefile('r', encoding='ascii').read()
        if not response:
            return None
        return json.loads(response)
    except ConnectionRefusedError:
        view.set_status(
            'z_tts_error',
            'Unable to connect to Tabletop Simulator: Connection refused'
        )
        return None


class GetScriptsCommand(sublime_plugin.WindowCommand):
    def run(self):
        scripts = send_data({'messageID': 0})
        if scripts is not None:
            for script in scripts['scriptStates']:
                open_script(script, self.window)


class SendScriptsCommand(sublime_plugin.WindowCommand):
    def run(self):
        send_data({'messageID': 1, 'scriptStates': [
            {
                'guid': guid,
                'script': view.substr(sublime.Region(0, view.size()))
            }
            for guid, view in views.items()
        ]})

    def is_enabled(self):
        return len(views) > 0


class CleanUpViews(sublime_plugin.EventListener):
    def on_close(self, view):
        for guid in views.keys():
            if view == views[guid]:
                del views[guid]
                break
