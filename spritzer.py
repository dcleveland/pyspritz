"""Speed-reading spritz application."""
# pylint: disable=unused-argument,unused-import,R0902,R0915
import copy
from optparse import OptionParser
import os
import pickle
from pickle import UnpicklingError
import sys

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    PY3 = False
except ImportError:
    import tkinter.ttk as ttk
    PY3 = True

import spritzer_support

# PATHS
BASE_PATH = '/home/dcleveland/code/pyspritz'
DATA_DIR = f'{BASE_PATH}/data'
IMAGES_DIR = f'{BASE_PATH}/images'
# Top/bottom borders.
TOP_BORDER_IMG = f'{IMAGES_DIR}/top_border.png'
BOTTOM_BORDER_IMG = f'{IMAGES_DIR}/bottom_border.png'
TMP_INPUT = '/tmp/spritz.txt'
BOOKMARKS_FILE = f'{BASE_PATH}/bookmarks.pkl'
#                                         ___   ___
#     //   ) )  //   / / /__  ___/ /__  ___/ / /    /|    / / //   ) )  //   ) )
#    ((        //____      / /       / /    / /    //|   / / //        ((
#      \\     / ____      / /       / /    / /    // |  / / //  ____     \\
#        ) ) //          / /       / /    / /    //  | / / //    / /       ) )
# ((___ / / //____/ /   / /       / /  __/ /___ //   |/ / ((____/ / ((___ / /
AUTOPLAY = True
# Default words per minute setting.
DEFAULT_WPM = 350
# Mulitplier for display ms when a 'pause' is added.
SENTENCE_PAUSE_MULT = 2.25
# Word length at which to add a pause.
ADD_DELAY_LENGTH = 10
# Punctuation characters after which to add a pause.
ADD_PAUSE_PUNCTUATIONS = ['.', '!', '?', ')', '"']
# Characters that should never be emphasis characters.
DO_NOT_EMPHASIZE_CHARS = ['-', '—', '/', '(', ')', ':', ]

TROUGH_COLOR = '#434343'
BAR_COLOR = '#f46464'


def start_gui(words, opt_start_idx=0, input_file=TMP_INPUT,
              bookmarks_path=BOOKMARKS_FILE):
    """Starting point when module is the main routine."""
    global val, w, root
    root = tk.Tk()
    root.wait_visibility()
    root.wm_attributes('-alpha', '0.85')
    # root.attributes('-fullscreen', True)
    width, height = root.winfo_screenwidth() / 3, root.winfo_screenheight()
    root.geometry("%dx%d+%d+%d" % (width, height, width, height))
    spritzer_support.set_Tk_var()
    top = SpritzApp(words_list=words, top=root, start_idx=opt_start_idx,
                    input_file=input_file)
    spritzer_support.init(root, top)
    root.mainloop()

w = None
def create_spritzapp(rt, *args, **kwargs):
    """Starting point when module is imported by another module.
       Correct form of call: 'create_spritzapp(root, *args, **kwargs)' ."""
    global w, w_win, root
    root = rt
    root.wait_visibility()
    root.wm_attributes('-alpha', '0.85')
    # root.attributes('-fullscreen', True)
    width, height = root.winfo_screenwidth() / 3, root.winfo_screenheight()
    root.geometry("%dx%d+%d+%d" % (width, height, width, height))
    w = tk.Toplevel(root)
    spritzer_support.set_Tk_var()
    top = SpritzApp(w)
    spritzer_support.init(w, top, *args, **kwargs)
    return (w, top)

def destroy_spritzapp(event):
    """Quit running application."""
    global w
    w.destroy()
    w = None


class SpritzApp():
    """Top-level application class."""
    def __init__(self, words_list, top=None, start_idx=0,
                 bookmarks_path=BOOKMARKS_FILE, input_file=TMP_INPUT):
        """This class configures and populates the toplevel window.
           top is the toplevel containing window."""
        self._words = words_list
        self.total_words = len(self._words)

        self._word_gen = iter(words_list)

        self.progress_val = tk.StringVar()

        self.bookmarks_path = bookmarks_path
        self.input_file = input_file
        
        self.current_idx = tk.IntVar()
        self.current_idx.set(start_idx)
        self.playing = False

        self.style = ttk.Style()
        self.style.configure(
                "bar.Horizontal.TProgressbar", troughcolor=TROUGH_COLOR,
                        bordercolor=BAR_COLOR, background=BAR_COLOR,
                lightcolor=BAR_COLOR, darkcolor=BAR_COLOR, relief="flat",
                        borderwidth="0")
        # top.wait_visibility()
        width, height = top.winfo_screenwidth() / 3, top.winfo_screenheight()

        top.geometry("%dx%d+%d+%d" % (width, height, width, height))

        top.resizable(1,  1)
        top.title("Spritzer")
        top.configure(background="#434343")
        top.configure(cursor="arrow")
        top.configure(highlightbackground="#757575")
        
        self.top = top
        # Keybindings.
        top.bind('<space>', self.play_pause)
        top.bind('<Right>', self.next_word)
        top.bind('<Left>', self.prev_word)
        top.bind('<Up>', self.increase_wpm)
        top.bind('<Down>', self.decrease_wpm)
        top.bind('<Control-q>', self.destroy_spritzapp)
        top.bind('<Escape>', self.destroy_spritzapp)
        
        # Vars for word segments.
        self.left_text_var = tk.StringVar()
        self.mid_text_var = tk.StringVar()
        self.right_text_var = tk.StringVar()

        # Container frame for text display.
        self.text_frame = tk.Frame(top)
        self.text_frame.place(
                relx=.1875, rely=0.4, relheight=.1296, relwidth=0.625)
        self.text_frame.configure(relief='groove')
        self.text_frame.configure(borderwidth="0")
        self.text_frame.configure(background="#434343")
        self.text_frame.configure(highlightbackground="#434343")


        # Container for left word segment.
        self.left_wd_frame = tk.Frame(self.text_frame)
        self.left_wd_frame.place(
                relx=0.0, rely=0.0, relheight=1.0, relwidth=0.488888)
        self.left_wd_frame.configure(relief="groove")
        self.left_wd_frame.configure(background="#434343")

        # Label for left word segment.
        self.left_wd_label = tk.Label(
                self.left_wd_frame, textvariable=self.left_text_var)
        self.left_wd_label.place(relx=0.0, rely=0.0, relheight=1, relwidth=1)
        self.left_wd_label.configure(activebackground="#434343")
        self.left_wd_label.configure(activeforeground="black")
        self.left_wd_label.configure(activeforeground="#434343")
        self.left_wd_label.configure(anchor='e')
        self.left_wd_label.configure(background="#434343")
        self.left_wd_label.configure(borderwidth="2")
        self.left_wd_label.configure(font="-family {Courier 10 Pitch} -size 24")
        self.left_wd_label.configure(justify='right')
        self.left_wd_label.configure(foreground="black")

        # Container for right word segment.
        self.right_wd_frame = tk.Frame(self.text_frame)
        self.right_wd_frame.place(
                relx=.511111, rely=0.0, relheight=1, relwidth=0.488888)
        self.right_wd_frame.configure(relief="groove")
        self.right_wd_frame.configure(background="#434343")

        # Label for right word segment.
        self.right_wd_label = tk.Label(
                self.right_wd_frame, textvariable=self.right_text_var)
        self.right_wd_label.place(relx=0.0, rely=0.0, relheight=1, relwidth=1)
        self.right_wd_label.configure(activebackground="#434343")
        self.right_wd_label.configure(activeforeground="black")
        self.right_wd_label.configure(anchor='w')
        self.right_wd_label.configure(background="#434343")
        self.right_wd_label.configure(borderwidth="0")
        self.right_wd_label.configure(
                font="-family {Courier 10 Pitch} -size 24")
        self.right_wd_label.configure(foreground="black")

        # Container for central character.
        self.central_frame = tk.Frame(self.text_frame)
        self.central_frame.place(
                relx=.488888, rely=0.0, relheight=1.0, width=26)
        self.central_frame.configure(relief="groove")

        # Label for central character.
        self.central_label = tk.Label(
                self.central_frame, textvariable=self.mid_text_var)
        self.central_label.place(relx=0.0, rely=0.0, relheight=1, relwidth=1)
        self.central_label.configure(background="#434343")
        self.central_label.configure(borderwidth="0")
        self.central_label.configure(font="-family {Courier 10 Pitch} -size 24")
        self.central_label.configure(foreground="#f46464")

        top_img = tk.PhotoImage(file=TOP_BORDER_IMG)
        # Label for top "border" image.
        self.top_border_label = tk.Label(self.text_frame, image=top_img)
        self.top_border_label.place(
                relx=0.0, rely=0.25, height=10, relwidth=1)
        self.top_border_label.configure(activebackground="#434343")
        self.top_border_label.configure(activeforeground="black")
        self.top_border_label.configure(anchor='center')
        self.top_border_label.configure(background="#434343")
        self.top_border_label.configure(borderwidth="0")
        self.top_border_label.configure(
                font="-family {Courier 10 Pitch} -size 24")
        self.top_border_label.configure(foreground="black")
        self.top_border_label.image = top_img

        bottom_img = tk.PhotoImage(file=BOTTOM_BORDER_IMG)
        self.bottom_border_label = tk.Label(self.text_frame, image=bottom_img)
        self.bottom_border_label.place(
                relx=0, rely=0.63, height=10, relwidth=1)
        self.bottom_border_label.configure(activebackground="#434343")
        self.bottom_border_label.configure(activeforeground="black")
        self.bottom_border_label.configure(anchor='center')
        self.bottom_border_label.configure(background="#434343")
        self.bottom_border_label.configure(borderwidth="0")
        self.bottom_border_label.configure(
                font="-family {Courier 10 Pitch} -size 24")
        self.bottom_border_label.configure(foreground="black")
        self.bottom_border_label.image = bottom_img

        # Container for controls.
        self.controls_frame = tk.Frame(top)
        self.controls_frame.place(
                relx=.1875, rely=0.75, relheight=.25, relwidth=.625)
        self.controls_frame.configure(relief="groove")
        self.controls_frame.configure(background="#434343")
        # Previous word button.
        self.prev_wd_btn = tk.Button(
                self.controls_frame, command=self.prev_word)
        self.prev_wd_btn.place(relx=0.363, rely=0.4, height=25, width=60)
        self.prev_wd_btn.configure(background="#434343")
        self.prev_wd_btn.configure(borderwidth="0")
        self.prev_wd_btn.configure(text="""<""")
        # Play/Pause button.
        self.play_pause_btn = tk.Button(
                self.controls_frame, command=self.play_pause)
        self.play_pause_btn.place(relx=0.467, rely=0.4, height=25, width=60)
        self.play_pause_btn.configure(background="#434343")
        self.play_pause_btn.configure(borderwidth="0")
        self.play_pause_btn.configure(text="""Play""")
        self.play_pause_btn.configure(textvariable=spritzer_support.is_playing)
        # Next word button.
        self.next_wd_btn = tk.Button(
                self.controls_frame, command=self.next_word)
        self.next_wd_btn.place(relx=0.568, rely=0.4, height=25, width=60)
        self.next_wd_btn.configure(background="#434343")
        self.next_wd_btn.configure(borderwidth="0")
        self.next_wd_btn.configure(state='disabled')
        self.next_wd_btn.configure(text=""">""")
        # Words-per-minute slider.
        self.wpm_slider = tk.Scale(self.controls_frame, from_=150.0, to=500.0)
        self.wpm_slider.place(
                relx=0.36111, rely=0.15, height=45, width=310)
        self.wpm_slider.configure(activebackground="#7f7f7f")
        self.wpm_slider.configure(background="#434343")
        self.wpm_slider.configure(highlightbackground="#969696")
        self.wpm_slider.configure(length="325")
        self.wpm_slider.configure(orient="horizontal")
        self.wpm_slider.configure(troughcolor="#232323")
        self.wpm_slider.configure(variable=spritzer_support.wpm_value)
        self.wpm_slider.set(DEFAULT_WPM)

        self.idx_frame = tk.Frame(self.controls_frame)
        self.idx_frame.place(relx=0.1875, rely=0.90, height=24, width=900)
        self.idx_frame.configure(background='#434343')

        self.idx_label = tk.Label(
                self.idx_frame, textvariable=self.progress_val)
        self.idx_label.place(relx=0.0, rely=0.0, relheight=1, relwidth=1)
        self.idx_label.configure(activebackground="#434343")
        self.idx_label.configure(activeforeground="black")
        self.idx_label.configure(anchor='e')
        self.idx_label.configure(background="#434343")
        self.idx_label.configure(borderwidth="0")
        self.idx_label.configure(
                font="-family {Courier 10 Pitch} -size 12")
        self.idx_label.configure(foreground="black")

        self.progress_bar = ttk.Progressbar(
                self.top, orient=tk.HORIZONTAL, length=float(self.total_words),
                        mode='determinate', style="bar.Horizontal.TProgressbar")
        self.progress_bar.config(maximum=float(self.total_words))
        self.progress_bar.place(relx=0.0, rely=0.0, height=5, relwidth=1)

        if AUTOPLAY:
            self.change_word(jump_idx=self.current_idx.get())
            self.top.after(1000, self.play)

    def destroy_spritzapp(self, event=None):
        """Quit application."""
        print(f'Last word index was {self.current_idx.get()}')
        bookmarks = load_bookmarks(self.bookmarks_path)
        bookmarks[self.input_file] = self.current_idx.get()
        print(f'{bookmarks=}')
        save_bookmarks(bookmarks)
        self.top.destroy()
        self.top = None
    
    @classmethod
    def get_word_text_elements(cls, word: str):
        """Separate word into three parts with middle part being 1 character."""
        if not word:
            return ['', '', '']
        if len(word) == 1:
            return ['', word, '']
        mid_char = cls.get_central_char_idx(word)
        try:
            if word[mid_char] in DO_NOT_EMPHASIZE_CHARS:
                mid_char += 1
            first = word[0:mid_char]
            central = word[mid_char]
            end = word[mid_char+1:]
            return [first, central, end]
        except:
            print("ERROR Parsing word %s" % word)
            print(f'{mid_char=}')
    @classmethod
    def wpm_to_spw(cls, wpm: int=200):
        """Converts words-per-minute to seconds."""
        return 60 / wpm

    @classmethod
    def wpm_to_mspw(cls, wpm: int):
        """Converts words-per-minute to miliseconds."""
        return int(cls.wpm_to_spw(wpm) * 1000)

    @classmethod
    def get_central_char_idx(cls, word: str=''):
        """Returns the index of the central character in a word."""
        return int(len(word) / 2) - 1

    def play_pause(self, event=None):
        """Toggle playback."""
        if not self.playing:
            self.play()
            return
        self.pause()

    def play(self):
        """Start playback."""
        self.playing = True
        spritzer_support.is_playing.set("Pause")
        self.next_wd_btn.configure(state='disabled')
        self.wpm_slider.configure(state='disabled')
        self.change_word()

    def pause(self):
        """Pause playback."""
        self.playing = False
        spritzer_support.is_playing.set("Play")
        self.next_wd_btn.configure(state='normal')
        self.wpm_slider.configure(state='normal')

    def prev_word(self, event=None):
        """Skip to the previous word."""
        if self.playing:
            self.pause()
        jump_idx = self.current_idx.get() - 1
        self.change_word(jump_idx=jump_idx)

    def next_word(self, event=None):
        """Skip to the next word."""
        if self.playing:
            return
        jump_idx = self.current_idx.get() + 1
        self.change_word(jump_idx=jump_idx)

    def increase_wpm(self, event=None, increment=5):
        """Increase words-per-minute by increment."""
        value = self.wpm_slider.get()
        self.wpm_slider.set(value + increment)

    def decrease_wpm(self, event=None, increment=5):
        """Reduce words-per-minute by increment."""
        value = self.wpm_slider.get()
        self.wpm_slider.set(value - increment)

    def change_word(self, jump_idx=None):
        """Display the next word from the generator or jump to jump_idx."""
        if jump_idx:
            tmp_words = copy.copy(self._words)[max(jump_idx-1, 0):]
            self._word_gen = iter(tmp_words)
            current_idx_val = jump_idx
        else:
            current_idx_val = self.current_idx.get() + 1
        try:
            new_word = self._word_gen.__next__()
        except StopIteration:
            self._word_gen = iter(self._words)
            current_idx_val = 0
            self.pause()
            return
        display_ms = int(self.wpm_to_mspw(self.wpm_slider.get()))
        if new_word and (new_word[-1] in ADD_PAUSE_PUNCTUATIONS
                or len(new_word) >= ADD_DELAY_LENGTH):
            display_ms = int(
                    self.wpm_to_mspw(
                            self.wpm_slider.get() / SENTENCE_PAUSE_MULT))

        left_text_val, mid_text_val, right_text_val = \
                self.get_word_text_elements(new_word)
        self.left_text_var.set(left_text_val)
        self.mid_text_var.set(mid_text_val)
        self.right_text_var.set(right_text_val)
        prog_pct = round(
                (float(current_idx_val) / float(self.total_words)) * 100, 2)
        
        self.current_idx.set(current_idx_val)
        prog_str = f'{self.current_idx.get()}/{self.total_words} ({prog_pct}%)'
        self.progress_val.set(prog_str)
        self.progress_bar.step()
        if self.playing:
            self.top.after(display_ms, self.change_word)


def parse_options():
    parser = OptionParser()
    parser.add_option('-i', '--input-file', action='store',
                      help='Path to input text file.', dest='input_file',
                      default='/tmp/spritz.txt')
    parser.add_option('-s', '--start-index', action='store',
                      help=('Starting word index. Over-rides any existing '
                            'bookmark.'), dest='start_idx',
                      default=0)
    parser.add_option('-b', '--bookmarks-file', action='store',
                      help=('Path to pickle file containing filename, word '
                            'index dictionary.'), dest='bookmarks_path',
                      default=BOOKMARKS_FILE)
    
    options, args = parser.parse_args()
    return options


# Load words from /tmp/spritz.txt.
def load_file_and_clean_words(file_path='/tmp/spritz.txt'):
    words = open(file_path, 'r').read().replace(
            '-', '- ').replace('—', '- ').split(' ')
    if words[0].startswith('"'):
        words = [words[0].replace('"', '')] + words[1:]
    if words[-1].endswith('"'):
        words = words[:-1] + [words[-1].replace('"', '')]
    words = [w for w in words if w]
    return words

def load_bookmarks(opt_path=BOOKMARKS_FILE):
    """Load pickle file containing dictionary of filename: word_index."""
    if not os.path.isfile(opt_path):
        raise FileNotFoundError(f'Bookmarks file {opt_path} does not exist!')
    try:
        bookmarks = pickle.load(open(opt_path, 'rb'))
        return bookmarks
    except UnpicklingError:
        return {}

def save_bookmarks(bookmarks: dict, opt_path=BOOKMARKS_FILE):
    # Don't save bookmark value for /tmp/spritz.txt.
    if bookmarks.get(TMP_INPUT):
        bookmarks.pop(TMP_INPUT)
    pickle.dump(bookmarks, open(opt_path, 'wb'))

if __name__ == '__main__':
    opts = parse_options()
    file_words_list = load_file_and_clean_words(opts.input_file)
    bookmarks = load_bookmarks(opts.bookmarks_path)
    # CL arg over-rides bookmark.
    start_idx = opts.start_idx or bookmarks.get(opts.input_file) or 0
    start_gui(words=file_words_list, opt_start_idx=start_idx,
              input_file=opts.input_file, bookmarks_path=BOOKMARKS_FILE)
