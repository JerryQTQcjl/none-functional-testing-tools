# Stage 1: Download Gatling
FROM eclipse-temurin:11-jdk AS gatling-setup

RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

RUN curl -L https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/3.10.3/gatling-charts-highcharts-bundle-3.10.3-bundle.zip -o /tmp/gatling.zip \
    && unzip /tmp/gatling.zip -d /opt/ \
    && mv /opt/gatling-charts-highcharts-bundle-3.10.3 /opt/gatling \
    && rm /tmp/gatling.zip \
    && chmod +x /opt/gatling/bin/gatling.sh

# Stage 2: Runtime (needs JDK for Gatling on-the-fly compilation)
FROM eclipse-temurin:11-jdk

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=gatling-setup /opt/gatling /opt/gatling
ENV GATLING_HOME=/opt/gatling
ENV PATH="${GATLING_HOME}/bin:${PATH}"

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY worker_agent.py .
COPY simulation_builder.py .
COPY metrics_collector.py .
COPY templates/ ./templates/
COPY conf/gatling.conf /opt/gatling/conf/gatling.conf

RUN mkdir -p /app/results /app/config /opt/gatling/user-files/simulations

ENV REDIS_URL=redis://redis:6379
ENV GATLING_HOME=/opt/gatling

CMD ["python3", "worker_agent.py"]
