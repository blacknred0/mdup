FROM blacknred0/mediacomsmsquota

MAINTAINER Irving Duran <irving.duran@gmail.com>

RUN apt update && apt upgrade -y
RUN mkdir -p /src/email2sms
#COPY main.py main_gather.py localf.py chromedriver_linux64 /src/email2sms/
ENTRYPOINT ["python"]
#CMD ["python", "/src/email2sms/main.py", "chromedriver_linux64"]
VOLUME ["/src/email2sms"]

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
