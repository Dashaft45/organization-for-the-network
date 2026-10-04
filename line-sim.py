import tkinter as tk
from tkinter import ttk

# ============================================================
# Физические константы
# ============================================================
CELERITY = 2.8e8  # м/с — скорость сигнала в кабеле

# ============================================================
# Геометрия отрисовки (в пикселях)
# ============================================================
WINDOW_W = 950
WINDOW_H = 300
LINE_X = 130
LINE_Y = 110
LINE_W = 660
LINE_H = 20
SENDER_X = 40
RECEIVER_X = 820

# Масштаб времени: сколько миллисекунд реального времени
# тратится на полную симуляцию (в модельных секундах).
# Если total_time маленький (0.08 мс) — растянем.
ANIMATION_DURATION_MS = 4000


class LineSimApp:
    def __init__(self, root):
        self.root = root
        root.title("Симулятор передачи пакета по линии")
        root.configure(bg="#f5f5f5")

        # ---- Состояние симуляции ----
        self.anim_id = None
        self.sim_start_ms = 0
        self.current_time = 0.0
        self.total_time = 0.0
        self.emission_time = 0.0
        self.propagation_time = 0.0
        self.line_length_m = 1_000_000  # текущая длина линии

        # ---- Верхняя панель управления ----
        self._build_controls()

        # ---- Холст ----
        self.canvas = tk.Canvas(
            root, width=WINDOW_W, height=WINDOW_H,
            bg="white", highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=(0, 10))

        # ---- Информационная строка ----
        self.info_var = tk.StringVar(value="Нажмите «Старт», чтобы запустить симуляцию.")
        info_label = tk.Label(
            root, textvariable=self.info_var,
            bg="#f5f5f5", fg="#333",
            font=("Arial", 11), anchor="w", justify="left"
        )
        info_label.pack(fill="x", padx=12, pady=(0, 10))

        # ---- Первичная инициализация параметров ----
        self._read_params()
        self._draw_base()

    # ------------------------------------------------------------
    # Построение панели управления
    # ------------------------------------------------------------
    def _build_controls(self):
        frame = tk.Frame(self.root, bg="#f5f5f5")
        frame.pack(fill="x", padx=12, pady=10)

        tk.Label(frame, text="Длина:", bg="#f5f5f5",
                 font=("Arial", 11, "bold")).grid(row=0, column=0, padx=(0, 4))

        self.length_var = tk.StringVar(value="1000 км")
        length_cb = ttk.Combobox(
            frame, textvariable=self.length_var,
            values=["10 км", "100 км", "1000 км"],
            state="readonly", width=10
        )
        length_cb.grid(row=0, column=1, padx=(0, 20))
        length_cb.bind("<<ComboboxSelected>>", lambda e: self._on_param_change())

        tk.Label(frame, text="Скорость:", bg="#f5f5f5",
                 font=("Arial", 11, "bold")).grid(row=0, column=2, padx=(0, 4))

        self.rate_var = tk.StringVar(value="100 Mbps")
        rate_cb = ttk.Combobox(
            frame, textvariable=self.rate_var,
            values=["512 kbps", "1 Mbps", "10 Mbps", "100 Mbps"],
            state="readonly", width=12
        )
        rate_cb.grid(row=0, column=3, padx=(0, 20))
        rate_cb.bind("<<ComboboxSelected>>", lambda e: self._on_param_change())

        tk.Label(frame, text="Размер пакета:", bg="#f5f5f5",
                 font=("Arial", 11, "bold")).grid(row=0, column=4, padx=(0, 4))

        self.size_var = tk.StringVar(value="1000 байт")
        size_cb = ttk.Combobox(
            frame, textvariable=self.size_var,
            values=["100 байт", "500 байт", "1000 байт"],
            state="readonly", width=12
        )
        size_cb.grid(row=0, column=5, padx=(0, 20))
        size_cb.bind("<<ComboboxSelected>>", lambda e: self._on_param_change())

        self.start_btn = tk.Button(
            frame, text="Старт", command=self.start_sim,
            bg="#2b6cb0", fg="white", font=("Arial", 11, "bold"),
            relief="flat", padx=16, pady=4, cursor="hand2"
        )
        self.start_btn.grid(row=0, column=6, padx=(0, 8))

        self.reset_btn = tk.Button(
            frame, text="Сброс", command=self.reset_sim,
            bg="#888", fg="white", font=("Arial", 11, "bold"),
            relief="flat", padx=16, pady=4, cursor="hand2"
        )
        self.reset_btn.grid(row=0, column=7)

    # ------------------------------------------------------------
    # Чтение параметров из интерфейса
    # ------------------------------------------------------------
    def _read_params(self):
        length_map = {"10 км": 10_000, "100 км": 100_000, "1000 км": 1_000_000}
        rate_map = {
            "512 kbps": 512_000,
            "1 Mbps": 1_000_000,
            "10 Mbps": 10_000_000,
            "100 Mbps": 100_000_000,
        }
        size_map = {"100 байт": 800, "500 байт": 4000, "1000 байт": 8000}

        L = length_map[self.length_var.get()]  # метры
        R = rate_map[self.rate_var.get()]      # бит/сек
        S = size_map[self.size_var.get()]      # биты

        self.line_length_m = L
        self.emission_time = S / R
        self.propagation_time = L / CELERITY
        self.total_time = self.emission_time + self.propagation_time

    def _on_param_change(self):
        self._read_params()
        if self.anim_id is None:
            self._draw_base()

    # ------------------------------------------------------------
    # Форматирование времени
    # ------------------------------------------------------------
    @staticmethod
    def _format_ms(seconds):
        return f"{seconds * 1000:.4f} мс"

    # ------------------------------------------------------------
    # Отрисовка статической сцены
    # ------------------------------------------------------------
    def _draw_base(self):
        c = self.canvas
        c.delete("all")

        # Линия
        c.create_rectangle(LINE_X, LINE_Y, LINE_X + LINE_W, LINE_Y + LINE_H,
                           fill="#eee", outline="#888")

        # Отправитель
        c.create_rectangle(SENDER_X, LINE_Y - 10,
                           SENDER_X + 60, LINE_Y + 30,
                           fill="#4a90e2", outline="#2b6cb0")
        c.create_text(SENDER_X + 30, LINE_Y + 50,
                      text="Sender", font=("Arial", 11))

        # Получатель
        c.create_rectangle(RECEIVER_X, LINE_Y - 10,
                           RECEIVER_X + 60, LINE_Y + 30,
                           fill="#4a90e2", outline="#2b6cb0")
        c.create_text(RECEIVER_X + 30, LINE_Y + 50,
                      text="Receiver", font=("Arial", 11))

        # Заголовок с временем
        c.create_text(30, 30, anchor="w",
                      text=f"Время: {self._format_ms(self.current_time)}",
                      font=("Arial", 13, "bold"), fill="#222")

        # Разбивка времени
        c.create_text(30, 60, anchor="w",
                      text=(f"Эмиссия: {self._format_ms(self.emission_time)}   |   "
                            f"Распространение: {self._format_ms(self.propagation_time)}   |   "
                            f"Итого: {self._format_ms(self.total_time)}"),
                      font=("Arial", 10), fill="#666")

    # ------------------------------------------------------------
    # Отрисовка движущегося пакета
    # ------------------------------------------------------------
    def _draw_packet(self, t):
        if t > self.total_time:
            return

        head_time = self.emission_time
        tail_time = 0.0
        L = self.line_length_m

        # Позиции головы и хвоста пакета на линии (доля 0..1)
        head_pos = ((t - head_time) * CELERITY) / L
        tail_pos = ((t - tail_time) * CELERITY) / L

        # Ограничим диапазон
        head_pos = max(0.0, min(1.0, head_pos))
        tail_pos = max(0.0, min(1.0, tail_pos))

        # Пока пакет ещё эмитируется — хвост у передатчика
        if t < self.emission_time:
            tail_pos = 0.0

        # Пакет полностью принят
        if tail_pos >= 1.0:
            return

        x1 = LINE_X + head_pos * LINE_W
        x2 = LINE_X + tail_pos * LINE_W

        left = min(x1, x2)
        width = abs(x1 - x2)

        self.canvas.create_rectangle(
            left, LINE_Y + 2, left + width, LINE_Y + LINE_H - 2,
            fill="#e74c3c", outline=""
        )

    # ------------------------------------------------------------
    # Анимация
    # ------------------------------------------------------------
    def _tick(self, timestamp):
        if self.sim_start_ms == 0:
            self.sim_start_ms = timestamp

        elapsed = timestamp - self.sim_start_ms
        self.current_time = (elapsed / ANIMATION_DURATION_MS) * self.total_time

        self._draw_base()
        self._draw_packet(self.current_time)

        if self.current_time < self.total_time * 1.05:
            self.anim_id = self.root.after(16, self._tick, timestamp + 16)
        else:
            self._finish()

    def _finish(self):
        self.anim_id = None
        self.start_btn.config(state="normal")
        self.reset_btn.config(state="normal")
        self.info_var.set(
            f"✅ Пакет доставлен за {self._format_ms(self.total_time)} "
            f"(эмиссия: {self._format_ms(self.emission_time)}, "
            f"распространение: {self._format_ms(self.propagation_time)})"
        )

    # ------------------------------------------------------------
    # Кнопки
    # ------------------------------------------------------------
    def start_sim(self):
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None

        self._read_params()
        self.sim_start_ms = 0
        self.current_time = 0.0
        self.start_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")
        self.info_var.set("Симуляция идёт...")
        self._tick(0)

    def reset_sim(self):
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self.sim_start_ms = 0
        self.current_time = 0.0
        self.start_btn.config(state="normal")
        self.reset_btn.config(state="normal")
        self._read_params()
        self._draw_base()
        self.info_var.set("Нажмите «Старт», чтобы запустить симуляцию.")


# ============================================================
# Точка входа
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = LineSimApp(root)
    root.mainloop()