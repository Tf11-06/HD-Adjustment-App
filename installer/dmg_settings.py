# dmgbuild settings for the Mac drag-to-Applications installer.

format = "UDZO"
filesystem = "HFS+"
compression_level = 9

files = ["dist/HDProcessor.app"]
symlinks = {"Applications": "/Applications"}

window_rect = ((100, 100), (760, 460))
default_view = "icon-view"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False

background = "builtin-arrow"
icon_size = 136
text_size = 14
label_pos = "bottom"
arrange_by = None

icon_locations = {
    "HDProcessor.app": (190, 220),
    "Applications": (570, 220),
}
