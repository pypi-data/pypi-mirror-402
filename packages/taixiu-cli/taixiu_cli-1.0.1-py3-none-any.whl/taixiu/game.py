"""
Tài Xỉu (Sic Bo) Casino CLI Game — Command-based
Requirements:
    pip install rich

Usage:
    python game.py [--money INIT_MONEY] [--no-sound]

Commands (examples):
    help
    bet tai 10000
    bet exact 9 5000
    allin xiu
    roll
    balance
    history
    stats
    odds
    deposit 500000
    withdraw 200000
    save
    load
    clear
    close       # return view to normal (after help/odds)
    exit

Notes:
- All interaction via typed commands + Enter.
- 'odds' and 'help' toggle special views; use 'close' to restore normal view.
"""
from typing import Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from datetime import datetime
import random, json, os, argparse, sys, time
from rich.live import Live

console = Console()

# ----------------- CLI args & config -----------------
parser = argparse.ArgumentParser(description="Tài Xỉu Casino Game")
parser.add_argument("--money", type=int, default=None, help="Initial money (VNĐ)")
parser.add_argument("--no-sound", action="store_true", help="Disable sound effects (no-op)")
args = parser.parse_args()

# default config (can be overridden by config.json)
default_config = {
    "init_money": 100000000000000,
    "min_bet": 100000,
    "max_bet": 50000000000000000,
    "payouts": {
        "tai": 1.8,
        "xiu": 1.8,
        "chan": 1.9,
        "le": 1.9,
        "pair": 2.5,
        "triple": 5.0,
        "exact": 6.0
    }
}
CONFIG_FILE = "config.json"
config = default_config.copy()
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        config.update(user_config)
    except Exception as e:
        console.print(f"[red]Không thể tải config.json: {e}[/]")

initial_money = config.get("init_money", default_config["init_money"])
min_bet = config.get("min_bet", default_config["min_bet"])
max_bet = config.get("max_bet", default_config["max_bet"])
payouts = config.get("payouts", default_config["payouts"])

# CLI override
if args.money:
    initial_money = args.money

# ----------------- Global game state -----------------
balance = initial_money
history = []
current_bets = []  # list of dicts: {"type":..., "value":..., "amount":...}
tai_count = 0
xiu_count = 0
announcement = ""
dice_result = None  # tuple of (d1,d2,d3) or None
view_mode = "normal"  # normal | odds | help
sound_enabled = not args.no_sound
SAVE_FILE = "taixiu_save.json"
current_input = ""  # store last user input to render in footer

# ASCII / Unicode dice
ASCII_DICE = {
    0: ["+-------+", "|       |", "|   ?   |", "|       |", "+-------+"],
    1: ["+-------+", "|       |", "|   o   |", "|       |", "+-------+"],
    2: ["+-------+", "| o     |", "|       |", "|     o |", "+-------+"],
    3: ["+-------+", "| o     |", "|   o   |", "|     o |", "+-------+"],
    4: ["+-------+", "| o   o |", "|       |", "| o   o |", "+-------+"],
    5: ["+-------+", "| o   o |", "|   o   |", "| o   o |", "+-------+"],
    6: ["+-------+", "| o   o |", "| o   o |", "| o   o |", "+-------+"]
}
UNICODE_DICE = ["⚀","⚁","⚂","⚃","⚄","⚅"]

BET_PHRASES = ["Chọn ngay, đừng ngại!", "Lên tiền rồi đó!", "Bệt hơi sâu nha...", "Nhiều cửa lắm nha!", "Đỏ quá rồi!"]
DEALER_COMMENTS = ["Ôi, may đó nha!", "Không trúng rồi, ráng lần sau!", "Quay kiểu này chưa hợp!", "Chúc mừng bạn!"]

THEME_COLORS = {
    "dark": {"bg": "on grey11", "fg": "bold white"},
    "blue": {"bg": "on blue", "fg": "bold white"},
    "red": {"bg": "on red", "fg": "bold white"},
    "green": {"bg": "on green", "fg": "bold black"},
}
if not hasattr(sys, "_theme"):
    sys._theme = "dark"

def set_theme(theme):
    if theme in THEME_COLORS:
        sys._theme = theme

def get_theme_bg():
    return THEME_COLORS.get(getattr(sys, "_theme", "dark"), THEME_COLORS["dark"])["bg"]

def get_theme_fg():
    return THEME_COLORS.get(getattr(sys, "_theme", "dark"), THEME_COLORS["dark"])["fg"]

def format_money(amount: int) -> str:
    return f"{amount:,} VNĐ"

def parse_money(text: str) -> Optional[int]:
    if not isinstance(text, str):
        return None
    text = text.strip().lower()
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1_000)
        if text.endswith("m"):
            return int(float(text[:-1]) * 1_000_000)
        if text.endswith("b"):
            return int(float(text[:-1]) * 1_000_000_000)
        return int(text)
    except Exception:
        return None

def save_game():
    global balance, history, tai_count, xiu_count, announcement
    data = {"balance": balance, "history": history, "tai_count": tai_count, "xiu_count": xiu_count}
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        announcement = f"[green]Đã lưu trạng thái vào {SAVE_FILE}[/]"
    except Exception as e:
        announcement = f"[red]Lỗi khi lưu: {e}[/]"

def load_game():
    global balance, history, tai_count, xiu_count, current_bets, dice_result, announcement
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            balance = data.get("balance", balance)
            history = data.get("history", history)
            tai_count = data.get("tai_count", tai_count)
            xiu_count = data.get("xiu_count", xiu_count)
            current_bets = []
            dice_result = None
            announcement = f"[green]Đã tải trạng thái từ {SAVE_FILE}[/]"
        except Exception as e:
            announcement = f"[red]Lỗi khi tải: {e}[/]"
    else:
        announcement = "[yellow]Không tìm thấy file lưu.[/]"

def compute_stats():
    total = len(history)
    wins = sum(1 for h in history if h.get("win"))
    losses = total - wins
    winrate = (wins / total * 100) if total else 0.0
    max_win = max_loss = 0
    cur_win = cur_loss = 0
    for h in history:
        if h.get("win"):
            cur_win += 1
            cur_loss = 0
        else:
            cur_loss += 1
            cur_win = 0
        max_win = max(max_win, cur_win)
        max_loss = max(max_loss, cur_loss)
    profit = balance - initial_money
    return total, wins, losses, winrate, max_win, max_loss, profit

def dealer_ai_message() -> str:
    recent = history[-10:]
    if not recent:
        msgs = [
            "🤖 Nhà cái phán: Cẩn thận nha, dòng đang lười!",
            "🤖 Nhà cái: Ai cũng có ngày may mắn..."
        ]
        return random.choice(msgs)
    tai = xiu = triples = 0
    for h in recent:
        dice = h.get("dice", [])
        if len(dice) == 3:
            dsum = sum(dice)
            if dice[0] == dice[1] == dice[2]:
                triples += 1
            elif dsum >= 11:
                tai += 1
            else:
                xiu += 1
    total = tai + xiu
    p_tai = (tai + 1) / (total + 2) if total >= 0 else 0.5
    if p_tai > 0.66:
        return f"🤖 Nhà cái phán: TÀI ĐANG BỆT ({int(p_tai*100)}%)"
    if p_tai < 0.34:
        return f"🤖 Có mùi XỈU quay đầu đó... ({int((1-p_tai)*100)}%)"
    neutral = [
        "🤖 Cân bằng lắm, đánh ít cho vui thôi.",
        "🤖 Nhà cái hơi do dự, chơi nhẹ đi nha.",
        f"🤖 Quan sát: {tai} TÀI / {xiu} XỈU / {triples} triple trong {len(recent)} ván"
    ]
    return random.choice(neutral)

def draw_ui() -> Layout:
    global balance, history, announcement, current_bets, dice_result, view_mode, current_input, help_content
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="content", ratio=1),
        Layout(name="footer", size=3)
    )
    if view_mode == "odds":
        layout["content"].split_row(
            Layout(name="dice", ratio=2),
            Layout(name="odds", ratio=2),
            Layout(name="right", ratio=3)
        )
    else:
        layout["content"].split_row(
            Layout(name="dice", ratio=2),
            Layout(name="right", ratio=3)
        )
    header_text = announcement or "[cyan]Nhập lệnh (gõ 'help' để xem danh sách lệnh)[/]"
    dealer_hint = dealer_ai_message() if history else ""
    header_panel = Panel(
        Text.from_markup(f"{header_text}\n{dealer_hint}", justify="center"),
        title="[bold yellow]TÀI XỈU - Sic Bo[/]",
        subtitle=f"Số dư: {format_money(balance)}",
        style=get_theme_bg()
    )
    layout["header"].update(header_panel)
    if dice_result:
        d1, d2, d3 = dice_result
        sum_d = d1 + d2 + d3
        uni_line = f"{UNICODE_DICE[d1-1]} {UNICODE_DICE[d2-1]} {UNICODE_DICE[d3-1]}"
        ascii_lines = []
        for i in range(len(ASCII_DICE[1])):
            ascii_lines.append(ASCII_DICE[d1][i] + " " + ASCII_DICE[d2][i] + " " + ASCII_DICE[d3][i])
        ascii_text = "\n".join(ascii_lines)
        result_text = "TÀI" if sum_d >= 11 else "XỈU"
        sum_color = "green" if sum_d >= 11 else "cyan"
        dice_panel = Panel(
            Text.from_markup(f"{uni_line}\n{ascii_text}\n\nTổng: {sum_d} → {result_text}", justify="center"),
            title="🎲 XÚC XẮC 🎲",
            subtitle=f"[bold {sum_color}]Kết quả[/]",
            style=get_theme_bg()
        )
    else:
        ascii_lines = []
        for i in range(len(ASCII_DICE[0])):
            ascii_lines.append(ASCII_DICE[0][i] + " " + ASCII_DICE[0][i] + " " + ASCII_DICE[0][i])
        ascii_text = "\n".join(ascii_lines)
        dice_panel = Panel(Text(ascii_text, justify="center"), title="🎲 XÚC XẮC 🎲", subtitle="Chưa có kết quả", style=get_theme_bg())
    layout["dice"].update(dice_panel)
    if view_mode == "odds":
        odds_table = Table.grid(padding=1)
        odds_table.add_column(justify="left")
        odds_table.add_column(justify="right")
        odds_table.add_row("TAI (11-17, trừ triple)", str(payouts.get("tai")))
        odds_table.add_row("XIU (4-10, trừ triple)", str(payouts.get("xiu")))
        odds_table.add_row("CHAN (tổng chẵn)", str(payouts.get("chan")))
        odds_table.add_row("LE (tổng lẻ)", str(payouts.get("le")))
        odds_table.add_row("PAIR (2 giống)", str(payouts.get("pair")))
        odds_table.add_row("TRIPLE (3 giống)", str(payouts.get("triple")))
        odds_table.add_row("EXACT (tổng chính xác)", str(payouts.get("exact")))
        odds_panel = Panel(odds_table, title="[bold]Odds & Payouts[/bold]", subtitle="Nhập 'close' để quay lại", style=get_theme_bg())
        layout["odds"].update(odds_panel)
    layout["right"].split_column(
        Layout(name="bet", size=5),
        Layout(name="history", ratio=3),
        Layout(name="stats", size=8)
    )
    if current_bets:
        bet_lines = []
        for b in current_bets:
            t = b["type"].upper()
            v = f"={b['value']}" if b.get("value") is not None else ""
            bet_lines.append(f"{t}{v}: {format_money(b['amount'])}")
        bet_text = "\n".join(bet_lines)
    else:
        bet_text = "[italic]Chưa đặt cược[/]"
    bet_panel = Panel(Text(bet_text, justify="left"), title="Cược hiện tại", subtitle=f"Số dư: {format_money(balance)}", style=get_theme_bg())
    layout["bet"].update(bet_panel)
    # History or help/shop
    if view_mode == "help":
        # Sử dụng help_content nếu có, ngược lại dùng sample_help mặc định
        if help_content:
            history_panel = Panel(Text(help_content), title="Help / Shop", style=get_theme_bg())
        else:
            sample_help = (
                "[bold]Mẫu lệnh nhanh[/bold]\n"
                "- bet tai 10000        (cược TÀI 10k)\n"
                "- bet xiu 50000        (cược XỈU 50k)\n"
                "- bet exact 9 5000     (cược tổng = 9, 5k)\n"
                "- allin xiu            (cược toàn bộ vào Xỉu)\n"
                "- roll                 (quay xúc xắc)\n"
                "- balance              (xem số dư)\n"
                "- history              (xem lịch sử)\n"
                "- stats                (thống kê)\n"
                "- odds                 (hiển thị odds)\n"
                "- deposit <tien>       (nạp tiền)\n"
                "- withdraw <tien>      (rút tiền)\n"
                "- save / load / clear\n"
                "- shop                 (đổi skin/màu)\n"
                "- close                (trở về chế độ bình thường)\n"
                "- exit                 (thoát game)\n"
            )
            history_panel = Panel(Text(sample_help), title="Help — Quick Examples", style=get_theme_bg())
    else:
        hist_table = Table(show_header=True, header_style="bold magenta")
        hist_table.add_column("#", width=3)
        hist_table.add_column("Time", width=5)
        hist_table.add_column("Bet", justify="right")
        hist_table.add_column("Choice", width=10)
        hist_table.add_column("Dice", width=7)
        hist_table.add_column("Sum", width=3, justify="right")
        hist_table.add_column("KQ", justify="center")
        hist_table.add_column("Balance", justify="right")
        recent = history[-10:]
        start_index = len(history) - len(recent) + 1 if history else 1
        for i, h in enumerate(recent, start=start_index):
            t = h.get("time", "")
            bet_amt = format_money(h.get("bet", 0))
            choice = h.get("choice", "")
            dice = h.get("dice", [])
            dice_str = "-".join(str(d) for d in dice) if dice else ""
            sum_v = str(sum(dice)) if dice else ""
            win_flag = h.get("win", False)
            res_text = Text("WIN", style="green") if win_flag else Text("LOSE", style="red")
            bal_after = format_money(h.get("balance", 0))
            hist_table.add_row(str(i), t, bet_amt, choice, dice_str, sum_v, res_text, bal_after)
        history_panel = Panel(hist_table, title="Lịch sử (ván gần đây)", style=get_theme_bg())
    layout["history"].update(history_panel)
    total_bets, wins, losses, winrate, max_win_streak, max_loss_streak, profit = compute_stats()
    stats_tbl = Table.grid(padding=0)
    stats_tbl.add_column(justify="left")
    stats_tbl.add_column(justify="right")
    stats_tbl.add_row("Tổng ván", str(total_bets))
    stats_tbl.add_row("Thắng", str(wins))
    stats_tbl.add_row("Thua", str(losses))
    stats_tbl.add_row("Tỉ lệ thắng", f"{winrate:.1f}%")
    stats_tbl.add_row("Chuỗi thắng dài nhất", str(max_win_streak))
    stats_tbl.add_row("Chuỗi thua dài nhất", str(max_loss_streak))
    stats_tbl.add_row("Tài (Big)", str(tai_count))
    stats_tbl.add_row("Xỉu (Small)", str(xiu_count))
    prof_txt = Text(format_money(profit), style="green" if profit >= 0 else "red")
    stats_tbl.add_row("Lãi/Lỗ", prof_txt)
    layout["stats"].update(Panel(stats_tbl, title="Thống kê", style=get_theme_bg()))
    footer_text = Text(
        "help | bet <cua> <tien> | allin <cua> | roll | balance | history | stats | odds | deposit <tien> | withdraw <tien> | save | load | clear | close | shop | exit",
        style="bold bright_white",
        justify="center"
    )
    layout["footer"].update(Panel(footer_text, style=get_theme_bg()))
    return layout

def place_bet(parts):
    global announcement, current_bets, balance
    try:
        if len(parts) < 3:
            announcement = "[red]Cú pháp sai. Ví dụ: bet tai 10000[/]"
            return
        typ = parts[1].lower()
        if typ not in ("tai","xiu","chan","le","pair","triple","exact"):
            announcement = "[red]Cửa cược không hợp lệ.[/]"
            return
        if typ == "exact":
            if len(parts) != 4:
                announcement = "[red]Cú pháp sai. Ví dụ: bet exact 9 5000[/]"
                return
            try:
                val = int(parts[2])
            except Exception:
                announcement = "[red]Số không hợp lệ.[/]"
                return
            amt = parse_money(parts[3])
            if amt is None:
                announcement = "[red]Số tiền không hợp lệ (vd: 100k, 5m, 1b)[/]"
                return
            if val < 3 or val > 18:
                announcement = "[red]Exact phải trong 3-18.[/]"
                return
        else:
            amt = parse_money(parts[2]) if len(parts) >= 3 else None
            if amt is None:
                announcement = "[red]Số tiền không hợp lệ (vd: 100k, 5m, 1b)[/]"
                return
            val = None
        if amt <= 0:
            announcement = "[red]Số tiền phải > 0[/]"
            return
        if amt < min_bet:
            announcement = f"[red]Tối thiểu {format_money(min_bet)}[/]"
            return
        if amt > max_bet:
            announcement = f"[red]Tối đa {format_money(max_bet)}[/]"
            return
        total_staked = sum(b["amount"] for b in current_bets) + amt
        if total_staked > balance:
            announcement = "[red]Không đủ tiền để đặt thêm cược.[/]"
            return
        balance -= amt
        if typ == "exact":
            existing = next((b for b in current_bets if b["type"]=="exact" and b["value"]==val), None)
            if existing:
                existing["amount"] += amt
            else:
                current_bets.append({"type":"exact","value":val,"amount":amt})
            announcement = f"[green]✔ Đặt {format_money(amt)} vào EXACT {val}[/]"
        else:
            existing = next((b for b in current_bets if b["type"]==typ and b.get("value") is None), None)
            if existing:
                existing["amount"] += amt
            else:
                current_bets.append({"type":typ,"value":None,"amount":amt})
            announcement = f"[green]✔ Đặt {format_money(amt)} vào {typ.upper()}[/]"
    except Exception as e:
        announcement = f"[red]Lỗi khi đặt cược: {e}[/]"

def do_roll():
    global dice_result, balance, history, current_bets, announcement, tai_count, xiu_count
    if not current_bets:
        announcement = "[yellow]⚠️ Chưa đặt cược. Dùng: bet <cua> <tien>[/]"
        console.clear()
        console.print(draw_ui())
        return
    try:
        anim_duration = 5.25
        frame_delay = 0.35
        frames = max(6, int(anim_duration / frame_delay))
        announcement = "🎲 Đang lắc xúc xắc..."
        with Live(draw_ui(), console=console, screen=False, refresh_per_second=10) as live:
            for _ in range(frames):
                tmp = (random.randint(1,6), random.randint(1,6), random.randint(1,6))
                dice_result = tmp
                live.update(draw_ui())
                time.sleep(frame_delay)
            d1, d2, d3 = random.randint(1,6), random.randint(1,6), random.randint(1,6)
            dice_result = (d1, d2, d3)
            total = d1 + d2 + d3
            triple = (d1 == d2 == d3)
            result_tai = (not triple and total >= 11)
            result_xiu = (not triple and total <= 10)
            if not triple:
                if total >= 11:
                    tai_count += 1
                else:
                    xiu_count += 1
            summary_lines = []
            for bet in list(current_bets):
                btype = bet["type"]
                val = bet.get("value")
                amt = bet["amount"]
                win = False
                payout = payouts.get(btype, 0)
                if triple:
                    win = (btype == "triple")
                else:
                    if btype == "tai":
                        win = result_tai
                    elif btype == "xiu":
                        win = result_xiu
                    elif btype == "chan":
                        win = (total % 2 == 0)
                    elif btype == "le":
                        win = (total % 2 == 1)
                    elif btype == "pair":
                        pair = ((d1==d2!=d3) or (d1==d3!=d2) or (d2==d3!=d1))
                        win = pair
                    elif btype == "triple":
                        win = triple
                    elif btype == "exact":
                        win = (total == val)
                if win:
                    gain = int(amt * payout)
                    balance += gain 
                    summary_lines.append(f"[green]✔ Thắng {btype.upper()}{(' '+str(val)) if val else ''} +{format_money(gain)}[/]")
                else:
                    summary_lines.append(f"[red]❌ Thua {btype.upper()}{(' '+str(val)) if val else ''}[/]")
                history.append({
                    "time": datetime.now().strftime("%H:%M"),
                    "bet": amt,
                    "choice": f"{btype.upper()}{(' '+str(val)) if val else ''}",
                    "dice": [d1, d2, d3],
                    "win": win,
                    "balance": balance
                })
            current_bets.clear()
            dealer_msg = dealer_ai_message()
            announcement = "\n".join(summary_lines + [dealer_msg])
            live.update(draw_ui())
        console.clear()
        console.print(draw_ui())
        if balance <= 0:
            console.print("[red]Bạn đã hết tiền! Game Over![/]")
            sys.exit(0)
    except Exception as e:
        announcement = f"[red]Lỗi khi quay: {e}[/]"
        console.clear(); console.print(draw_ui())

def handle_shop_command(parts):
    if len(parts) == 1:
        return (
            "[bold]Shop Fake:[/]\n"
            "- skin classic/blue/red\n"
            "- theme dark/blue/red/green\n"
            "Dùng: shop skin <tên> hoặc shop theme <tên>"
        )
    if parts[1] == "skin":
        if len(parts) < 3 or parts[2] not in ("classic", "blue", "red"):
            return "[red]Cú pháp: shop skin <classic|blue|red>[/]"
        global UNICODE_DICE
        if parts[2] == "classic":
            UNICODE_DICE = ["⚀","⚁","⚂","⚃","⚄","⚅"]
        elif parts[2] == "blue":
            UNICODE_DICE = ["[blue]⚀[/]","[blue]⚁[/]","[blue]⚂[/]","[blue]⚃[/]","[blue]⚄[/]","[blue]⚅[/]"]
        elif parts[2] == "red":
            UNICODE_DICE = ["[red]⚀[/]","[red]⚁[/]","[red]⚂[/]","[red]⚃[/]","[red]⚄[/]","[red]⚅[/]"]
        return f"[green]Đã đổi skin xúc xắc thành {parts[2]}[/]"
    if parts[1] == "theme":
        if len(parts) < 3 or parts[2] not in THEME_COLORS:
            return "[red]Cú pháp: shop theme <dark|blue|red|green>[/]"
        set_theme(parts[2])
        return f"[green]Đã đổi màu giao diện thành {parts[2]}[/]"
    return "[red]Cú pháp: shop skin <classic|blue|red> hoặc shop theme <dark|blue|red|green>[/]"

def main_loop():
    global announcement, view_mode, dice_result, balance, current_input, help_content
    console.clear()
    console.print(draw_ui())
    while True:
        current_input = ""
        try:
            raw = input("> ")
        except (KeyboardInterrupt, EOFError):
            raw = "exit"
        cmd = (raw or "").strip()
        current_input = cmd
        if not cmd:
            announcement = "[yellow]Lệnh rỗng. Gõ 'help' để xem lệnh.[/]"
            console.clear(); console.print(draw_ui()); continue
        parts = cmd.split()
        command = parts[0].lower()
        if command == "help":
            view_mode = "help"
            help_content = None
            announcement = "[cyan]Help mode: xem mẫu lệnh. Gõ 'close' để quay lại.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "shop":
            view_mode = "help"
            help_content = handle_shop_command(parts)
            announcement = ""
            console.clear(); console.print(draw_ui()); continue
        if command == "close":
            view_mode = "normal"
            help_content = None
            announcement = "[cyan]Đã trở về chế độ bình thường.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "odds":
            view_mode = "odds"
            announcement = "[cyan]Odds mode: xem tỷ lệ trả. Gõ 'close' để quay lại.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "bet":
            place_bet(parts)
            console.clear(); console.print(draw_ui()); continue
        if command == "allin":
            if len(parts) != 2:
                announcement = "[red]Cú pháp: allin <cua>[/]"
                console.clear(); console.print(draw_ui()); continue
            cua = parts[1].lower()
            if cua not in ("tai","xiu","chan","le","pair","triple","exact"):
                announcement = "[red]Cửa không hợp lệ[/]"
                console.clear(); console.print(draw_ui()); continue
            if balance <= 0:    
                announcement = "[red]Số dư không đủ[/]"
                console.clear(); console.print(draw_ui()); continue
            if cua == "exact":
                announcement = "[red]allin không hỗ trợ exact (dùng bet exact n amount)[/]"
                console.clear(); console.print(draw_ui()); continue
            parts2 = ["bet", cua, str(balance)]
            place_bet(parts2)
            console.clear(); console.print(draw_ui()); continue
        if command == "roll":
            do_roll()
            continue
        if command == "balance":
            announcement = f"[green]Số dư hiện tại: {format_money(balance)}[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "history":
            view_mode = "normal"
            announcement = "[cyan]Lịch sử hiển thị phía dưới.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "stats":
            view_mode = "normal"
            announcement = "[cyan]Thống kê hiển thị phía dưới.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "odds_table" or command == "odds?":
            view_mode = "odds"
            announcement = "[cyan]Odds mode: gõ 'close' để quay lại.[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "deposit":
            if len(parts) < 2:
                announcement = "[red]Cú pháp: deposit <tien> (vd: 500k, 2m)[/]"
                console.clear(); console.print(draw_ui()); continue
            amt = parse_money(parts[1])
            if amt is None:
                announcement = "[red]Cú pháp: deposit <tien> (vd: 500k, 2m)[/]"
                console.clear(); console.print(draw_ui()); continue
            if amt <= 0:
                announcement = "[red]Số tiền phải > 0[/]"
                console.clear(); console.print(draw_ui()); continue
            balance += amt
            announcement = f"[green]Đã nạp {format_money(amt)}[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "withdraw":
            if len(parts) < 2:
                announcement = "[red]Cú pháp: withdraw <tien> (vd: 500k, 2m)[/]"
                console.clear(); console.print(draw_ui()); continue
            amt = parse_money(parts[1])
            if amt is None:
                announcement = "[red]Cú pháp: withdraw <tien> (vd: 500k, 2m)[/]"
                console.clear(); console.print(draw_ui()); continue
            if amt <= 0:
                announcement = "[red]Số tiền phải > 0[/]"
                console.clear(); console.print(draw_ui()); continue
            if amt > balance:
                announcement = "[red]Không đủ số dư để rút[/]"
                console.clear(); console.print(draw_ui()); continue
            balance -= amt
            announcement = f"[green]Đã rút {format_money(amt)}[/]"
            console.clear(); console.print(draw_ui()); continue
        if command == "save":
            save_game()
            console.clear(); console.print(draw_ui()); continue
        if command == "load":
            load_game()
            console.clear(); console.print(draw_ui()); continue
        if command == "clear":
            announcement = ""
            console.clear(); console.print(draw_ui()); continue
        if command in ("exit","quit"):
            announcement = "[yellow]Thoát game. Hẹn gặp lại![/]"
            break
        announcement = "[red]Lệnh không hợp lệ. Gợi ý: help[/]"
        console.clear(); console.print(draw_ui())
def main():
    try:
        main_loop()
    except Exception as e:
        console.print(f"[red]Lỗi không mong muốn: {e}[/]")
        raise

if __name__ == "__main__":
    main()
