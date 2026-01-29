import tkinter as tk
from importlib.resources import files


# TODO: implementation is specific windows
# The fallback is acceptable. The dialog popup to open/save file may not appear on the right monitor.
# Could try to support other platforms but the best option may be to do a pull request to screeninfo library to support get_active_monitor.
def getActiveMonitorTkinterGeometry() -> str:
  defaultGeometry = '0x0-50000-50000'
  try:
    import ctypes
    import ctypes.wintypes

    import screeninfo
  except:
    return defaultGeometry

  CCHDEVICENAME = 32
  class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
      ("cbSize", ctypes.wintypes.DWORD),
      ("rcMonitor", ctypes.wintypes.RECT),
      ("rcWork", ctypes.wintypes.RECT),
      ("dwFlags", ctypes.wintypes.DWORD),
      ("szDevice", ctypes.wintypes.WCHAR * CCHDEVICENAME),
    ]

  windowId = ctypes.windll.user32.GetForegroundWindow()
  MONITOR_DEFAULTTONEAREST = 2
  monitorId = ctypes.windll.user32.MonitorFromWindow(windowId, MONITOR_DEFAULTTONEAREST)
  info = MONITORINFOEXW()
  info.cbSize = ctypes.sizeof(MONITORINFOEXW)
  if ctypes.windll.user32.GetMonitorInfoW(monitorId, ctypes.byref(info)):
    name = info.szDevice
  else:
    return defaultGeometry

  primaryInfo = None
  activeInfo = None
  for info in screeninfo.get_monitors():
    if info.name == name:
      activeInfo = info
    if info.is_primary:
      primaryInfo = info
  if primaryInfo is None or activeInfo is None:
    return defaultGeometry

  dx = activeInfo.x - primaryInfo.x + int(activeInfo.width / 4)
  dy = activeInfo.y - primaryInfo.y
  return f'0x0+{dx}+{dy}'

def getTkinterWindow() -> tk.Tk:
  window = tk.Tk()
  # Hide the window (while the popup dialog is displayed) without explicitly hide it so that an icon is still displayed in the taskbar.
  window.attributes("-alpha", 0)
  window.geometry(getActiveMonitorTkinterGeometry())
  iconPath = str(files('guirecognizerapp.resources').joinpath('favicon.ico'))
  window.iconbitmap(iconPath)
  # Force the window to be in front of any other window.
  window.wm_attributes('-topmost', 1)
  return window
