# **📦 PIX-8 — Tiny Fantasy Console**

PIX-8 is a minimal, retro-style fantasy console written in Python.  
 It lets you create **tiny games** with a simple PEP-8-inspired Python cartridge format.

---

## **⚡ Features**

* 128×128 pixel display

* 16-color palette

* Simple drawing API: `cls()`, `pset()`, `rectfill()`

* Input: arrow keys \+ `Z/X` as buttons

* PEP-8–style cartridges (`init(pix)`, `update(pix)`, `draw(pix)`)

* Runs as a single Python file (`pix8.py`)

---

## **🏁 Installation**

`git clone <repo-url>`  
`cd pix8`  
`pip install .`

Or if you just want to run it locally without pip:

`python pix8.py game.py`

---

## **🎮 Writing a Cartridge**

Create a Python file, for example `game.py`:

`metadata = {"title": "Tiny Demo"}`

`def init(pix):`  
    `pix.x = 60`  
    `pix.y = 60`

`def update(pix):`  
    `if pix.btn("left"):`  
        `pix.x -= 1`  
    `if pix.btn("right"):`  
        `pix.x += 1`

`def draw(pix):`  
    `pix.cls(1)`  
    `pix.rectfill(pix.x, pix.y, 8, 8, 8)`

Run it:

`pix8 game.py`

---

## **🔑 API Reference**

| Function | Description |
| ----- | ----- |
| `pix.cls(color=0)` | Clear the screen |
| `pix.pset(x, y, color=7)` | Draw a single pixel |
| `pix.rectfill(x, y, w, h, color=7)` | Draw a filled rectangle |
| `pix.btn("left")` | Check if a button is pressed (`left`, `right`, `up`, `down`, `a`, `b`) |
| `pix.flip()` | Update the screen and tick FPS |

---

## **📄 License**

MIT License — free to use, modify, and share.

