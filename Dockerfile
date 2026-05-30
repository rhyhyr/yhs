# Node.js 20 버전의 가벼운(alpine) OS 이미지를 사용
FROM node:20-alpine

# 작업 폴더 지정
WORKDIR /app

# 패키지 정보 복사 및 설치
COPY package.json ./
RUN npm install

# 소스 코드 복사
COPY index.js ./

# 도커 컨테이너가 켜질 때 실행할 명령어
CMD ["node", "index.js"]