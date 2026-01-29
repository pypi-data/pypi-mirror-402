from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("orange3-bcaats")
except PackageNotFoundError:
    __version__ = "0.0.1"

NAME = "BCAATs"
DESCRIPTION = ""
BACKGROUND = "#f6612d"
ICON = "icons/addon_icon.png"


