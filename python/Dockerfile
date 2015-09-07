FROM mitmproxy/mitmproxy

ADD ./main.py /opt/
WORKDIR /opt/

ENTRYPOINT ["/opt/main.py"]

EXPOSE 8080 8081 8105
