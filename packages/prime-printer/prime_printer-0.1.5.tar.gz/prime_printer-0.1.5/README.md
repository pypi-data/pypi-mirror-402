# 😎 Prime Printer 👀
Console I/O Helper - Print Awesome. Make It Prime 🚀

<img src="logo.png"></img>

Easy Usage, Easy handling, BIG Improvement for your needs 🎯

Easy Installation -> https://pypi.org/project/prime-printer/
```bash 
pip install prime_printer
```

<br>

**⚡Quick Look⚡**

🖨️ Printing with Delay, Type-Sound, Control, Conditions and Stylings:

<div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;"> 
<img src="./res/example_colored_delay_sound_print.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> 
<img src="./res/example_game_menu.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> 
<img src="./res/example_input_with_condition.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> </div>

<br><br>

🖼️ Print Images:

<div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;"> 
<img src="./res/example_image_print.gif" width="400" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> </div>

<br><br>

⏳ Print your Process:

<div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;"> 
<img src="./res/example_progress_bar_1.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> 
<img src="./res/example_progress_bar_2.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> 
<img src="./res/example_progress_bar_3.gif" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/> </div>

<br><br>

**Detailed Features of this Console IO Helper** 
<h1 style="float:right">🧐</h1>

- [Constants](#constants)
- [Functions](#functions)
    - [awesome_print](#awesome_print)
    - [add_special_effect](#add_special_effect)
    - [img_to_str](#img_to_str)
    - [get_progress_bar](#get_progress_bar)
    - [get_hardware](#get_hardware)
    - [get_time](#get_time)
    - [clear](#clear)
    - [get_input](#get_input)
    - [get_char](#get_char)
    - [rgb_to_python](#rgb_to_python)
    - [play_sound](#play_sound)
- [Functions not for print](#functions-not-for-print)
   - [show_images](#show_images)
   - [plot_func](#plot_func)



> There are also some examples on the bottom of the [core file](./prime_printer/cio_helper.py).

> Note: Works with Windows and Linux.



<br><br>


---
### Constants

---



All constants are available with:
```python
import prime_printer as prime

my_awesome_txt = prime.BOLD + "AWESOME" + prime.END
```

1. **Colors**: These constants represent foreground colors used for text styling in the terminal. (all RGB colors are available with the [rgb_to_python function](#rgb_to_python))
   - `PURPLE`, `CYAN`, `DARKCYAN`, `BLUE`, `GREEN`, `YELLOW`, `MAGENTA`, `RED`, `WHITE`, `BLACK`

2. **Background Colors**: These constants represent background colors used for text styling.
   - `BACKGROUND_BLACK`, `BACKGROUND_RED`, `BACKGROUND_GREEN`, `BACKGROUND_YELLOW`, `BACKGROUND_BLUE`, `BACKGROUND_MAGENTA`, `BACKGROUND_CYAN`, `BACKGROUND_WHITE`

3. **Styles**: Constants for various text styles.
   - `BOLD`, `UNDERLINE`, `REVERSED`, `HEADER`

4. **Cursor Navigation**: These are functions for moving the cursor around the terminal.
   - `UP(n)`, `DOWN(n)`, `RIGHT(n)`, `LEFT(n)`, `NEXT_LINE(n)`, `PREV_LINE(n)`, `SET_COLUMN(n)`, `SET_POSITION(n, m)`

5. **Clearing**: Functions to clear the screen or parts of the screen.
   - `CLEAR_SCREEN(n)`, `CLEAR_LINE(n)`

6. **Reset**: The constant for resetting any formatting.
   - `END`

7. **Sounds**: A list of sounds stored in the specified directory, typically for use during typing or other user interactions.
   - `PATH_TO_SOUND`, `SOUNDS`

8. **Emojis**: A set of predefined emoji constants.
   - `EMOJI_SMILE`, `EMOJI_HEART`, `EMOJI_THUMBS_UP`, etc.

9. **Helpful Lists**:
   - `NUMBERS`: List of digits `"0"` to `"9"`.
   - `ALPHABET`: List of lowercase alphabetic characters `"a"` to `"z"`.
   - `CHINESE_SIGNS`: List of common Chinese characters.
   - `GREEK_ALPHABET`: List of uppercase and lowercase Greek alphabet characters.
   - `COMMON_SIGNS`: A list of common punctuation marks and symbols.

10. **Common User Input List**: This is a comprehensive list for user input, combining emojis, numbers, the alphabet, Chinese signs, Greek letters, and common signs.
   - `COMMON_USER_INPUT_LIST` includes: emojis, numbers, alphabet, Chinese characters, Greek alphabet, and common symbols like punctuation marks and signs.



<br><br>


---
### Functions

---



#### awesome_print

`awesome_print(txt:str, *features: tuple, should_cut_str_in_chars: boll = True, should_play_sound: bool = False, should_add_backspace_at_end: bool = True, print_delay: float = None, print_delay_min: float = None, print_delay_max: float = None)`

Print text to the console with optional typing effects, sounds, styling, and custom delays — just like a cinematic terminal scene.

```python
import prime_printer as prime

prime.awesome_print("Loading complete!", prime.BOLD, prime.GREEN, should_play_sound=True, print_delay_min=0.05, print_delay_max=0.1)
```

---\> Parameters <---

| Name                        | Type    | Default    | Description                                                                 |
|-----------------------------|---------|------------|-----------------------------------------------------------------------------|
| `txt`                       | `str`   | *required* | The text to print.                                                         |
| `*features`                 | `str`   | `()`       | Optional text styling (e.g., `"BOLD"`, `"RED"`, `"ITALIC"`).               |
| `should_cut_str_in_chars`   | `bool`  | `True`     | Decides to cut the input text in parts to process, or not.                                                         |
| `should_play_sound`         | `bool`  | `False`    | Whether to play a typing sound per character.                              |
| `should_add_backspace_at_end` | `bool`  | `True`     | Whether to add a backspace/newline at the end of the printed text.         |
| `print_delay`               | `float` | `None`     | Fixed delay between each character. If `None`, uses random delay range.    |
| `print_delay_min`           | `float` | `None`     | Minimum random delay (used only if `print_delay` is `None`).               |
| `print_delay_max`           | `float` | `None`     | Maximum random delay (used only if `print_delay` is `None`).               |



---\> Sounds <---

Typing sounds play only if `should_play_sound=True` and the delay isn't too short (e.g. `> 0.1s`). A final sound plays at the end for fast modes.


<br><br>


---
#### add_special_effect

`add_special_effect(txt: str, *features: str) -> str`

Applies special styling effects (like color or emphasis) to a given string using terminal control codes or tags.

```python
import prime_printer as prime

styled = prime.add_special_effect("Warning!", prime.RED, prime.BOLD)
print(styled)
```

---\> Parameters <---

| Name         | Type     | Description                                                    |
|--------------|----------|----------------------------------------------------------------|
| `txt`        | `str`    | The original text to which you want to apply styles.           |
| `*features`  | `str`    | One or more style codes (e.g. `"BOLD"`, `"RED"`, `"ITALIC"`).  |



---\> Behavior <---

- If a single tuple of styles is passed (e.g. `(prime.BOLD, prime.GREEN)`), it's automatically unpacked.
- Styles are applied in order, wrapping the entire string each time.
- Automatically resets the styling at the end using `END`.



<br><br>


---
#### img_to_str 

`img_to_str(img_path: str, width: int = 60, is_256color: bool = False, is_truecolor: bool = True, is_unicode: bool = True) -> str`

Converts an image into a stylized text-based string for beautiful console prints using ANSI color codes and optional Unicode blocks.

```python
import prime_printer as prime

print(prime.img_to_str("./logo.png", width=80, is_256color=True))
```

---\> Parameters <---

| Name           | Type    | Default     | Description                                                             |
|----------------|---------|-------------|-------------------------------------------------------------------------|
| `img_path`     | `str`   | *required*  | Path to the image file to load.                                        |
| `width`        | `int`   | `60`        | Target width of the output in characters.                              |
| `is_256color`  | `bool`  | `False`      | Whether to use 256-color ANSI mode (for better compatibility).         |
| `is_truecolor` | `bool`  | `True`      | Enables truecolor (24-bit) output if the terminal supports it.         |
| `is_unicode`   | `bool`  | `True`      | Uses Unicode blocks for improved resolution and clarity.               |


---\> Returns <---

- `str`: The converted image as a string that can be directly printed in the terminal.

> You can use [print_image](#print_image) if you want to print your image directly.



<br><br>


---
#### print_image 

`print_image(img_path: str, width: int = 60, is_256color: bool = False, is_truecolor: bool = True, is_unicode: bool = True) -> None`

Prints an image directly to the terminal using colored text blocks — a quick and stylish way to preview images in your console.

```python
import prime_printer as prime

prime.print_image("logo.png", width=80)
```

---\> Parameters <---

| Name           | Type    | Default     | Description                                                             |
|----------------|---------|-------------|-------------------------------------------------------------------------|
| `img_path`     | `str`   | *required*  | Path to the image file to be rendered.                                 |
| `width`        | `int`   | `60`        | Desired width of the image in character columns.                       |
| `is_256color`  | `bool`  | `False`      | Enables 256-color ANSI mode (fallback for limited terminals).          |
| `is_truecolor` | `bool`  | `True`      | Enables truecolor (24-bit color) output if supported.                  |
| `is_unicode`   | `bool`  | `True`      | Enables Unicode rendering for higher pixel fidelity.                   |



> Internally uses [`img_to_str()`](#img_to_str) to convert and print.




<br><br>


---
#### get_progress_bar
 
`get_progress_bar(total, progress, should_clear=False, left_bar_char="|", right_bar_char="|", progress_char="#", empty_char=" ", size=100) -> str`

Displays a customizable progress bar in the console, ideal for visual feedback in loops, tasks, or animations.

```python
import prime_printer as prime

for i in range(101):
    prime.awesome_print(prime.get_progress_bar(total=100, progress=i))
    time.sleep(0.05)
```

---\> Parameters <---

| Name              | Type            | Default     | Description                                                              |
|-------------------|-----------------|-------------|--------------------------------------------------------------------------|
| `total`           | `int` / `float` | *required*  | Total number representing 100% of the progress.                          |
| `progress`        | `int` / `float` | *required*  | Current progress value.                                                  |
| `should_clear`    | `bool`          | `False`     | Whether to clear the console before printing.                            |
| `left_bar_char`   | `str`           | `"|"`       | Character used on the left side of the bar.                              |
| `right_bar_char`  | `str`           | `"|"`       | Character used on the right side of the bar.                             |
| `progress_char`   | `str`           | `"#"`       | Character representing the completed progress.                           |
| `empty_char`      | `str`           | `" "`       | Character representing the remaining portion.                            |
| `front_message`   | `str`           | `""`        | Message for the progress bar.                                            |
| `back_message`    | `str`           | `""`        | Message behind the progress bar.                                         |
| `size`            | `int`           | `100`       | Total width of the progress bar in characters.                           |

---\> Returns <---
- `str`: The generated progress bar string (printed if `should_print=True`).



<br><br>


---
#### get_hardware

`get_hardware() -> None`

Prints the current detected hardware and ai support. Prints information about: System, CPU, GPU and RAM.

```python
import prime_printer as prime

prime.awesome_print(prime.get_hardware())
```

<br><br>

---
#### get_time

`get_time(pattern="[DAY.MONTH.YEAR, HOUR:MINUTE]", offset_days=0, offset_hours=0, offset_minutes=0, offset_seconds=0, time_zone="Europe/Berlin")`

This function prints the current date and time based on a custom pattern and optional time offsets. It supports timezone handling and allows backspace characters at the end of the printed string, useful for updating dynamic terminal output.

```python
import prime_printer as prime

# Print the current time in the format '[DAY.MONTH.YEAR, HOUR:MINUTE]'
prime.awesome_print(prime.get_time())

# Print time 1 hour and 30 minutes in the future with a different format
prime.awesome_print(prime.get_time(pattern="[HOUR:MINUTE:SECOND on DAY/MONTH/YEAR]", offset_hours=1, offset_minutes=30))
```

In this example, the function prints the current or adjusted time formatted with your custom pattern.


---\> Parameters <---

| **Parameter**                | **Type**  | **Description**                                                                 |
|-----------------------------|-----------|---------------------------------------------------------------------------------|
| `pattern`                   | `str`     | A custom pattern using keywords like `DAY`, `MONTH`, `YEAR`, `HOUR`, `MINUTE`, and `SECOND`. |
| `offset_days`               | `int`     | Days to offset from the current time.                                          |
| `offset_hours`              | `int`     | Hours to offset from the current time.                                         |
| `offset_minutes`            | `int`     | Minutes to offset from the current time.                                       |
| `offset_seconds`            | `int`     | Seconds to offset from the current time.                                       |
| `time_zone`                 | `str`     | The IANA timezone name (e.g., `"Europe/Berlin"`). Set to `None` for UTC+0.     |

<br><br>


---
#### clear
 
`clear() -> None`

Clears the entire console screen and resets the cursor position to the top-left corner. Useful for animations, live updates, or a clean UI.

```python
import prime_printer as prime

prime.clear()
```


---\> Parameters <---

None


---\> Behavior <---

- Uses ANSI escape sequences to clear the screen (`CLEAR_SCREEN(2)`) and reset cursor (`SET_POSITION(0, 0)`).
- Prints the escape string directly to apply the effect.



<br><br>


---
#### get_input

`get_input(message='User: ', end_chars=['\n', '\r'], back_chars=['\u0008', '\b'], should_play_sound=False, *features) -> str`

Custom interactive input function with support for live console feedback, styled text, backspace handling, conditions and optional typing sounds.

```python
import prime_printer as prime

name = prime.get_input("Enter your name: ", should_play_sound=True, RED, BOLD)
```

A bit more advanced are conditions, if the user-input have to pass a given format. Here 2 examples:
```python
import prime_printer as prime

is_int = lambda x: True if all([x in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for char in x]) else False
name = prime.get_input("Enter a number: ", condition=is_int)
```

```python
import prime_printer as prime

name = prime.get_input("Do you accept (y/n): ", condition=lambda x: True if x.lower() in ['y', 'n'] else False)
```


---\> Parameters <---

| **Parameter**         | **Type**        | **Default**            | **Description**                                               |
|-----------------------|-----------------|------------------------|---------------------------------------------------------------|
| `message`             | `str`           | `'User: '`              | Prompt message shown to the user.                             |
| `get_input`           | `bool`          | `True`                  | Lower user input during the return.                           |
| `end_chars`           | `List[str]`     | `['\n', '\r']`          | Characters that indicate input completion.                    |
| `back_chars`          | `List[str]`     | `['\u0008', '\b']`      | Characters that represent backspace (deletes last input).     |
| `should_play_sound`   | `bool`          | `False`                 | Whether to play typing sounds during input.                   |
| `condition`           | `Call(x)`       | `lambda x: True`        | A condition function that the input must pass, else it will ask again. |
| `*features`           | `str` (variadic)| _None_                  | Optional style features for the input (e.g., `BOLD`, `RED`).  |

Let me know if you need further adjustments or more information!



---\> Returns <---

- `str` — The full user input as a string (with carriage returns removed).


---\> Features <---

- Styled real-time typing
- Backspace-aware input
- Optional typewriter-like sound
- Designed for terminal-based UIs or games
- Conditions (like int or y/n)




<br><br>


---
#### get_char

`get_char`

This function allows you to capture a single character of user input from the console, based on the platform.

---\> Parameters <---
- No parameters are required for this function.

---\> Description <---
- On Linux, it uses `termios` and `tty` to configure raw input, reading a single character directly from the console without waiting for the Enter key.
- On Windows, it uses `msvcrt.getch()` to capture the character input.

---\> Returns <---
- A single character (`str`) representing the current key pressed by the user.





<br><br>


---
#### rgb_to_python

`rgb_to_python(r:int, g:int, b:int) -> str`

Converts RGB color values to an ANSI escape sequence for 24-bit colors (truecolor) that can be used to color text in the terminal.


---\> Parameters <---

| Parameter | Type | Description |
|-----------|------|-------------|
| `r`       | `int` | The red component of the color (0 to 255). |
| `g`       | `int` | The green component of the color (0 to 255). |
| `b`       | `int` | The blue component of the color (0 to 255). |
| `background_color` | `int` | Whether to convert to background color or front color. (Defaults to False) |


---\> Returns <---

- **str**: The ANSI escape sequence corresponding to the RGB value, in the format `\033[38;2;r;g;b` for setting the foreground color.





<br><br>


---
#### play_sound

`play_sound(path_to_sound_file)`

This function initializes the pygame mixer, loads a sound file from the specified path, and plays it asynchronously on both Windows and Linux systems.

```python
import prime_printer as prime

path = "sounds/typing_sound.wav"
prime.play_sound(path)
```

In this example, the function will load and play the `typing_sound.wav` file located in the `sounds` directory.

---\> Parameters <---

| **Parameter**          | **Type**    | **Description**                            |
|------------------------|-------------|--------------------------------------------|
| `path_to_sound_file`   | `str`       | The file path to the sound file to be played. It should be a valid path to a `.wav` file. |





<br><br>

---
### Functions not for print

---



#### log

`log(content: str, path="./logs", file_name="output.log", clear_log=False, add_backslash=True)`

This function saves a given string of content into a `.log` file at a specified location. It can either append to the file or clear its contents first, depending on your use case. It is helpful for storing debug outputs, notes, or any kind of logging information during runtime.

```python
import prime_printer as prime

# Save a message into the default log file
prime.log("Process started...")

# Save to a custom location and clear the log first
prime.log("First line of a fresh log", path="my_logs", file_name="run.log", clear_log=True)

# Append more content to the same file
prime.log("Another log entry.", path="my_logs", file_name="run.log")

# Use other prime functions in combination
prime.log(f"Start Training, detecting hardware...\n{prime.get_hardware()}", 
          file_name=f"training_{prime.get_time(pattern='YEAR_MONTH_DAY-HOUR_MINUTE')}")
```

In this example, the `log()` function helps you manage logs in a clean and customizable way.

---

> Parameters <---

| **Parameter**    | **Type** | **Description**                                                                 |
|------------------|----------|---------------------------------------------------------------------------------|
| `content`        | `str`    | The text content to be saved to the log file.                                  |
| `path`           | `str`    | Directory where the log file will be stored. Defaults to `"./logs"`.           |
| `file_name`      | `str`    | Name of the log file (with or without `.log` extension). Defaults to `"output.log"`. |
| `clear_log`      | `bool`   | If `True`, clears the file before writing. If `False`, appends to existing log. |
| `add_backslash`  | `bool`   | If `True`, add a backslash at the end of the given content string.             |


<br><br>

---
#### show_images

`show_images(image_paths, title=None, image_width=5, axis=False, color_space="gray", cmap=None, cols=2, save_to=None, hspace=0.01, wspace=0.01, use_original_sytle=False, invert=False)`

This function visualizes one or multiple images in a flexible grid layout using `matplotlib`. It supports different color spaces, image inversion, custom figure styling, and optional saving of the visualized image.

```python
from image_utils import show_images

paths = ["images/cat.png", "images/dog.png"]
show_images(paths, title="Animals", color_space="RGB", cols=2)
```

In this example, two images will be loaded, converted to RGB color space, and displayed in a 2-column layout with the title "Animals".



---\> Parameters <---

| **Parameter**            | **Type**        | **Description**                                                                 |
|--------------------------|-----------------|---------------------------------------------------------------------------------|
| `image_paths`            | `List[str]`     | List of paths to the images to be visualized.                                  |
| `title`                  | `str`, optional | Title of the entire image plot. Default is `None`.                             |
| `image_width`            | `int`, optional | Width of each image in inches. Default is `5`.                                 |
| `axis`                   | `bool`, optional| Whether to display axis ticks and labels. Default is `False`.                  |
| `color_space`            | `str`, optional | Colorspace for displaying images: `"RGB"`, `"BGR"`, `"gray"`, or `"HSV"`. Default is `"gray"`. |
| `cmap`                   | `str`, optional | Matplotlib colormap to use (mostly for grayscale images). Default is `None`.   |
| `cols`                   | `int`, optional | Number of columns in the plot grid. Default is `2`.                            |
| `save_to`                | `str`, optional | File path to save the final visualization as an image. Default is `None`.      |
| `hspace`                 | `float`, optional| Horizontal spacing between images. Default is `0.01`.                          |
| `wspace`                 | `float`, optional| Vertical spacing between images. Default is `0.01`.                            |
| `use_original_sytle`     | `bool`, optional| Whether to use the current matplotlib style. Default is `False`.               |
| `invert`                 | `bool`, optional| Whether to invert the images before displaying. Default is `False`.            |



---\> Returns <---

| **Return** | **Type**        | **Description**                      |
|------------|------------------|--------------------------------------|
| `images`   | `np.ndarray`     | Array of the loaded images.          |



<br><br>

---
#### plot_func

`plot_func(func, should_plot=True, should_print=False, print_width=60, should_print_information=True, derivation_degree=3, root_degree=1, transparent=True, color='white', bg_color='white', function_color="steelblue", linestyle='-', linewidth=2.0, marker='None', lim=10, n=100, x_size=15, y_size=10, grid=False, xlim=None, ylim=None, coordinate=False, small=False)`

This function plots a mathematical expression given as a string. It supports symbolic differentiation and integration (via SymPy), optional display of results in ASCII format, and customizable styling for the matplotlib plot.

```python
import prime_printer as prime

# Plot and print information about a function
prime.plot_func("sin(x) + x^2")

# Show only ASCII output, without rendering the plot
prime.plot_func("x^3 - 3*x", should_plot=False, should_print=True)

# Customize the appearance and derivative depth
prime.plot_func("cos(x)", derivation_degree=2, root_degree=1, function_color="red", linestyle='--')
```

In this example, the function string is parsed and evaluated over a defined range. Derivatives and integrals are shown based on the user’s input. The plot can be shown as an image or ASCII.

--\> Parameters <---

| **Parameter**             | **Type**     | **Description**                                                                 |
|--------------------------|--------------|---------------------------------------------------------------------------------|
| `func`                   | `str`        | A string representing the function to plot (e.g., `"x^2 + sin(x)"`). Use `'x'` as variable. |
| `should_plot`            | `bool`       | Whether to display the plot in a window (via `matplotlib`).                    |
| `should_print`           | `bool`       | Whether to print an ASCII representation of the plot.                          |
| `print_width`            | `int`        | Width (in characters) for ASCII plot output.                                   |
| `should_print_information` | `bool`     | Whether to print symbolic function info, roots and derivatives.                |
| `derivation_degree`      | `int`        | Number of times the function is symbolically differentiated.                   |
| `root_degree`            | `int`        | Number of times the function is symbolically integrated.                       |
| `transparent`            | `bool`       | Whether the background of the ASCII plot should be transparent.                |
| `color`                  | `str`        | Color for plot edges and tick marks.                                           |
| `bg_color`               | `str`        | Background color of the plot.                                                  |
| `function_color`         | `str`        | Line color for the function plot.                                              |
| `linestyle`              | `str`        | Style of the function line (`'-'`, `'--'`, `':'`, etc.).                       |
| `linewidth`              | `float`      | Thickness of the plotted line.                                                 |
| `marker`                 | `str`        | Marker for plotted points (`'o'`, `'.'`, etc., or `'None'` to disable).        |
| `lim`                    | `int`        | Symmetric range for x-axis (from `-lim` to `+lim`), if `xlim` is not set.      |
| `n`                      | `int`        | Number of points to sample for plotting.                                       |
| `x_size`                 | `float`      | Width of the figure in centimeters.                                            |
| `y_size`                 | `float`      | Height of the figure in centimeters.                                           |
| `grid`                   | `bool`       | Whether to show grid lines in the plot.                                        |
| `xlim`                   | `list[float]`| Manual x-axis limits; overrides `lim` if set.                                  |
| `ylim`                   | `list[float]`| Manual y-axis limits; if `None`, auto-scaled based on y values.                |
| `coordinate`             | `bool`       | Whether to draw zero-centered x and y axes (origin-based coordinate system).   |
| `small`                  | `bool`       | Use tight layout to reduce padding and spacing in the plot.                    |


---










