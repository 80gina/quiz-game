"""Mini NPU 핵심 연산 모듈 (3번 미션과 같은 로직, 표준 라이브러리만 사용).

- 라벨 정규화: '+', 'cross' -> 'Cross' / 'x' -> 'X'
- MAC(Multiply-Accumulate) 연산: 위치별로 곱해서 모두 더한다 (반복문으로 직접 구현)
- 허용오차(epsilon) 기반 판정: 점수 차이가 1e-9보다 작으면 판정 불가(UNDECIDED)
- 패턴 생성: N x N 십자가(Cross)와 X 패턴
"""

EPSILON = 1e-9


def normalize_label(raw) -> str | None:
    """입력 라벨을 표준 라벨(Cross, X)로 바꾼다. 알 수 없으면 None."""
    key = str(raw).strip().lower()
    if key in ("+", "cross"):
        return "Cross"
    if key == "x":
        return "X"
    return None


def mac(pattern: list[list[float]], filt: list[list[float]]) -> float:
    """패턴과 필터를 위치별로 곱하고 모두 더한 점수를 돌려준다."""
    n = len(pattern)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filt[i][j]
    return total


def judge(score_cross: float, score_x: float) -> str:
    """두 점수를 비교해 Cross / X / UNDECIDED 로 판정한다."""
    if abs(score_cross - score_x) < EPSILON:
        return "UNDECIDED"
    return "Cross" if score_cross > score_x else "X"


def make_cross(n: int) -> list[list[int]]:
    """N x N 십자가: 가운데 가로줄과 세로줄이 1."""
    mid = n // 2
    return [[1 if i == mid or j == mid else 0 for j in range(n)] for i in range(n)]


def make_x(n: int) -> list[list[int]]:
    """N x N X: 두 대각선이 1."""
    return [[1 if i == j or i + j == n - 1 else 0 for j in range(n)] for i in range(n)]


def render(pattern: list[list[float]]) -> str:
    """패턴을 화면용 글자(■ = 1, □ = 0)로 바꾼다."""
    return "\n".join("".join("■" if v else "□" for v in row) for row in pattern)
