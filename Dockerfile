#dockerfile
FROM arpasmr/python_base
WORKDIR /usr/src/myapp
COPY *.py ./
COPY launch_feed.sh ./
ENV IRIS_USER_ID postgres
ENV IRIS_DB_NAME iris_base
ENV IRIS_DB_HOST 10.10.0.19
ENV http_proxy=http://proxy2.arpa.local:8080
ENV https_proxy=https://proxy2.arpa.local:8080
