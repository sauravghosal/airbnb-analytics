# !/bin/zsh
mkdir ./bin
curl https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip -o ./chromedriver.zip
curl -L https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-53/stable-headless-chromium-amazonlinux-2017-03.zip -o ./headless-chromium.zip
unzip chromedriver.zip -d ./bin
unzip headless-chromium.zip -d ./bin
rm -f chromedriver.zip
rm -f headless-chromium.zip
