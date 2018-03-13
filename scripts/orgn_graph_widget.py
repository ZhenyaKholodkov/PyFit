import matplotlib

matplotlib.use('Qt5Agg', force=True)
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import peakutils

class OrgnGrpahWidget():
    def __init__(self, figsize, settings, animate_call_back):
        self.animate_call_back = animate_call_back
        self.figure, self.ax = plt.subplots(1, 1, figsize=figsize)
        self.canvas = FigureCanvas(self.figure)
        self.lines = []
        self.possible_colors = ['b--', 'g--', 'r--', 'c--', 'm--', 'y--', 'w--']

        self.button_pressed = False
        self.settings = settings

        #Markers
        self.mouse_on_left_marker = False
        self.mouse_on_right_marker = False
        self.edit_mode = False
        self.detect_x_range = 0
        self.left_marker = None
        self.right_marker = None
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self.on_button_press_event)
        self.canvas.mpl_connect('button_release_event', self.on_button_release_event)

    def on_button_press_event(self, event):
        self.button_pressed = True
        if self.mouse_on_left_marker or self.mouse_on_right_marker:
            self.edit_mode = True

    def on_button_release_event(self, event):
        self.button_pressed = False
        self.edit_mode = False

    def on_mouse_move(self, event):
        if self.left_marker is not None and self.right_marker is not None\
                and event.xdata is not None:
            if self.edit_mode:
                if self.mouse_on_left_marker:
                    self.left_marker.set_xdata([event.xdata, event.xdata])
                    self.settings.markers.left_value = event.xdata
                elif self.mouse_on_right_marker:
                    self.right_marker.set_xdata([event.xdata, event.xdata])
                    self.settings.markers.right_value = event.xdata
                self.canvas.draw()
            else:
                if self.left_marker.get_xdata()[0] - self.detect_x_range < event.xdata \
                        < self.left_marker.get_xdata()[0] + self.detect_x_range:
                    self.mouse_on_left_marker = True
                    self.mouse_on_right_marker = False
                else:
                    self.mouse_on_left_marker = False

                if self.right_marker.get_xdata()[0] - self.detect_x_range < event.xdata \
                        < self.right_marker.get_xdata()[0] + self.detect_x_range:
                    self.mouse_on_right_marker = True
                    self.mouse_on_left_marker = False
                else:
                    self.mouse_on_right_marker = False

    def add_line(self, x, y, color_options):
        line, = self.ax.plot(x, y, color_options, ms=5, mew=2)
        self.lines.append(line)

    def remove_lines(self):
        for line in self.lines:
            if line in self.ax.lines:
                self.ax.lines.remove(line)
                del line
        self.lines.clear()
        self.ax.relim()

    def set_title(self, title):
        plt.title(title)

    def show_ver_markers(self, x_left, x_right, ymin, ymax):
        self.detect_x_range = 0.005 * (x_right - x_left)
        self.left_marker = self.ax.axvline(x=x_left, ymin=ymin, ymax=ymax, color='r')
        self.right_marker = self.ax.axvline(x=x_right, ymin=ymin, ymax=ymax, color='r')
        self.canvas.draw()

    def hide_ver_markers(self):
        if self.left_marker is None and self.right_marker is None:
            return

        self.settings.markers.left_value = None
        self.settings.markers.right_value = None
        self.ax.lines.remove(self.left_marker)
        del self.left_marker
        self.left_marker = None
        self.ax.lines.remove(self.right_marker)
        del self.right_marker
        self.right_marker = None
        self.ax.relim()
        self.canvas.draw()

    def is_ver_markers_shown(self):
        if self.left_marker is None and self.right_marker is None:
            return False
        return True

    def get_markers_positions(self):
        if self.left_marker is None:
            return None, None
        else:
            return self.left_marker.get_xdata()[0], self.right_marker.get_xdata()[0]

    def autoscale(self, enable=True):
        self.ax.autoscale(enable)

    def set_x_lim(self, lim=(0, 1)):
        self.ax.set_xlim(lim)

    def set_y_lim(self, lim=(0, 1)):
        self.ax.set_ylim(lim)

    def init_animation(self):
        return self.lines[0]

    def show_animation(self, interval):
        self.cur_y_ind = 0
        self.anim = animation.FuncAnimation(self.figure, self.animate_call_back, init_func=self.init_animation, interval=interval)
        plt.draw()

    def stop_animation(self):
        self.anim.event_source.stop()

    def get_figure(self):
        return self.figure

    def get_canvas(self):
        return self.canvas
