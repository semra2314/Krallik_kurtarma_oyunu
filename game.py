import os
import threading
import time
import tkinter as tk
from tkinter import ttk

MUSIC_FILE = "bg_music.mp3"

try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

# try to import Pillow for broader image support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


def discover_assets():
    """Scan current directory for likely start/victory images and music/sfx."""
    files = os.listdir('.')
    imgs = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    mp3s = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.ogg', '.mpeg', '.mpg', '.m4a', '.aac'))]

    start_img = None
    victory_img = None
    music = None
    sfx = None

    # heuristics for images
    for name in imgs:
        ln = name.lower()
        if any(k in ln for k in ('start', 'giris', 'giriş', 'menu', 'cover')) and not start_img:
            start_img = name
        if any(k in ln for k in ('victory', 'kazanan', 'kazan', 'win', 'victor', 'zafer')) and not victory_img:
            victory_img = name
        if any(k in ln for k in ('vamp', 'vampir', 'vampire', 'saldir', 'saldırı', 'saldiri', 'attack')) and not sfx:
            # temporarily hold an attack image in sfx variable to reuse
            # we'll set VAMP_IMAGE below
            sfx = name

    # fallback: if only one image present, use it for both
    if not start_img and imgs:
        start_img = imgs[0]
    if not victory_img and len(imgs) >= 2:
        victory_img = imgs[1]
    elif not victory_img and imgs:
        victory_img = imgs[0]

    # music/sfx
    if MUSIC_FILE in mp3s:
        music = MUSIC_FILE
    elif mp3s:
        music = mp3s[0]

    # look for short sfx
    for m in mp3s:
        if any(k in m.lower() for k in ('sfx', 'effect', 'win', 'victory')):
            sfx = m
            break

    # determine vamp image (attack) if present
    vamp_img = None
    for name in imgs:
        ln = name.lower()
        if any(k in ln for k in ('vamp', 'vampir', 'vampire', 'saldir', 'saldırı', 'attack')):
            vamp_img = name
            break

    return start_img, victory_img, music, sfx, vamp_img


START_IMAGE, VICTORY_IMAGE, DETECTED_MUSIC, SFX_FILE, VAMP_IMAGE = discover_assets()
if DETECTED_MUSIC:
    MUSIC_FILE = DETECTED_MUSIC

print(f"Detected assets -> start: {START_IMAGE}, victory: {VICTORY_IMAGE}, music: {MUSIC_FILE}, sfx: {SFX_FILE}, vamp: {VAMP_IMAGE}")


def center_crop_and_resize(path, target_w=800, target_h=520):
    if PIL_AVAILABLE:
        img = Image.open(path)
        iw, ih = img.size
        target_ratio = target_w / target_h
        src_ratio = iw / ih
        if src_ratio > target_ratio:
            # source is wider -> crop left/right
            new_w = int(ih * target_ratio)
            left = (iw - new_w) // 2
            img = img.crop((left, 0, left + new_w, ih))
        else:
            # source taller -> crop top/bottom
            new_h = int(iw / target_ratio)
            top = (ih - new_h) // 2
            img = img.crop((0, top, iw, top + new_h))
        img = img.resize((target_w, target_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    else:
        # fallback: let tkinter handle resizing (may not crop)
        return tk.PhotoImage(file=path)


class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Krallık - KRALLAR UYUMAZ")
        # determine window size from images (will cap to screen)
        self.win_w, self.win_h = self.determine_window_size()
        self.geometry(f"{self.win_w}x{self.win_h}")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.container = tk.Frame(self, bg="#111011")
        self.container.pack(fill="both", expand=True)

        self.name = tk.StringVar()

        self.create_start_screen()
        self.create_main_screen()
        self.create_result_screen()
        self.create_intro_screen()
        # start intro shortly after initialization so texts appear
        self.after(100, self.start_intro)

    def create_start_screen(self):
        self.start_frame = tk.Frame(self.container, bg="#0b2b3a")
        # do not place now; intro will show first

        # if a start image is available, show it as background
        if START_IMAGE:
            try:
                self.start_bg_image = center_crop_and_resize(START_IMAGE, self.win_w, self.win_h)
                bg = tk.Label(self.start_frame, image=self.start_bg_image)
                bg.place(relwidth=1, relheight=1)
            except Exception:
                title = tk.Label(self.start_frame, text="Krallığın Çağrısı", fg="#ffd700",
                                 bg="#0b2b3a", font=("Segoe UI", 32, "bold"))
                title.pack(pady=(40, 10))
        else:
            title = tk.Label(self.start_frame, text="Krallığın Çağrısı", fg="#ffd700",
                             bg="#0b2b3a", font=("Segoe UI", 32, "bold"))
            title.pack(pady=(40, 10))

        subtitle = tk.Label(self.start_frame, text="KRALLAR UYUMAZ - Macerana hoş geldin",
                            fg="#e0f7ff", bg="#0b2b3a", font=("Segoe UI", 12))
        subtitle.pack(pady=(0, 20))

        entry_label = tk.Label(self.start_frame, text="Adın:", fg="#dff6ff", bg="#0b2b3a")
        entry_label.pack()
        self.name_entry = ttk.Entry(self.start_frame, textvariable=self.name, width=30)
        self.name_entry.pack(pady=6)

        start_btn = ttk.Button(self.start_frame, text="👑 Başla", command=self.show_main, style='Royal.TButton')
        start_btn.pack(pady=16)

    def create_main_screen(self):
        self.main_frame = tk.Frame(self.container, bg="#081c24")

        # story label will be updated with the player's name when showing main
        self.story_label = tk.Label(self.main_frame, text="", fg="#cfe8ff", bg="#081c24",
                        font=("Segoe UI", 14), wraplength=700, justify="center")
        self.story_label.pack(pady=(30, 20))

        choices_frame = tk.Frame(self.main_frame, bg="#081c24")
        choices_frame.pack(pady=10)

        b1 = ttk.Button(choices_frame, text="1. Birilerini uyandır.", command=lambda: self.on_choice(1))
        b2 = ttk.Button(choices_frame, text="2. Krallığın kapılarını aç.", command=lambda: self.on_choice(2))
        b3 = ttk.Button(choices_frame, text="3. Krallığı boşverdin ve yollara düştün.", command=lambda: self.on_choice(3))

        b1.grid(row=0, column=0, padx=12, pady=8, ipadx=10, ipady=8)
        b2.grid(row=0, column=1, padx=12, pady=8, ipadx=10, ipady=8)
        b3.grid(row=0, column=2, padx=12, pady=8, ipadx=10, ipady=8)

        b1.grid(row=0, column=0, padx=12, pady=8, ipadx=10, ipady=8)
        b2.grid(row=0, column=1, padx=12, pady=8, ipadx=10, ipady=8)
        b3.grid(row=0, column=2, padx=12, pady=8, ipadx=10, ipady=8)

        back_btn = ttk.Button(self.main_frame, text="Geri", command=self.show_start, style='Royal.TButton')
        back_btn.pack(side="bottom", pady=14)

    def create_result_screen(self):
        self.result_frame = tk.Frame(self.container, bg="#000000")

        self.result_canvas = tk.Canvas(self.result_frame, bg="#000000", highlightthickness=0)
        self.result_canvas.pack(fill="both", expand=True)

        self.result_text = tk.Label(self.result_canvas, text="", fg="#fff", bg="#000000",
                                    font=("Segoe UI", 18), wraplength=760, justify="center")

        self.krallar_label = tk.Label(self.result_canvas, text="KRALLAR UYUMAZ", fg="#ffd700",
                                      bg="#000000", font=("Segoe UI", 36, "bold"))

        # victory image placeholder
        self.victory_bg_image = None
        if VICTORY_IMAGE:
            try:
                self.victory_bg_image = center_crop_and_resize(VICTORY_IMAGE, 800, 520)
            except Exception:
                self.victory_bg_image = None
        # load vamp image
        self.vamp_bg_image = None
        if VAMP_IMAGE:
            try:
                self.vamp_bg_image = center_crop_and_resize(VAMP_IMAGE, 800, 520)
            except Exception:
                self.vamp_bg_image = None

        self.retry_btn = ttk.Button(self.result_frame, text="Tekrar Başla", command=self.show_start, style='Royal.TButton')
        self.quit_btn = ttk.Button(self.result_frame, text="Çıkış", command=self.quit, style='Royal.TButton')

    def show_start(self):
        self.main_frame.place_forget()
        self.result_frame.place_forget()
        self.start_frame.place(relwidth=1, relheight=1)

    def show_main(self):
        name = self.name.get().strip() or "Gezgin"
        self.start_frame.place_forget()
        self.result_frame.place_forget()
        self.main_frame.place(relwidth=1, relheight=1)
        # update story and prompt to match console dialog
        story_text = (
            "Hoş geldin, cesur kahraman!\n"
            "Bir zamanlar bir krallık varmış, bu krallıkta herkes uyuyormuş ama bir kişi hariç.\n\n"
            f"{name}, krallığı kurtarmak için ne yapmalıyız?"
        )
        self.story_label.config(text=story_text)

    def create_intro_screen(self):
        # full-screen black intro frame with fading texts
        self.intro_frame = tk.Frame(self.container, bg="#000000")
        self.intro_label = tk.Label(self.intro_frame, text="", fg="#000000", bg="#000000",
                                    font=("Segoe UI", 26), wraplength=self.win_w - 80, justify="center")
        self.intro_label.place(relx=0.5, rely=0.45, anchor="center")

        # prepare royal button style
        try:
            self.style.configure('Royal.TButton', font=("Segoe UI", 12, 'bold'), foreground="#fff",
                                 background="#b8860b", padding=10, relief="raised")
            self.style.map('Royal.TButton', background=[('active', '#ffd700'), ('!disabled', '#b8860b')],
                           foreground=[('active', '#000000'), ('!disabled', '#ffffff')])
        except Exception:
            pass

    def start_intro(self):
        # sequence of texts
        seq = [
            ("Bir zamanlar yaşlı bir cadı varmış", 1600),
            ("Çalışkan insanlardan nefret edermiş", 1600),
            ("Kıskançlığına yenik düşmüş ve tüm ülkeyi uyku büyüsü ile uyutmuş", 2200)
        ]

        self.intro_frame.place(relwidth=1, relheight=1)

        def fade_text(text, duration=1200, hold=600, on_done=None):
            steps = 20
            step_time = max(10, duration // steps)
            # color interpolation from black to pale gold
            start_rgb = (0, 0, 0)
            end_rgb = (248, 240, 200)  # pale gold-ish

            def set_step(i):
                t = i / steps
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.intro_label.config(text=text, fg=color)

            def fade_in(i=0):
                if i <= steps:
                    set_step(i)
                    self.after(step_time, lambda: fade_in(i + 1))
                else:
                    self.after(hold, lambda: fade_out(steps))

            def fade_out(i=steps):
                if i >= 0:
                    set_step(i)
                    self.after(step_time, lambda: fade_out(i - 1))
                else:
                    if on_done:
                        on_done()

            fade_in(0)

        # sequential runner
        def run_seq(i=0):
            if i >= len(seq):
                # intro finished — hide intro and show start screen
                self.intro_frame.place_forget()
                self.start_frame.place(relwidth=1, relheight=1)
                # focus name entry
                try:
                    self.name_entry.focus()
                except Exception:
                    pass
                return

            text, hold = seq[i]
            fade_text(text, duration=1400, hold=hold, on_done=lambda: self.after(600, lambda: run_seq(i + 1)))

        # begin
        self.after(200, lambda: run_seq(0))

    def show_result(self, text, success=False, fail=False):
        self.main_frame.place_forget()
        self.start_frame.place_forget()
        self.result_frame.place(relwidth=1, relheight=1)

        if fail:
            self.result_canvas.configure(bg="#220000")
            self.result_text.configure(bg="#220000", fg="#ffcccc")
        elif success:
            self.result_canvas.configure(bg="#001a00")
            self.result_text.configure(bg="#001a00", fg="#cfffcc")
        else:
            self.result_canvas.configure(bg="#000000")
            self.result_text.configure(bg="#000000", fg="#ffffff")


        # draw background image if available (for victory)
        self.result_canvas.delete("all")
        if success and self.victory_bg_image:
            # place image and dim it slightly by drawing a translucent rectangle
            self.result_canvas.create_image(0, 0, anchor="nw", image=self.victory_bg_image)
            self.result_canvas.create_rectangle(0, 0, self.win_w, self.win_h, fill="#000000", stipple="gray50")
        elif fail and getattr(self, 'vamp_bg_image', None):
            # show vamp attack background for failure
            self.result_canvas.create_image(0, 0, anchor="nw", image=self.vamp_bg_image)
            self.result_canvas.create_rectangle(0, 0, self.win_w, self.win_h, fill="#000000", stipple="gray25")
        self.result_text.config(text=text)
        center_x = self.win_w // 2
        center_y = int(self.win_h * 0.35)
        self.result_canvas.create_window(center_x, center_y, window=self.result_text)

        if success:
            # show krallar label above everything
            self.krallar_label.place_forget()
            self.krallar_label.lift()
            self.animate_krallar()

        # buttons
        self.retry_btn.place(relx=0.35, rely=0.85, anchor="center")
        self.quit_btn.place(relx=0.65, rely=0.85, anchor="center")

    def animate_krallar(self):
        # place label starting below the canvas and move up
        self.krallar_label.place_forget()
        x = self.win_w // 2
        y = self.win_h + 40

        def step():
            nonlocal y
            y -= max(4, self.win_h // 120)
            target_y = int(self.win_h * 0.25)
            if y <= target_y:
                y = target_y
            self.krallar_label.place(x=x, y=y, anchor="center")
            if y > target_y:
                self.after(30, step)

        step()

    def on_choice(self, n):
        name = self.name.get().strip() or "Gezgin"
        if n == 1:
            text = "Sen ve ekibin krallığı kurtardı ve sen kral oldun!"
            # show the result and animate the rising text
            self.show_result(text, success=True)
        elif n == 2:
            text = "Gece vampirler saldırdı ve herkes öldü.\nGörev başarısız!"
            self.show_result(text, fail=True)
        elif n == 3:
            text = "Yolda büyücü cadıyı buldun ve krallığı kurtardın"
            self.show_result(text, success=True)

    def determine_window_size(self):
        # inspect available images and return a window size (width, height)
        candidates = []
        for fname in (START_IMAGE, VICTORY_IMAGE, VAMP_IMAGE):
            if not fname:
                continue
            try:
                if PIL_AVAILABLE:
                    with Image.open(fname) as im:
                        candidates.append(im.size)
                else:
                    pi = tk.PhotoImage(file=fname)
                    candidates.append((pi.width(), pi.height()))
            except Exception:
                continue

        if candidates:
            widths = [w for w, h in candidates]
            heights = [h for w, h in candidates]
            w = max(widths)
            h = max(heights)
        else:
            w, h = 800, 520

        # cap to screen with margin
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            w = min(w, screen_w - 100)
            h = min(h, screen_h - 100)
        except Exception:
            pass

        # ensure minimum size
        w = max(640, w)
        h = max(360, h)
        return w, h


def start_music_if_available():
    if not PYGAME_AVAILABLE:
        print("Müzik için pygame yüklü değil. Yüklemek için: pip install pygame")
        return
    if not os.path.exists(MUSIC_FILE):
        print(f"Müzik dosyası bulunamadı: {MUSIC_FILE} — isterseniz bu dosyayı aynı klasöre koyun.")
        return
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Müzik çalınamadı:", e)


if __name__ == "__main__":
    # start music in background thread so GUI remains responsive
    t = threading.Thread(target=start_music_if_available, daemon=True)
    t.start()

    app = GameApp()
    app.mainloop()