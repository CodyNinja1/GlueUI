# GlueUi: A basic UI library built upon pySDL2 for Python 3.12
# Copyright (C) 2024 Ahmad S.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Literal
import sdl2
import sdl2.ext as sdl2ext
import sdl2.sdlttf as sdlttf
import ctypes

class Nat2:
    def __init__(self, X: int, Y: int):
        self.X = X
        self.Y = Y
    
    def __add__(self, other):
        # If adding another Nat2 instance
        if isinstance(other, Nat2):
            return Nat2(self.X + other.X, self.Y + other.Y)
        # If adding an integer to both X and Y
        elif isinstance(other, int):
            return Nat2(self.X + other, self.Y + other)
        # If adding an unsupported type, raise an error
        else:
            return NotImplemented
    
    def __repr__(self):
        return f'Nat2({self.X}, {self.Y})'
        
class Rect:
    def __init__(self, XY: Nat2, WH: Nat2):
        self.XY = XY
        self.WH = WH

class Vec4:
    def __init__(self, X: float, Y: float, Z: float, W: float = 1):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.W = W

    def ToSdl2Color(self):
        return sdl2ext.Color(int(self.X * 255), int(self.Y * 255), int(self.Z * 255), int(self.W * 255))

def TupleToVec4(t: tuple[int, int, int]) -> Vec4:
    return Vec4(t[0], t[1], t[2])

def ColorPaletteToVec4(l: list[tuple]) -> list[Vec4]:
    return list([TupleToVec4(tup) for tup in l])

class UiManager:
    def __init__(self, WindowTitle: str = "GlueUi", Resolution: Nat2 = Nat2(848, 480)):
        # Initialize SDL and TTF
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        sdlttf.TTF_Init()
        
        self.Window = sdl2.SDL_CreateWindow(
            WindowTitle.encode('ascii'),
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            Resolution.X, Resolution.Y, sdl2.SDL_WINDOW_SHOWN
        )
        
        # Use SDL_RENDERER_PRESENTVSYNC for smooth rendering and double buffering
        self.Renderer = sdl2.SDL_CreateRenderer(self.Window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)
        
        # Get window surface for legacy purposes (if needed later)
        self.Surface = sdl2.SDL_GetWindowSurface(self.Window)
        
        self.Event = sdl2.SDL_Event()
        self.Running: bool = True
        self.Fonts: dict[str, any] = {}
        self.ActiveMenu: Literal["Main", "Settings", "Schedule"] = "Main"
        
        # Initialize the list to store images and textures
        self.Images: list = []  # List to store surfaces
        self.Textures: list = []  # List to store textures

        # Checkbox and button states
        self.CheckboxStates: dict = {}
        self.Buttons: dict[str, dict] = {}  # Dictionary to store states of all buttons

        # Color palette and UI mode
        self.ColorPalette: list[Vec4] = [Vec4(0, 0.922, 0.451), Vec4(0, 0.78, 0.376), Vec4(0, 0.62, 0.298), Vec4(0, 0.459, 0.224), Vec4(0, 0.302, 0.149)]
        self.IsDarkMode: bool = True

    def Button(self, Label: str, Pos: Nat2, FontName: str, OnClick: callable, 
           ColorTextIdx: int = 2, ColorHoverIdx: int = 1, ColorNormalIdx: int = 3, 
           ) -> tuple[Rect, bool, bool]:
        """
        Creates and renders a button UI element.

        Parameters:
            Label (str): The text displayed on the button. This also serves as its identifier.
            Pos (Nat2): The position (top-left corner) of the button in the window.
            OnClick (callable): The function to call when the button is clicked.
            ColorTextIdx (int): The color palette index for the button text.
            ColorHoverIdx (int): The color palette index for the button background when hovered.
            ColorNormalIdx (int): The color palette index for the button background in its normal state.
            FontIdx (int, optional): The index of the font to use for rendering the label. Defaults to 0.

        Returns:
            tuple[Rect, bool, bool]: 
                - `Rect`: The rectangle defining the button's position and size.
                - `bool`: Whether the button was clicked in the current frame.
                - `bool`: Whether the button is currently being hovered.
        """
        # Initialize button state if not already present
        if Label not in self.Buttons:
            self.Buttons[Label] = {"active": True, "mouse_down": True, "prev_mouse_down": True} # HACK

        # Calculate button rectangle
        TextRect: Rect = self.Text(Label, Pos, FontName, ColorTextIdx, NoDraw=True)
        ButtonRect: Rect = Rect(TextRect.XY + -10, TextRect.WH + 20)

        clicked = False  # Tracks whether the button was clicked in this frame
        hovered = self.RectIsHover(ButtonRect)  # Tracks whether the button is hovered

        # Get the current mouse state (pressed or released)
        mouse_down = self.IsClick("Left")

        # Check if mouse is hovering and clicked
        if hovered:
            ColorIdx = ColorHoverIdx
            # We register a click only when the mouse goes from "not pressed" to "pressed"
            if mouse_down and not self.Buttons[Label]["prev_mouse_down"]:
                OnClick()  # Call the click handler
                clicked = True  # Mark the button as clicked
        else:
            ColorIdx = ColorNormalIdx

        # Render the button
        self.Rect(ButtonRect.XY, ButtonRect.WH, ColorIdx)
        self.Text(Label, Pos, FontName, ColorTextIdx)

        # Update button state
        self.Buttons[Label]["prev_mouse_down"] = mouse_down

        # Return the button's rectangle, clicked state, and hovered state
        return ButtonRect, clicked, hovered

    def GetModeIcon(self):
        return "" if not self.IsDarkMode else ""

    def SwitchMode(self):
        self.IsDarkMode = not self.IsDarkMode

    def ColorPaletteMode(self) -> list[Vec4]:
        return self.ColorPalette[::-1] if not self.IsDarkMode else self.ColorPalette

    def RectBorder(self, Pos: Nat2, Size: Nat2, ColorIdx: int, Thickness: int = 1):
        """
        Draws a border for a rectangle at a specified position and size using `self.Rect`.

        Parameters:
            Pos (Nat2): Top-left position of the rectangle.
            Size (Nat2): Width and height of the rectangle.
            Color (Vec4): RGBA color of the border.
            Thickness (int): Thickness of the border lines.
        """
        # Top border
        self.Rect(Pos, Nat2(Size.X, Thickness), ColorIdx)
        # Left border
        self.Rect(Pos, Nat2(Thickness, Size.Y), ColorIdx)
        # Bottom border
        self.Rect(Nat2(Pos.X, Pos.Y + Size.Y - Thickness), Nat2(Size.X, Thickness), ColorIdx)
        # Right border
        self.Rect(Nat2(Pos.X + Size.X - Thickness, Pos.Y), Nat2(Thickness, Size.Y), ColorIdx)

    def Checkbox(self, Label: str, Pos: Nat2, FontName: str, 
             ColorBorderIdx: int = 0, ColorInnerIdx: int = 1, 
             ColorInnerHoverIdx: int = 2, ColorTextIdx: int = 0) -> tuple[bool, bool]:
        """
        Render a checkbox UI component and toggle its state when clicked.

        Parameters:
            Label (str): The label to display next to the checkbox.
            Pos (Nat2): The position of the checkbox (top-left corner of the checkbox).
            ColorBorderIdx (int): The color palette index for the checkbox border.
            ColorInnerIdx (int): The color palette index for the checkbox fill when checked.
            ColorInnerHoverIdx (int): The color palette index for the checkbox fill when hovered.
            ColorTextIdx (int): The color palette index for the checkbox text.

        Returns:
            tuple[bool, bool]: 
                - `bool`: The current state of the checkbox (True for checked, False for unchecked).
                - `bool`: Whether the checkbox is currently being hovered.
        """
        # Define the checkbox size
        CheckboxSize = Nat2(20, 20)
        CheckboxRect = Rect(Pos, CheckboxSize)

        # Initialize checkbox state if not already present
        if Label not in self.CheckboxStates:
            self.CheckboxStates[Label] = {"checked": False, "mouse_down": False}

        hovered = self.RectIsHover(CheckboxRect)  # Tracks whether the checkbox is hovered

        # Handle mouse hover and click for toggling the state
        if hovered:
            if not self.CheckboxStates[Label]["checked"]:
                self.Rect(Pos + Nat2(4, 4), Nat2(CheckboxSize.X - 8, CheckboxSize.Y - 8), ColorInnerHoverIdx)
            if self.IsClick("Left"):
                if not self.CheckboxStates[Label]["mouse_down"]:
                    self.CheckboxStates[Label]["checked"] = not self.CheckboxStates[Label]["checked"]
                    self.CheckboxStates[Label]["mouse_down"] = True
            else:
                self.CheckboxStates[Label]["mouse_down"] = False
        else:
            self.CheckboxStates[Label]["mouse_down"] = False

        # Draw the filled rectangle if checked
        if self.CheckboxStates[Label]["checked"]:
            self.Rect(Pos + Nat2(4, 4), Nat2(CheckboxSize.X - 8, CheckboxSize.Y - 8), ColorInnerIdx)

        # Draw the checkbox border
        self.RectBorder(Pos, CheckboxSize, ColorBorderIdx, Thickness=2)

        # Render the label
        LabelPos = Pos + Nat2(CheckboxSize.X + 10, 0)
        self.Text(Label, LabelPos, FontName, ColorIdx=ColorTextIdx)

        # Return the checkbox's checked state and hovered state
        return self.CheckboxStates[Label]["checked"], hovered

    def ChangeActiveMenu(self, MenuName: str):
        self.ActiveMenu = MenuName

    def GetMouseState(self):
        """Get the current cursor position and mouse button states."""
        x_pos = ctypes.c_int(0)
        y_pos = ctypes.c_int(0)
        
        # Get the mouse position and button states
        button_state = sdl2.SDL_GetMouseState(ctypes.byref(x_pos), ctypes.byref(y_pos))
        
        return x_pos.value, y_pos.value, button_state

    def IsClick(self, Button: Literal["Left", "Right", "Middle"]) -> bool:
        """Check if the specified mouse button is currently clicked."""
        _, _, button_state = self.GetMouseState()

        if Button == "Left":
            return bool(button_state & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_LEFT))
        elif Button == "Right":
            return bool(button_state & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_RIGHT))
        elif Button == "Middle":
            return bool(button_state & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_MIDDLE))
        else:
            raise ValueError("Button must be 'Left', 'Right', or 'Middle'")

    def RectIsHover(self, TRect: Rect):
        return self.PointInsideRect(self.GetCursorPosition(), TRect.XY, TRect.WH)

    def ColorOnHover(self, TRect: Rect, Color1Idx: int, Color2Idx: int):
        return Color1Idx if self.RectIsHover(TRect) else Color2Idx

    def PointInsideRect(self, Point: Nat2, RectPos: Nat2, RectSize: Nat2) -> bool:
        return RectPos.X <= Point.X <= RectPos.X + RectSize.X and RectPos.Y <= Point.Y <= RectPos.Y + RectSize.Y

    def GetCursorPosition(self):
        """Get the current cursor position relative to the window."""
        x_pos = ctypes.c_int(0)
        y_pos = ctypes.c_int(0)
        sdl2.SDL_GetMouseState(ctypes.byref(x_pos), ctypes.byref(y_pos))
        return Nat2(x_pos.value, y_pos.value)

    def Update(self):
        """Update the display surface."""
        sdl2.SDL_UpdateWindowSurface(self.Window)

    def CreateButton(self):
        self.Buttons.append([False, False])

    def Rect(self, Pos: Nat2, Size: Nat2, ColorIdx: int):
        """Draw a rectangle on the surface."""
        Color = self.ColorPaletteMode()[ColorIdx]
        ColorSdl = Color.ToSdl2Color()
        RectSdl = sdl2.SDL_Rect(Pos.X, Pos.Y, Size.X, Size.Y)
        sdl2.SDL_FillRect(self.Surface, RectSdl, sdl2.SDL_MapRGBA(self.Surface.contents.format,
                                                                  ColorSdl.r, ColorSdl.g, ColorSdl.b, ColorSdl.a))
    
    def LoadFont(self, Filepath: str, Name: str, Size: int = 24, Bold: bool = False):
        """Load a TTF font into the UiManager."""
        Font = sdlttf.TTF_OpenFont(Filepath.encode('utf-8'), Size)
        if Bold:
            sdl2.sdlttf.TTF_SetFontStyle(Font, sdl2.sdlttf.TTF_STYLE_BOLD)
        self.Fonts[Name] = Font
        if not Font:
            raise RuntimeError(f"Failed to load font from {Filepath}: {sdl2.SDL_GetError().decode('utf-8')}")

    def Text(self, Str: str, Pos: Nat2, FontName: str, ColorIdx: int = 2, NoDraw: bool = False) -> Rect:
        """Render text on the surface."""
        Color = self.ColorPaletteMode()[ColorIdx]
        if len(self.Fonts) == 0:
            raise RuntimeError("No font loaded. Use LoadFont() before rendering text.")
        
        # Convert the color
        ColorSdl = sdl2.SDL_Color(int(Color.X * 255), int(Color.Y * 255), int(Color.Z * 255), int(Color.W * 255))
        
        # Render the text to an SDL surface
        TextSurface = sdlttf.TTF_RenderUTF8_Blended(self.Fonts[FontName], Str.encode('utf-8'), ColorSdl)
        if not TextSurface:
            raise RuntimeError(f"Failed to render text: {sdl2.SDL_GetError().decode('utf-8')}")
        
        # Blit the text surface onto the window surface
        TextRect = sdl2.SDL_Rect(Pos.X, Pos.Y, TextSurface.contents.w, TextSurface.contents.h)
        Rxy = Nat2(TextRect.x, TextRect.y)
        Rwh = Nat2(TextRect.w, TextRect.h)
        RRect = Rect(Rxy, Rwh)
        if not NoDraw: sdl2.SDL_BlitSurface(TextSurface, None, self.Surface, TextRect)
        
        # Free the temporary text surface
        sdl2.SDL_FreeSurface(TextSurface)
        return RRect

    def TextWrapped(self, Str: str, Pos: Nat2, FontName: str, ColorIdx: int):
        Strings = Str.split("\n")
        for Idx, String in enumerate(Strings):
            if String == "":
                continue
            self.Text(String, Pos + Nat2(0, Idx * 16), FontName, ColorIdx=ColorIdx)

    def MainLoop(self):
        """Render each frame."""
        while sdl2.SDL_PollEvent(ctypes.byref(self.Event)) != 0:
            if self.Event.type == sdl2.SDL_QUIT:
                self.Running = False
                break
        
        sdl2.SDL_RenderPresent(self.Renderer)
        self.Update()
        sdl2.SDL_Delay(1)

    def Quit(self):
        """Clean up resources."""
        for Font in self.Fonts:
            sdlttf.TTF_CloseFont(self.Fonts[Font])
        sdl2.SDL_DestroyWindow(self.Window)
        sdl2.SDL_Quit()
        sdlttf.TTF_Quit()
