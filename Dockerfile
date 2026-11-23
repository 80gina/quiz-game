# 숲해설·환경교육 퀴즈 게임 (Python 3.10 이상 필요)
FROM python:3.12-slim

LABEL org.opencontainers.image.title="quiz-game" \
      org.opencontainers.image.description="숲해설·환경교육 터미널 퀴즈 게임" \
      org.opencontainers.image.source="https://github.com/80gina/quiz-game"

WORKDIR /app
COPY main.py npu_core.py data.json test_quizgame.py ./

# 퀴즈와 최고 점수는 /data 폴더(볼륨)에 저장해서, 컨테이너를 지워도 남게 한다.
ENV QUIZ_STATE_FILE=/data/state.json \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8
RUN mkdir -p /data
VOLUME ["/data"]

CMD ["python", "main.py"]
