from GlueUi import GlueUiManager, Nat2

Tooltip = ""

def RenderTooltip(UiMgr: GlueUiManager):
    global Tooltip
    UiMgr.TextWrapped(Tooltip, Nat2(600, 10), "Medium", 0)

def SetTooltip(String: str):
    global Tooltip
    if String == "":
        Tooltip = "Description:"
    else:
        Tooltip = f"Description:\n\n{String}"

def InitUi(UiMgr: GlueUiManager, Log: Logger):
    UiMgr.LoadFont("Fonts/GeistMonoLight.ttf", "Large", 32)
    UiMgr.LoadFont("Fonts/GeistMonoExtraLightManiaIcons.ttf", "Medium", 16)
    UiMgr.LoadFont("Fonts/GeistMonoExtraLightManiaIcons.ttf", "SmallIcons", 11)

def Main():
    UiMgr = GlueUiManager(WindowTitle = "Hello world!")
    InitUi(UiMgr)

    Log.Log("[FRONTEND] Hello, world!")
    Log.Log(f"[FRONTEND] ChannelNotif {Setting.Updates.Version}")

    while UiMgr.Running:
        UiMgr.Begin()

        # this is just to clear the screen
        UiMgr.Rect(Nat2(0, 0), Nat2(848, 480), ColorIdx=-1)

        SetTooltip("Tooltip. Hover over an\nelement to view its\ndescription.")  

        UiMgr.Text("Hello, world!", Nat2(10, 10), "Large")
    
        ButtonRect, Clicked, ButtonHovered = UiMgr.Button(UiMgr.GetModeIcon(), Nat2(100, 100), "Medium", UiMgr.SwitchMode) # On click, UiMgr.SwitchMode is called
        if ButtonHovered:
            SetTooltip("Dark/light mode switch.")
          
        Checked, CheckboxHovered = UiMgr.Checkbox("Testing", Nat2(100, 160), "Medium")
        if CheckboxHovered:
            SetTooltip(f"Checkbox.\nIt is{"n't" if not Checked else ""} checked.")

        UiMgr.End()

    UiMgr.Quit()

if __name__ == "__main__":
    Main()
