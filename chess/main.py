import io
import sys
import subprocess
import urllib.request
import chess
import chess.pgn
import chess.svg
import cairosvg

def render_game(game_id, perspective="black", fps=1.0, size=800):
    url = f"https://lichess.org/game/export/{game_id}?clocks=false&evals=false"
    pgn_text = urllib.request.urlopen(url).read().decode("utf-8")
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()
    orientation = chess.BLACK if perspective == "black" else chess.WHITE

    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-vcodec", "png",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        f"{game_id}.mp4"
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write_frame(b, move=None, repeat=1):
        check_sq = b.king(b.turn) if b.is_check() else None
        svg = chess.svg.board(
            board=b,
            orientation=orientation,
            lastmove=move,
            check=check_sq,
            size=size
        )
        png = cairosvg.svg2png(bytestring=svg.encode("utf-8"))
        for _ in range(repeat):
            proc.stdin.write(png)

    write_frame(board)
    last_move = None
    for move in game.mainline_moves():
        board.push(move)
        last_move = move
        write_frame(board, move)

    write_frame(board, last_move, repeat=4)
    proc.stdin.close()
    proc.wait()

if __name__ == "__main__":
    gid = sys.argv[1]
    side = sys.argv[2] if len(sys.argv) > 2 else "black"
    render_game(gid, side)