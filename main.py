import asyncio
import pygame
import sys
import random
import time

# 定数
BOARD_SIZE = 9
PIECE_PIX = 50


# 駒の移動可能範囲パターン
PIECE_MOVES = {

  "Ki": [
    [0, 0, 0],
    [1, 1, 1],
    [1, "x", 1],
    [0, 1, 0]
  ],
  "Gi": [
    [0, 0, 0],
    [1, 1, 1],
    [0, "x", 0],
    [1, 0, 1]
  ],
  "Oh": [
    [0, 0, 0],
    [1, 1, 1],
    [1, "x", 1],
    [1, 1, 1]
  ],
  "Ke": [
    [1, 0, 1],
    [0, 0, 0],
    [0, "x",0],
    [0, 0, 0]
  ],
  "Fu": [
    [0, 1, 0],
    [0, "x",0],
    [0, 0, 0]
  ],
  "Ky": [
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
    [0, "x",0],
  ],

}

# チームの移動方向
DIRECTION_MAP = {
  "A": 0,   # 上向き
  "B": 180,  # 右向き
}


########################################################
class AIShougi:
  def __init__(self, board):
    self.board = board

  PIECE_VALUES = {
    "Ki": 50,
    "Gi": 30,
    "Oh": 1000,
    "Ke": 25,
    "Ky": 20,
    "Fu": 5
  }

  def evaluate_board(self):
    """盤面の評価値を計算"""
    score = 0
    ox, oy = 0, 0
    for y in range(BOARD_SIZE):
      for x in range(BOARD_SIZE):
        piece = self.board[y][x]
        if piece:
          value = self.PIECE_VALUES[piece.name]
          if piece.team == "B":
            score += value * 1.1
          else:
            score -= value

          if piece.team == "B" and piece.name == "Oh":
            ox = x
            oy = y

    # print(ox, oy)
    for y in range(3):
      for x in range(3):
        ix = ox - 1 + x
        iy = oy + y
        if 0 <= ix < BOARD_SIZE and 0 <= iy < BOARD_SIZE:
          piece = self.board[iy][ix]
          if piece:
            if piece.team == "B":
              score += self.PIECE_VALUES[piece.name] * 0.4
            else:
              score -= self.PIECE_VALUES[piece.name] * 0.8

    return score

  def generate_moves(self, team):
    """指定されたチームの全ての可能な移動を生成"""
    moves = []
    for y in range(BOARD_SIZE):
      for x in range(BOARD_SIZE):
        piece = self.board[y][x]
        if piece and piece.team == team:
          move_pattern = piece.get_move_pattern()
          # 中心位置 ("x") を探す
          center_x, center_y = None, None
          for dy, row in enumerate(move_pattern):
            for dx, cell in enumerate(row):
              if cell == "x":
                center_x, center_y = dx, dy
                break
            if center_x is not None:
              break
          # 移動可能なセルを計算
          for dy, row in enumerate(move_pattern):
            for dx, cell in enumerate(row):
              if cell == 1:
                nx = x + dx - center_x
                ny = y + dy - center_y
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                  target_piece = self.board[ny][nx]
                  if not target_piece or target_piece.team != team:
                    moves.append(((x, y), (nx, ny)))
    # print(len(moves))
    return moves

  def make_move(self, move):
    """指定された移動を実行"""
    (start_x, start_y), (end_x, end_y) = move
    self.board[end_y][end_x] = self.board[start_y][start_x]
    self.board[start_y][start_x] = None

  def undo_move(self, move, captured_piece=None):
    """指定された移動を元に戻す"""
    (start_x, start_y), (end_x, end_y) = move
    self.board[start_y][start_x] = self.board[end_y][end_x]
    self.board[end_y][end_x] = captured_piece


  def minimax(self, depth, is_maximizing):
      """Minimaxアルゴリズムを用いて最適な手を探索"""
      if depth == 0:
          return self.evaluate_board(), None

      best_move = None
      best_moves = []  # スコアが同じ手を保持するリスト

      if is_maximizing:  # AIのターン
          max_eval = float('-inf')
          for move in self.generate_moves("B"):
              captured_piece = self.board[move[1][1]][move[1][0]]  # 取った駒を記録
              self.make_move(move)
              evaluation, _ = self.minimax(depth - 1, False)
              self.undo_move(move, captured_piece)

              if evaluation > max_eval:
                  max_eval = evaluation
                  best_move = move
                  best_moves = [move]  # 新しい最高スコアの場合、リセット
              elif evaluation == max_eval:
                  best_moves.append(move)  # スコアが同じ場合、候補に追加

          # スコアに変化がない場合はランダムな手を選択
          if len(best_moves) > 1:
              best_move = random.choice(best_moves)

          return max_eval, best_move

      else:  # 人間のターン
          min_eval = float('inf')
          for move in self.generate_moves("A"):
              captured_piece = self.board[move[1][1]][move[1][0]]  # 取った駒を記録
              self.make_move(move)
              evaluation, _ = self.minimax(depth - 1, True)
              self.undo_move(move, captured_piece)

              if evaluation < min_eval:
                  min_eval = evaluation
                  best_move = move
                  best_moves = [move]  # 新しい最低スコアの場合、リセット
              elif evaluation == min_eval:
                  best_moves.append(move)  # スコアが同じ場合、候補に追加

          # スコアに変化がない場合はランダムな手を選択
          if len(best_moves) > 1:
              best_move = random.choice(best_moves)

          return min_eval, best_move



#######################################################
class Piece:   
  """駒を表すクラス"""
  def __init__(self, name, team):
    self.name = name  # 駒の名前
    self.team = team  # 所属チーム
    self.angle = DIRECTION_MAP[team]  # チームに応じた回転角度

  def get_move_pattern(self):
    """駒の移動パターンを回転"""
    move_pattern = PIECE_MOVES[self.name]

    for _ in range(self.angle // 90):
      move_pattern = list(zip(*move_pattern))[::-1]  # 回転処理
    return move_pattern

  def print(self):
    message = f"name: {self.name} team: {self.team} angle: {self.angle}"
    return message


#######################################################
class GuiPygame:
  def __init__(self):
    pygame.init()
    self.screen = pygame.display.set_mode((PIECE_PIX * (BOARD_SIZE+1), PIECE_PIX * BOARD_SIZE))
    self.clock = pygame.time.Clock()
    self.running = True
    self.font = pygame.font.SysFont(None, 24)

  def set_game(self, game):
    self.game = game
    return
  
  def draw_board(self):
    """将棋盤を描画"""
    self.screen.fill((160, 82, 45))  # 背景色
    for x in range(BOARD_SIZE):
      for y in range(BOARD_SIZE):
        rect = pygame.Rect(x * PIECE_PIX, y * PIECE_PIX, PIECE_PIX, PIECE_PIX)
        pygame.draw.rect(self.screen, (210, 180, 140), rect)  # 各マスの色
        pygame.draw.rect(self.screen, (139, 69, 19), rect, 1)  # 枠線

  def draw_piece(self, bx, by, piece, color=(0, 0, 0)):
    """駒を描画"""
    name = piece.name
    angle = piece.angle
    # print("draw piece", bx, by, name)
    x = bx * PIECE_PIX + PIECE_PIX // 2
    y = by * PIECE_PIX + PIECE_PIX // 2
    text_surface = self.font.render(name, True, color)
    if angle == 180:
      text_surface = pygame.transform.rotate(text_surface, angle)
    text_rect = text_surface.get_rect(center=(x, y))
    self.screen.blit(text_surface, text_rect)

  def draw_all_pieces(self):
    for y in range(BOARD_SIZE):
      for x in range(BOARD_SIZE):
        piece = self.game.board[y][x]
        if piece:
          self.draw_piece(x, y, piece)

    return
  
  def draw_selected_cell(self):
    if self.game.selected_position is not None:
      bx, by = self.game.selected_position
      self.draw_cell(bx, by, (0, 0, 255))
    return
  
  def draw_movable_cells(self):
    for position in self.game.movable_cell_list:
      bx, by = position
      self.draw_cell(bx, by, (255, 255, 0))
    return
  
  def draw_cell(self, bx, by, color):
    rect = pygame.Rect(bx * PIECE_PIX + 5, by * PIECE_PIX + 5, PIECE_PIX - 10, PIECE_PIX - 10)
    pygame.draw.rect(self.screen, color, rect, 3)  # 枠を描画
    return
  
  def draw_turn(self):
    current_team = self.game.current_team
    """ターンの表示を更新"""
    # 日本語表示用のフォント
    font = self.font
    pygame.draw.rect(self.screen, (255, 255, 200), (PIECE_PIX * BOARD_SIZE, 10, 100, 50))  # 背景色で上書き
    text_dict = {"A": "You", "B": "AI"}
    text_surface = font.render(f"{text_dict[current_team]}", True, (0, 0, 0))  # 日本語で順番を表示
    text_rect = text_surface.get_rect(center=(PIECE_PIX * (BOARD_SIZE+0.5), 30))
    self.screen.blit(text_surface, text_rect)
    return
  
  def draw_all(self):
    self.draw_board()
    self.draw_all_pieces()
    self.draw_selected_cell()
    self.draw_movable_cells()
    self.draw_turn()

    # pygame.display.flip()
    # self.clock.tick(10)
    # await asyncio.sleep(0)  # 非同期ループ対応


    return
  
  def on_click(self, bx, by):
    if bx is None or BOARD_SIZE <= bx: 
      return
    if by is None or BOARD_SIZE <= by:
      return
    # bx is 0-8, by is 0-8

    self.game.on_click(bx, by)
    self.draw_all()

    return

  async def mainloop(self):
    """非同期のメインループ"""
    while self.running:
      if self.game.current_team == "A":
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            self.running = False
          elif event.type == pygame.MOUSEBUTTONDOWN:
            bx, by = event.pos[0] // PIECE_PIX, event.pos[1] // PIECE_PIX
            print(f"Clicked at: {event.pos}", bx, by)
            self.on_click(bx, by)

      else: # AI turn
        self.game.run_ai_turn()
        self.draw_all()


      pygame.display.flip()
      self.clock.tick(10)
      await asyncio.sleep(0)  # 非同期ループ対応

    pygame.quit()

        
#######################################################
class ShougiGame:
  def __init__(self, gui):
    self.gui = gui
    # self.gui.set_title("AI Shogi")
    self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    self.selected_piece = None
    self.selected_position = None
    self.movable_cell_list = []
    self.current_team = "A"

    self.ai = AIShougi(self.board)  # AIShougiクラスをインスタンス化
  

    self.gui.set_game(self)

    # self.gui.draw_board()
    self.init_piece_list()
    self.gui.draw_all()
    return
     
  def init_piece_list(self):
    """駒を初期配置"""
    # self.add_piece(0, 8, Piece("香", "A軍"))
    self.add_piece(1, 8, Piece("Ke", "A"))
    self.add_piece(2, 8, Piece("Gi", "A"))
    self.add_piece(3, 8, Piece("Ki", "A"))
    self.add_piece(4, 8, Piece("Oh", "A"))
    self.add_piece(5, 8, Piece("Ki", "A"))
    self.add_piece(6, 8, Piece("Gi", "A"))
    self.add_piece(7, 8, Piece("Ke", "A"))
    # self.add_piece(8, 8, Piece("香", "A軍"))

    # self.add_piece(0, 6, Piece("歩", "A軍"))
    # self.add_piece(1, 6, Piece("歩", "A軍"))
    # self.add_piece(2, 6, Piece("歩", "A軍"))
    # self.add_piece(3, 6, Piece("歩", "A軍"))
    # self.add_piece(4, 6, Piece("歩", "A軍"))
    # self.add_piece(5, 6, Piece("歩", "A軍"))
    # self.add_piece(6, 6, Piece("歩", "A軍"))
    # self.add_piece(7, 6, Piece("歩", "A軍"))
    # self.add_piece(8, 6, Piece("歩", "A軍"))

    # self.add_piece(0, 0, Piece("香", "C軍"))
    self.add_piece(1, 0, Piece("Ke", "B"))
    self.add_piece(2, 0, Piece("Gi", "B"))
    self.add_piece(3, 0, Piece("Ki", "B"))
    self.add_piece(4, 0, Piece("Oh", "B"))
    self.add_piece(5, 0, Piece("Ki", "B"))
    self.add_piece(6, 0, Piece("Gi", "B"))
    self.add_piece(7, 0, Piece("Ke", "B"))
    # self.add_piece(8, 0, Piece("香", "C軍"))

    # self.add_piece(0, 2, Piece("歩", "C軍"))
    # self.add_piece(1, 2, Piece("歩", "C軍"))
    # self.add_piece(2, 2, Piece("歩", "C軍"))
    # self.add_piece(3, 2, Piece("歩", "C軍"))
    # self.add_piece(4, 2, Piece("歩", "C軍"))
    # self.add_piece(5, 2, Piece("歩", "C軍"))
    # self.add_piece(6, 2, Piece("歩", "C軍"))
    # self.add_piece(7, 2, Piece("歩", "C軍"))
    # self.add_piece(8, 2, Piece("歩", "C軍"))

    return
  
  def add_piece(self, bx, by, piece):
    """駒を配置"""
    self.board[by][bx] = piece
    # self.gui.add_piece(bx, by, piece)
    return
  
  def set_selected_piece(self, bx, by):
    piece = self.board[by][bx]

    if piece and piece.team == self.current_team:
      self.selected_piece = piece
      self.selected_position = (bx, by)
    return
  
  def move_piece(self, bx, by):
    old_bx, old_by = self.selected_position
    piece = self.selected_piece

    target_piece = self.board[by][bx]

    self.board[old_by][old_bx] = None
    self.board[by][bx] = piece

    self.selected_piece = None
    self.selected_position = None

    return    
  
  def set_movable_cell_list(self, bx, by):
    piece = self.selected_piece

    if piece is None:
      return
    if piece.name not in PIECE_MOVES:
      return
    
    move_pattern = piece.get_move_pattern()

    # 中心位置 ("x") を探す
    center_x, center_y = None, None
    for dy, row in enumerate(move_pattern):
      for dx, cell in enumerate(row):
        if cell == "x":
          center_x, center_y = dx, dy
          break
      if center_x is not None:
        break

    if center_x is None or center_y is None:
      return
    
    # 移動可能セルを計算
    for dy, row in enumerate(move_pattern):
      for dx, cell in enumerate(row):
        if cell == 1:
          nx = bx + dx - center_x
          ny = by + dy - center_y
          if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            target_piece = self.board[ny][nx]

            # 空欄または敵軍である場合のみハイライト
            if not target_piece or target_piece.team != piece.team:
              self.movable_cell_list.append((nx, ny))  # 一貫した形式で追加

    print(self.movable_cell_list)
    return
  
  def clear_selection(self):
    self.selected_piece = None
    self.selected_position = None
    self.movable_cell_list.clear()
    return
  
  def switch_turn(self):
    """ターンを切り替える"""
    teams = ["A", "B"]
    next_index = (teams.index(self.current_team) + 1) % len(teams)
    self.current_team = teams[next_index]

    # # AIターンの処理を呼び出す
    # if self.current_team == "B":
    #   self.gui.draw_all()
    #   self.run_ai_turn()
    #   self.current_team = "A"
    return
  
  def run_ai_turn(self):
    """B軍のAIターン処理"""
    print("AI Turn")
    ai_depth = 4
    eval, best_move = self.ai.minimax(depth=ai_depth, is_maximizing=True)
    print(f"AI Evaluation: {eval}")

    if best_move:
      (bx, by), (nx, ny) = best_move
      piece = self.board[by][bx]

      # self.set_selected_piece(bx, by)
      # self.set_movable_cell_list(bx, by)
      # self.gui.draw_all()
      # time.sleep(0.5)  # 0.1秒間だけ表示

      # self.movable_cell_list.clear()


      # 移動処理を実行
      self.selected_piece = piece
      self.selected_position = (bx, by)
      self.move_piece(nx, ny)
      self.current_team = "A"
      return
    
    self.current_team = "A"
    return
  
  def on_click(self, bx, by):

    if self.current_team == "A":
      if not self.selected_piece:
        self.set_selected_piece(bx, by)
        self.set_movable_cell_list(bx, by)
      elif (bx, by) in self.movable_cell_list:
        self.move_piece(bx, by)
        self.movable_cell_list.clear()
        self.switch_turn()
      else:
        self.clear_selection()

    else: # AI turn
       pass


    # self.print_pieces()
    return
  
  def print_pieces(self):
    for y in range(BOARD_SIZE):
      for x in range(BOARD_SIZE):
        piece = self.board[y][x]
        if piece:
          print(x, y, piece.name)



#########################################
# 実行
gui = GuiPygame()
game = ShougiGame(gui)


asyncio.run(gui.mainloop())
