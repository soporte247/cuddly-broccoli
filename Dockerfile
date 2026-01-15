FROM node:18
WORKDIR /app
COPY package.json package.json
RUN npm install
COPY . /app
EXPOSE 5173
CMD ["npm", "run", "dev"]
