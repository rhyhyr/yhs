FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
# 무거운 테스트 도구(devDependencies)는 빼고 서버 실행에 필요한 것만 가볍게 설치!
RUN npm install --omit=dev
COPY . .
EXPOSE 8080
CMD ["npm", "start"]