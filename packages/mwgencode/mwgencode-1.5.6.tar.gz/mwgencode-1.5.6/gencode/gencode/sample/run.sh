#!/usr/bin/env bash
# consul的host 格式 ip:port
export CONSUL_HTTP_ADDR=192.168.101.88:8500
# docker host的port
export WEB_PORT=8899
# true自動註冊到kong，true，false不做，注意字母全小寫
export KONG_AUTO_REGISTER=true
# true自動註冊成 consul服務，false不做，注意字母全小寫
export CONSUL_AUTO_REGISTER=true
# 资料库名，默认为 maxbus
export DATABASE_NAME=maxbus
# 权限用的系统名称
export SYSTEM_NAME=maxguide
# 權限第一層的ID
export SYSTEM_ID=maxguide000
export LOG_LEVEL=20
#export SWAGGER_HOST=192.168.101.88:8081
export UPLOAD_FOLDER="/var/文件共享目录"
# 认证方式 jwt，session，默认为jwt（不需要该设定，因auth已同时支持session和jwt）
# export AUTH_TYPE=jwt
# 開發環境的docker，代碼valume方式
# 设定session在redis中的保存时长，单位为秒，有设定值时，超过该值的时间没有用系统，session则失效，为0时按session有效时长等于登录的jwt有效时长
# export SESSION_EXPIRATION_TIME=0
docker-compose -f docker-compose-dev.yaml up -d
# 部署的docker-compose 文件
#docker-compose up -d

