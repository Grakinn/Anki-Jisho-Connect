from aqt.qt import QMenu

def get_grkn_menu(mw):
    for attr in ["menuBar", "menubar"]:
        menubar = getattr(mw.form, attr, None)
        if menubar:
            for act in menubar.actions():
                menu = act.menu()
                if menu and (menu.title().replace("&", "") == "GRKN"):
                    return menu
            grkn_menu = QMenu("&GRKN", mw)
            menubar.addMenu(grkn_menu)
            return grkn_menu
    return None
