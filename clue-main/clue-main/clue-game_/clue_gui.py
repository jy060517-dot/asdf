import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import random
import time
import os
from collections import defaultdict 

# ==================== 게임 데이터 및 카드 목록 ====================

SUSPECTS = ["머스타드", "피콕", "스칼렛", "플럼", "그린", "화이트"]
WEAPONS = ["단검", "촛대", "권총", "밧줄", "파이프", "렌치"]
ROOMS = ["마당", "게임룸", "거실", "부엌", "서재", "식당", "차고", "욕실", "침실"]
PLAYER_CARD_COUNT = 4 

class Card:
    """정적 메서드를 사용하여 카드 데이터에 접근"""
    def __init__(self, name, card_type):
        self.name = name
        self.card_type = card_type
    
    @staticmethod
    def get_all_names():
        return SUSPECTS + WEAPONS + ROOMS

# ==================== 게임 로직 및 UI 관리 클래스 ====================

class GameManager:
    
    @classmethod
    def create_deck(cls):
        """모든 카드 객체를 생성"""
        all_cards = ([Card(n, "살인자") for n in SUSPECTS] +
                     [Card(n, "무기") for n in WEAPONS] +
                     [Card(n, "장소") for n in ROOMS])
        return all_cards

    @staticmethod
    def load_card_image_safe(card_name, card_type):
        """try...except를 포함한 정적 메서드로 이미지 로딩을 처리"""
        if card_type == "무기": folder = "weapons"
        elif card_type == "살인자": folder = "suspects"
        elif card_type == "장소": folder = "rooms"
        else: folder = "unknown"
        image_path = os.path.join("images", folder, f"{card_name}.png")
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path).resize((100, 140))
                return ImageTk.PhotoImage(img)
            else:
                raise FileNotFoundError(f"Image file not found: {image_path}")
        except Exception:
            return GameManager.create_default_card(card_name, card_type)

    @staticmethod
    def create_default_card(card_name, card_type):
        """기본 이미지 생성 로직"""
        img = Image.new('RGB', (100, 140), color='lightgray')
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 99, 139], outline='black', width=2)
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("malgun.ttf", 15)
        except Exception:
            font = None
        draw.text((50, 70), f"{card_name}\n({card_type})", fill='black', anchor='mm', font=font, align='center')
        return ImageTk.PhotoImage(img)


    def __init__(self, root, canvas, human_player_name, selected_ball_id_init):
        self.root = root
        self.canvas = canvas
        self.MOVE_STEP = 60 
        self.human_player_name = human_player_name
        
        self.game = self._setup_game(human_player_name) 
        
        self.selected_ball_id = selected_ball_id_init 
        self.dice_roll_result = 0
        self.is_moving = False 
        self.last_dice_roll = 0
        
        self._init_ui()
        self.start_turn()

    def _setup_game(self, human_name):
        """게임 데이터 설정 및 카드 분배"""
        solution = {
            "무기": random.choice(WEAPONS),
            "살인자": random.choice(SUSPECTS),
            "장소": random.choice(ROOMS)
        }
        all_cards = GameManager.create_deck() 
        
        remaining_cards = [c for c in all_cards if not any(c.name == s for s in solution.values())]
        random.shuffle(remaining_cards)
        
        human_hand = remaining_cards[:PLAYER_CARD_COUNT]
        unclaimed_cards = remaining_cards[PLAYER_CARD_COUNT:] 
        
        return {'solution': solution, 'hand': human_hand, 'unclaimed': unclaimed_cards}


    def _init_ui(self):
        # 상태 라벨
        self.status_label = tk.Label(
            self.root, 
            text="", 
            font=("맑은 고딕", 16, "bold"), 
            bg='white', 
            fg='black', 
            justify=tk.CENTER,
            borderwidth=2, relief="groove"
        )
        self.status_label.place(relx=0.5, y=30, anchor=tk.CENTER, width=screen_width * 0.7)
        
        # 버튼들
        self.dice_btn = tk.Button(self.root, text="주사위 굴리기", command=self.open_dice_window, font=("Arial", 20), anchor='center')
        self.dice_btn.place(x=screen_width - 250, y=screen_height - 100)
        
        # ⚠️ 턴 종료 버튼 제거 ⚠️
        
        self.guess_btn = tk.Button(self.root, text="추리/고발", command=self.open_guess_window, font=("Arial", 20), state=tk.DISABLED, anchor='center', bg='blue', fg='white')
        self.guess_btn.place(x=screen_width - 250, y=screen_height - 160)
        
        self.card_btn = tk.Button(self.root, text="내 카드 보기", command=self.show_my_hand, font=("맑은 고딕", 12))
        self.card_btn.place(x=50, y=screen_height - 100)

    # --- UI 액션 함수 ---

    def open_guess_window(self):
        if self.guess_btn['state'] == tk.NORMAL: # '추리/고발' 버튼이 활성화된 상태에서만
            win = tk.Toplevel(self.root)
            win.title("추리 또는 고발 선택")
            win.geometry("300x150")
            win.attributes('-topmost', True)

            tk.Button(win, text="일반 추리 (진행)", command=lambda: self._start_action(win, False), bg='lightgray', width=20).pack(pady=10)
            tk.Button(win, text="최종 고발 (성공/실패)", command=lambda: self._start_action(win, True), bg='red', fg='white', width=20).pack(pady=5)
    
    def _start_action(self, win, is_accusation):
        win.destroy()
        GuessAccusationWindow(self.root, self, is_accusation, SUSPECTS, WEAPONS, ROOMS)

    def show_my_hand(self):
        """새 창에 내 카드 표시"""
        hand_win = tk.Toplevel(self.root)
        hand_win.title("내 카드")
        hand_win.attributes('-topmost', True)
        
        human_hand = self.game['hand']

        tk.Label(hand_win, text=f"👤 {self.human_player_name} (나)의 카드 ({len(human_hand)}장)", 
                 font=("맑은 고딕", 14, "bold"),
                 pady=10).pack()

        card_frame = tk.Frame(hand_win)
        card_frame.pack(padx=10, pady=10)
        
        self.card_images = [] 
        
        for i, card in enumerate(human_hand):
            card_img = GameManager.load_card_image_safe(card.name, card.card_type)
            self.card_images.append(card_img) 
            
            img_label = tk.Label(card_frame, image=card_img, borderwidth=1, relief="solid")
            img_label.grid(row=0, column=i, padx=5)
            
            tk.Label(card_frame, text=f"{card.name}", 
                     font=("맑은 고딕", 10),
                     justify=tk.CENTER).grid(row=1, column=i)
        
        hand_win.update_idletasks()
        hand_win.geometry(f"{hand_win.winfo_reqwidth()}x{hand_win.winfo_reqheight()}+50+70")
        
        tk.Button(hand_win, text="닫기", command=hand_win.destroy).pack(pady=10)


    def open_dice_window(self):
        if not self.is_moving:
            win = tk.Toplevel(self.root)
            win.title("주사위")
            win.geometry("520x500")
            win.attributes('-topmost', True)

            def on_dice_roll_done(result):
                self.dice_roll_result = result
                win.destroy()
                self.handle_dice_result()

            ClueDice(win, on_dice_roll_done)
            self.dice_btn.config(state=tk.DISABLED)
            self.guess_btn.config(state=tk.DISABLED) # 주사위 굴리는 동안 추리 비활성화

    def handle_dice_result(self):
        """주사위 결과 처리"""
        self.status_label.config(text=f"🎲 내 턴! 주사위: {self.dice_roll_result}. 방향키로 {self.dice_roll_result}번 이동하세요.")
        
        self.is_moving = True
        self.last_dice_roll = self.dice_roll_result

    def end_turn_action(self):
        """턴 종료 후 다음 턴 시작 (이동 횟수 소진 시 호출)"""
        if self.game.get('game_over'):
            return

        self.is_moving = False
        self.last_dice_roll = 0
        
        self.dice_btn.config(state=tk.DISABLED)
        self.guess_btn.config(state=tk.NORMAL) # 추리/고발 버튼만 활성화
        self.status_label.config(text="이동 횟수를 모두 사용했습니다. '추리/고발'을 누르세요.")
            
        # self.start_turn() 호출 대신 행동 대기 상태 유지

    def start_turn(self):
        """새로운 턴 시작"""
        self.status_label.config(text=f"👉 {self.human_player_name} (나)의 턴입니다. 주사위를 굴리세요.")
        self.dice_btn.config(state=tk.NORMAL)
        self.guess_btn.config(state=tk.DISABLED) # 턴 시작 시 추리 버튼 비활성화

    # --- 이동 로직 ---

    def move_human_ball(self, event):
        """사람 플레이어의 토큰 이동 처리"""
        if not self.is_moving or self.last_dice_roll <= 0: 
            return

        dx, dy = 0, 0
        if event.keysym in ('Up', 'w'): dy = -self.MOVE_STEP
        elif event.keysym in ('Down', 's'): dy = self.MOVE_STEP
        elif event.keysym in ('Left', 'a'): dx = -self.MOVE_STEP
        elif event.keysym in ('Right', 'd'): dx = self.MOVE_STEP

        if dx != 0 or dy != 0:
            self.canvas.move(self.selected_ball_id, dx, dy) 
            
            self.last_dice_roll -= 1
            self.status_label.config(text=f"🎲 내 턴! 남은 이동 횟수: {self.last_dice_roll}")
            
            if self.last_dice_roll <= 0:
                self.end_turn_action() # 이동 횟수 소진 시 턴 종료 액션 호출


class GuessAccusationWindow:
    """추리/고발 처리 창"""
    def __init__(self, root, game_manager, is_accusation, suspects, weapons, rooms):
        self.game_manager = game_manager
        self.root = tk.Toplevel(root)
        self.root.title("고발" if is_accusation else "추리")
        self.root.geometry("400x400")
        self.root.attributes('-topmost', True)
        self.is_accusation = is_accusation
        self.refuting_message = tk.StringVar(self.root)
        self.refuting_message.set("추리 내용을 선택해주세요.")

        self.suspect_var = tk.StringVar(self.root)
        self.weapon_var = tk.StringVar(self.root)
        self.room_var = tk.StringVar(self.root)

        tk.Label(self.root, text="살인자:").pack(pady=5)
        tk.OptionMenu(self.root, self.suspect_var, *suspects).pack()

        tk.Label(self.root, text="무기:").pack(pady=5)
        tk.OptionMenu(self.root, self.weapon_var, *weapons).pack()

        tk.Label(self.root, text="장소:").pack(pady=5)
        tk.OptionMenu(self.root, self.room_var, *rooms).pack()
        
        tk.Label(self.root, textvariable=self.refuting_message, pady=10).pack()

        action_btn = tk.Button(self.root, text="최종 " + ("고발" if is_accusation else "추리"), command=self.submit_guess, bg='yellow')
        action_btn.pack(pady=20)

    def submit_guess(self):
        suspect = self.suspect_var.get()
        weapon = self.weapon_var.get()
        room = self.room_var.get()

        if not (suspect and weapon and room):
            self.refuting_message.set("세 가지 항목을 모두 선택해야 합니다.")
            return

        solution = self.game_manager.game['solution']

        if self.is_accusation:
            # --- 고발 로직 ---
            is_correct = (solution["무기"] == weapon and 
                          solution["살인자"] == suspect and 
                          solution["장소"] == room)
            
            if is_correct:
                self.refuting_message.set(f"🎉 **승리!** 정답입니다: {suspect}, {weapon}, {room}")
                self.game_manager.game['game_over'] = True
            else:
                self.refuting_message.set(f"❌ **패배!** 오답입니다: {suspect}, {weapon}, {room}. (게임 종료)")
                self.game_manager.game['game_over'] = True 
                
            tk.Button(self.root, text="게임 종료", command=lambda: self._finalize_turn(True)).pack(pady=10)
            self.root.attributes('-topmost', False) 
            return

        else:
            # --- 추리 로직 ---
            human_hand_names = [c.name for c in self.game_manager.game['hand']]
            unclaimed_names = [c.name for c in self.game_manager.game['unclaimed']]
            
            refute_card = next((item for item in [weapon, suspect, room] if item in human_hand_names), None)
            
            if refute_card:
                self.refuting_message.set(f"✅ **{refute_card}** 카드로 스스로 반박했습니다. (반박 성공)")
            else:
                potential_refutes = [item for item in [weapon, suspect, room] if item in unclaimed_names]
                
                if potential_refutes:
                    refute_card_simulated = random.choice(potential_refutes)
                    self.refuting_message.set(f"📢 다른 플레이어에게 **{refute_card_simulated}**으로 반박당했습니다. (미사용 카드 중 반박)")
                else:
                    self.refuting_message.set("🔔 아무도 반박하지 못했습니다! (성공적인 추리)")
            
            tk.Button(self.root, text="턴 마침", command=lambda: self._finalize_turn(False)).pack(pady=10)
            self.root.attributes('-topmost', False)


    def _finalize_turn(self, game_over):
        self.root.destroy()
        if game_over:
            self.game_manager.status_label.config(text="게임 종료! 다시 시작하려면 프로그램을 재실행하세요.")
            self.game_manager.dice_btn.config(state=tk.DISABLED)
            self.game_manager.guess_btn.config(state=tk.DISABLED)
        else:
            # 턴을 마치면 바로 주사위 굴리는 새 턴 시작
            self.game_manager.start_turn()


class ClueDice:
    """주사위 굴리기 GUI 클래스"""
    def __init__(self, round_window, callback):
        self.round = round_window
        self.callback = callback
        self.canvas = tk.Canvas(round_window, width = 500, height = 400, bg = 'white')
        self.canvas.pack()

        self.dice = self.canvas.create_rectangle(130,100,230,200, fill = 'white', outline='black')
        self.text = self.canvas.create_text(181,151, text ='주사위',font = ("Arial", 35))
        
        self.click_button = tk.Button(round_window, text='주사위 굴리기', command = self.rolling_dice)
        self.click_button.pack(pady=10)
        
        self.result_label = tk.Label(round_window, text="")
        self.result_label.pack()

        self.confirm_button = tk.Button(round_window, text='결과 확정', command=self.confirm_result, state=tk.DISABLED)
        self.confirm_button.pack(pady=10)
        self.final_number = 0

    def rolling_dice(self):
        self.click_button.config(state=tk.DISABLED)
        for i in range(20):
            num = random.randint(2,12)
            self.canvas.itemconfig(self.text,text=str(num))
            self.round.update()
            time.sleep(0.05)
            
        self.final_number = random.randint(2,12)
        self.canvas.itemconfig(self.text,text = str(self.final_number))
        self.result_label.config(text=f"나온 숫자: {self.final_number}")
        self.confirm_button.config(state=tk.NORMAL)

    def confirm_result(self):
        if self.final_number > 0:
            self.callback(self.final_number)


# ==================== 메인 프로그램 실행 ====================

root = tk.Tk()
root.title("Clue: 1인용 프로그램")
HUMAN_PLAYER_NAME = "스칼렛" 

# --- 화면 및 캔버스 설정 ---
try:
    root.attributes('-fullscreen', True)
    root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    try:
        original_image = Image.open("clueground.png")
        bg_img = original_image.resize((screen_width, screen_height))
        bg_img = ImageTk.PhotoImage(bg_img)
    except FileNotFoundError:
        bg_img = None
        raise

    canvas = tk.Canvas(root, width=screen_width, height=screen_height)
    canvas.pack(fill="both", expand=True)
    if bg_img:
        bg_id = canvas.create_image(0, 0, image=bg_img, anchor="nw")
        canvas.tag_lower(bg_id)
except Exception:
    root.attributes('-fullscreen', False)
    root.geometry("1200x800")
    screen_width = 1200
    screen_height = 800
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg='darkgreen')
    canvas.pack(fill="both", expand=True)

BALL_RADIUS = 15

# 토큰 1개 생성 (사람 플레이어)
human_ball_pos = (screen_width//2 - 20, screen_height//2 - 50, '#FF0000') 
x, y, color = human_ball_pos
selected_ball_id = canvas.create_oval(
    x, y, x + BALL_RADIUS*2, y + BALL_RADIUS*2,
    fill=color, outline="black"
)
canvas.tag_raise(selected_ball_id)
canvas.itemconfig(selected_ball_id, outline="#EEFF00", width=3) 

# 게임 매니저 실행
game_manager = GameManager(root, canvas, HUMAN_PLAYER_NAME, selected_ball_id)

# 방향키 바인딩
root.bind('<Key>', game_manager.move_human_ball)

root.mainloop()

#cd "C:\Users\이예림\Desktop\Clue" - 오류 시 사용
