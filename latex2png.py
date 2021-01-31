import matplotlib
from matplotlib import pyplot as plt
from matplotlib import text as mtext

matplotlib.rcParams['text.latex.preamble'] = r"\usepackage[T2A]{fontenc}"
matplotlib.rcParams['font.family'] = 'serif'


def autowrap_text(textobj, renderer):
    """Wraps the given matplotlib text object so that it doesn't exceed the
    boundaries of the axis it is plotted in."""
    # Get the starting position of the text in pixels...
    x0, y0 = textobj.get_transform().transform(textobj.get_position())
    # Get the extents of the current axis in pixels...
    clip = textobj.figure.get_window_extent()
    # Set the text to rotate about the left edge (nonsensical otherwise)
    textobj.set_rotation_mode('anchor')

    # Get the amount of space in the direction of rotation to the left and
    # right of x0, y0 (left and right are relative to the rotation)
    rotation = textobj.get_rotation()
    right_space = min_dist_inside((x0, y0), rotation, clip)
    left_space = min_dist_inside((x0, y0), rotation - 180, clip)

    # Use either the left or right distance depending on the h-alignment.
    alignment = textobj.get_horizontalalignment()
    if alignment is 'left':
        new_width = right_space
    elif alignment is 'right':
        new_width = left_space
    else:
        new_width = 2 * min(left_space, right_space)

    # Convert to characters with a minimum width of 1 character
    wrap_width = max(1, new_width // pixels_per_char(textobj))
    try:
        wrapped_text = safewrap(textobj.get_text(), wrap_width)
    except TypeError:
        # This appears to be a single word
        wrapped_text = textobj.get_text()
    textobj.set_text(wrapped_text)

def min_dist_inside(point, rotation, box):
    """Gets the space in a given direction from "point" to the boundaries
    of "box" (where box is an object with x0, y0, x1, & y1 attributes,
    point is a tuple of x,y, and rotation is the angle in degrees)"""
    from math import sin, cos, radians
    x0, y0 = point
    rotation = radians(rotation)
    distances = []
    threshold = 0.0001
    if cos(rotation) > threshold:
        # Intersects the right axis
        distances.append((box.x1 - x0) / cos(rotation))
    if cos(rotation) < -threshold:
        # Intersects the left axis
        distances.append((box.x0 - x0) / cos(rotation))
    if sin(rotation) > threshold:
        # Intersects the top axis
        distances.append((box.y1 - y0) / sin(rotation))
    if sin(rotation) < -threshold:
        # Intersects the bottom axis
        distances.append((box.y0 - y0) / sin(rotation))
    return min(distances)

def pixels_per_char(textobj):
    """Determines the average width of a character of the given textobj
    by drawing a test string and calculating it's length"""
    test_text = 'Найти значение неопределенного интеграла'
    orig_text = textobj.get_text()
    textobj.set_text(test_text)
    width = textobj.get_window_extent().width
    textobj.set_text(orig_text)
    return width / len(test_text)

def safewrap(text, width):
    """Wraps text, but avoids putting linebreaks in tex strings"""
    import textwrap, re
    # If it's not a tex string, just wrap it as usual...
    if '$' not in text:
        return textwrap.fill(text, width)

    # Tex segments will be inside two "$"'s, so we want the odd items
    segments = text.split('$')
    tex = segments[1::2]

    # Temporarily replace spaces and dashes inside tex segments so that
    # they will be treated as long words by textwrap...
    segments[1::2] = [re.sub(r'[^\d\w]', '', re.sub(r'\\\w+', 'I', x)) for x in tex]
    # Rejoin the temp tex strings with the rest of the text and wrap it
    temp_text = '$'.join(segments)
    wrapped = textwrap.fill(temp_text, width,
                            break_long_words=False, replace_whitespace=False)

    # Put the original tex strings back in between $'s
    segments = wrapped.split('$')
    segments[1::2] = tex
    return '$'.join(segments)


def on_draw(event):
    from matplotlib import text as mtext
    fig = event.canvas.figure

    # Cycle through all artists in all the axes in the figure
    # for ax in fig.axes:
    for artist in fig.get_children():
        # If it's a text artist, wrap it...
        if isinstance(artist, mtext.Text):
            autowrap_text(artist, event.renderer)

    # Temporarily disconnect any callbacks to the draw event...
    # (To avoid recursion)
    func_handles = fig.canvas.callbacks.callbacks[event.name]
    fig.canvas.callbacks.callbacks[event.name] = {}
    # Re-draw the figure..
    fig.canvas.draw()
    # Reset the draw event callbacks
    fig.canvas.callbacks.callbacks[event.name] = func_handles


def draw_integral_problem(problem, integral):
    import io

    plt.axis('off')
    fig = plt.figure()
    # fig.text(0.01, 0.51, problem, va='bottom', usetex=False, size=11)
    fig.text(0.01, 0.49, integral, va='top', usetex=False, size=18)
    # fig.canvas.mpl_connect('draw_event', on_draw)
    out = io.BytesIO()
    fig.savefig(out, format='png', bbox_inches='tight', dpi=100)
    out.seek(0)
    return out


if __name__ == '__main__':
    from PIL import Image, ImageChops
    
    problem = r"Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл Найти интеграл"
    integral = r"9.353. $\int \frac{\arcsin x}{\sqrt{\left(1-x^{2}\right)^{3}}} d x$"
    Image.open(draw_integral_problem(problem, integral)).show()
