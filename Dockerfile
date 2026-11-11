# syntax=docker/dockerfile:1.7
FROM maven:3.9-eclipse-temurin-26@sha256:b2c1ad85954592f9928e84327c65201f308ad9b5d8ed7d5b823717c97bf23fbb AS build
ARG VERSION=""
WORKDIR /workspace
COPY pom.xml ./
COPY config ./config
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 \
    if [ -n "$VERSION" ]; then \
      mvn -B -ntp org.codehaus.mojo:versions-maven-plugin:2.25.1:set -DnewVersion="$VERSION" -DgenerateBackupPoms=false; \
    fi \
    && mvn -B -ntp -DskipTests -Dcheckstyle.skip -Dpmd.skip -Dspotbugs.skip -Djacoco.skip=true package

FROM eclipse-temurin:25-jre-noble@sha256:a98128a57de944a72bd31fbc79b898edd5a5864d3652071d5bbd2160ab7d7dce
LABEL org.opencontainers.image.source="https://github.com/ChristianPresley/agentic-pipelines" \
      org.opencontainers.image.title="hello-api" \
      org.opencontainers.image.licenses="MIT"
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade apt libapt-pkg6.0t64 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=build --chown=10001:10001 /workspace/target/hello-api-*.jar /app/app.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
