void activateWidget()
{
  timeval timeout;
  timeout.tv_sec  = 0;
  timeout.tv_usec = 0;

  int nfds = g_client + 1;
  fd_set readfs;
  FD_ZERO(&readfs);
  FD_SET(g_client, &readfs);
  int res = select(nfds, &readfs, NULL, NULL, &timeout);
  if (res <= 0) {
    return;
  }

  if (!FD_ISSET(g_client, &readfs)) {
    return;
  }

  uint64_t widget_id;
  read(g_client, &widget_id, sizeof(widget_id));
  widget_id = ntohll(widget_id);
  void* ptr = reinterpret_cast<void*>(widget_id);
  g_handlers[ptr]();
}

void doUpdateWidgetWindow(QObject* instance, QWidget* window)
{
  uint32_t wid = window->winId();
  sendString(g_server, "setWidgetWindow");
  sendData(g_server, getPid());
  sendData(g_server, reinterpret_cast<uint64_t>(instance));
  sendData(g_server, reinterpret_cast<uint32_t>(wid));
  g_widgetWindow[instance] = window;
}

void updateWidgetWindow(QObject* instance, QWidget* window)
{
    const bool widgetRegistered = g_handlers.find(instance) !=
      g_handlers.end();
    if (!widgetRegistered) {
      return;
    }

    auto parent = g_widgetWindow.find(instance);
    if (parent == g_widgetWindow.end()) {
      doUpdateWidgetWindow(instance, window);
      return;
    }

    if (parent->second != window) {
      doUpdateWidgetWindow(instance, window);
    }
}

void updateWidgetsWindowsRecursive(QObject* instance, QWidget* window)
{
  // Update self
  updateWidgetWindow(instance, window);

  // Update children
  for (auto child : instance->children()) {
    updateWidgetsWindowsRecursive(child, window);
  }
}

void checkEvent(QWidget* instance, QEvent* event)
{
  switch (event->type()) {
    case QEvent::WindowActivate:
      sendString(g_server, "activated");
      sendData(g_server, getPid());
      sendData(g_server, getWindowId());
      return;
  }

  QWidgetList windows;
  for (QWidget* w : QApplication::topLevelWidgets()) {
    if (w->parent() != nullptr) {
      continue;
    }

    if (windows.contains(w)) {
      continue;
    }

    windows.append(w);
  }

  for (QWidget* w : windows) {
    updateWidgetsWindowsRecursive(w, w);
  }

  // Check if need to activate
  activateWidget();
}
