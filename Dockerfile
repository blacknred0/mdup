FROM blacknred0/mdup

MAINTAINER Irving Duran <irving.duran@gmail.com>

RUN apt update && apt upgrade -y && apt -y autoremove
RUN mkdir -p /src/mdup
#COPY main.py main_gather.py localf.py chromedriver_linux64 /src/mdup/
ENTRYPOINT ["python"]
#CMD ["python", "/src/mdup/main.py", "chromedriver_linux64"]
VOLUME ["/src/mdup"]

#fix chrome issues with xvfb source -> https://github.com/kfatehi/docker-chrome-xvfb/blob/master/Dockerfile
ENV DISPLAY :99

# Install Xvfb init script
ADD xvfb_init /etc/init.d/xvfb
RUN chmod a+x /etc/init.d/xvfb
ADD xvfb-daemon-run /usr/bin/xvfb-daemon-run
RUN chmod a+x /usr/bin/xvfb-daemon-run

# Allow root to execute Google Chrome by replacing launch script
ADD google-chrome-launcher /usr/bin/google-chrome
RUN chmod a+x /usr/bin/google-chrome
