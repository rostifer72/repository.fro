import xbmc
import sys

listitem = sys.listitem
widget_status = listitem.getProperty("fen_widget")
path = listitem.getPath()

def furkit_playback_context_menu():
    xbmc.executebuiltin('RunPlugin(plugin://plugin.video.fen/?mode=playback_menu)')

if __name__ == '__main__':
    furkit_playback_context_menu()
