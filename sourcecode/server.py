class Server(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.__applications = []
        self.__running = True
        self.__last_window_id = None

        if os.path.exists(SOCKET_FILE_PATH):
            os.remove(SOCKET_FILE_PATH)

        server = Socket(AF_UNIX, SOCK_DGRAM)
        server.bind(SOCKET_FILE_PATH)
        self.__socket = server

        self.__thread = QThread(self)
        self.moveToThread(self.__thread)
        self.__thread.started.connect(self.__loop)

    def start(self):
        """Start main server cycle."""
        self.__thread.start()

    def stop(self):
        """Stop main server cycle."""
        self.__running = False

    def __get_app(self, pid):
        return _find_one(self.__applications, lambda app: app.pid == pid)

    def __find_window_by_wid(self, wid):
        all_windows = []
        for app in self.__applications:
            all_windows += app.windows

        return _find_one(all_windows, lambda win: win.wid == wid)

    def get_options(self):
        """Activate widget with `widget_name` in last activated window."""
        last_window = self.__find_window_by_wid(self.__last_window_id)
        if last_window is None:
            return []
        return [widget.text for widget in last_window.widgets]

    def activate(self, widget_name):
        """Activate widget with `widget_name` in last activated window."""
        last_window = self.__find_window_by_wid(self.__last_window_id)
        widget = _find_one(last_window.widgets,
                lambda widget: widget.text == widget_name)

        print('Widget "{widget_name}" with addr {addr} activated'.format(
            widget_name=widget.text, addr=hex(widget.addr)))

        self.__activate_widget(widget)
        _activate_window(last_window)

    def __activate_widget(self, widget):
        app = _find_one(self.__applications, lambda app:
                        _find_one(app.windows, lambda win:
                                  widget in win.widgets))
        _activate_widget(app.client, widget)

    def __add_new_app(self, pid, socket_path):
        client_socket = Socket(AF_UNIX, SOCK_DGRAM)
        client_socket.connect(socket_path)
        app = App(pid, client_socket)
        self.__applications.append(app)

    def __set_widget_text(self, pid, addr, text):
        app = self.__get_app(pid)
        text = text.replace('&', '')
        app.set_widget_text(addr, text)
        print(f'Widget "{text}" with addr {hex(addr)} added')

    def __set_widget_window(self, pid, addr, wid):
        app = self.__get_app(pid)
        app.set_widget_window(addr, wid)

    def __remove(self, pid, addr):
        app = self.__get_app(pid)
        for window in app.windows:
            window.widgets = [w for w in window.widgets if w.addr != addr]
        print('Widget with addr {} removed'.format(addr))

    def __activated(self, pid, wid):
        self.__last_window_id = wid

    def __handle_cmd(self, server, command):
        print(f'[DEBUG] Handle cmd: {command}')
        if command == 'newApp':
            pid = _recv_uint64(server)
            socket_path = _recv_text(server)
            self.__add_new_app(pid, socket_path)
        elif command == 'setWidgetText':
            pid = _recv_uint64(server)
            addr = _recv_uint64(server)
            text = _recv_text(server)
            self.__set_widget_text(pid, addr, text)
        elif command == 'remove':
            pid = _recv_uint64(server)
            addr = _recv_uint64(server)
            self.__remove(pid, addr)
        elif command == 'activated':
            pid = _recv_uint64(server)
            wid = _recv_uint32(server)
            self.__activated(pid, wid)
        elif command == 'setWidgetWindow':
            pid = _recv_uint64(server)
            addr = _recv_uint64(server)
            wid = _recv_uint32(server)
            self.__set_widget_window(pid, addr, wid)
        else:
            print(f'Unknown command: {command}')

    def __loop(self):
        while self.__running:
            print('[DEBUG] Loop iteration')
            # TODO: Add timeout
            rlist = select.select([self.__socket], [], [])[0]
            # HACK: Handle only first socket
            socket = rlist[0]
            if socket in rlist:
                command = _recv_command(socket)
                self.__handle_cmd(socket, command)

        self.__socket.close()
        os.remove(SOCKET_FILE_PATH)
