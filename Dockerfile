FROM ubuntu:latest

MAINTAINER Irving Duran <irving.duran@gmail.com>

RUN apt update && apt -y install wget
# setup chrome for install source https://www.linuxbabe.com/ubuntu/install-google-chrome-ubuntu-16-04-lts
RUN echo '\n\n#add chome browser to list of sources' \
  '\ndeb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list && \
  wget https://dl.google.com/linux/linux_signing_key.pub && \
  apt-key add linux_signing_key.pub

#install dependencies, chrome, and config environment
RUN apt update && apt upgrade -y && apt -y autoremove && \
  apt -y install python3 libxss1 libappindicator1 libindicator7 xvfb google-chrome-stable && \
  wget https://bootstrap.pypa.io/get-pip.py && \
  ln /usr/bin/python3.5 /usr/bin/python && \
  python get-pip.py && \
  pip install numpy scipy matplotlib sympy nose pandas sklearn selenium pyvirtualdisplay && \
  rm get-pip.py linux_signing_key.pub && \
  mkdir -p /src/mdup

WORKDIR /src/mdup/
ENTRYPOINT ["python", "app.py"]
VOLUME ["/src/mdup"]

#fix chrome issues with xvfb source -> https://github.com/kfatehi/docker-chrome-xvfb/blob/master/Dockerfile
ENV DISPLAY :99

# Install Xvfb init script
COPY xvfb_init /etc/init.d/xvfb
COPY xvfb-daemon-run /usr/bin/xvfb-daemon-run
# Allow root to execute Google Chrome by replacing launch script
COPY google-chrome-launcher /usr/bin/google-chrome
RUN chmod a+x /etc/init.d/xvfb /usr/bin/xvfb-daemon-run /usr/bin/google-chrome
