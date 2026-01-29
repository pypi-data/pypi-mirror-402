# coloray

[![PyPI version](https://img.shields.io/pypi/v/coloray?color=blue&label=PyPI)](https://pypi.org/project/coloray/)
[![PyPI downloads](https://img.shields.io/pypi/dm/coloray?color=green&label=downloads)](https://pypistats.org/packages/coloray)
[![License](https://img.shields.io/badge/license-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.en.html)
[![GitHub stars](https://img.shields.io/github/stars/leafcss/coloray?style=social)](https://github.com/leafcss/coloray/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/leafcss/coloray?style=social)](https://github.com/leafcss/coloray/watchers)

a minimal python library for colorful terminal output.

works with foreground colors, background colors, gradients, and text styles. works in **24-bit truecolor** or **8-bit fallback** mode.

---

## features

- 24 bit support  
- 8 bit fallback for older terminals  
- gradients (foreground + background)  
- background colors with optional foreground  
- text styles: bold, italic, underline, strike, reverse  
- easy to use, just like colorama but even better fr 

---

## install

```bash
pip install coloray
````

---

## how to use

### switching modes

you can pick between 24-bit truecolor and 8-bit colors:

```python
from coloray import truecolor, ansi8bit

truecolor()  # 24 bit mode
ansi8bit()   # 8 bit mode
```

---

### colors

```python
from coloray import color

print(color.red + "red" + color.RESET)
print(color.orange + "orange" + color.RESET)
print(color.yellow + "yellow" + color.RESET)
print(color.lime + "lime" + color.RESET)
print(color.green + "green" + color.RESET)
print(color.cyan + "cyan" + color.RESET)
print(color.lightblue + "lightblue" + color.RESET)
print(color.blue + "blue" + color.RESET)
print(color.magenta + "magenta" + color.RESET)
print(color.black + "black" + color.RESET)
print(color.white + "white" + color.RESET)
print(color.RESET + "reset text" + color.RESET)

# hex and rgb colors
print(color.hex("#058aff") + "hex color" + color.RESET)
print(color.rgb(255,0,255) + "rgb color" + color.RESET)
```

---

### text styles

```python
from coloray import style

print(style.bold + "bold" + style.RESET)
print(style.italic + "italic" + style.RESET)
print(style.underline + "underline" + style.RESET)
print(style.strike + "strike" + style.RESET)
print(style.bold + style.underline + style.italic + "combined styles" + style.RESET)
```

---

### background colors

```python
# named backgrounds
print(color.bg.red + "bg red" + color.RESET)
print(color.bg.orange + "bg orange" + color.RESET)
print(color.bg.yellow + "bg yellow" + color.RESET)

# background + foreground
print(color.bg.white + color.black + "bg white with black text" + color.RESET + style.RESET)

# rgb / hex backgrounds
print(color.bg.rgb(128,0,128) + color.yellow + "bg purple with yellow text" + color.RESET + style.RESET)
print(color.bg.hex("#00ffff") + color.magenta + "bg cyan with magenta text" + color.RESET + style.RESET)
```

---

### gradients

```python
from coloray import color

# foreground gradient
print(color.gradient("#ff0000","#ff8800","gradient red->orange") + color.RESET)
print(color.gradient("#00ff00","#0000ff","gradient green->blue") + color.RESET)
print(color.gradient("#ff00ff","#00ffff","gradient magenta->cyan") + color.RESET)

# background gradient with optional foreground color
print(color.bg.gradient("#ff0000","#ff8800","gradient bg", fg=color.black) + style.RESET)
```

---

### notes

* always use `color.RESET` and `style.RESET` at the end to reset colors and styles.
* gradients, hex, and rgb automatically adjust to 24 bit or 8 bit mode.
* background gradients can take a fixed `fg` color to keep text readable.
* all named colors are available for foreground and background (e.g., `color.red`, `color.bg.red`).

