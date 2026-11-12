# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/dotnet/sdk:11.0@sha256:65f3c7c6a25a239ab3e6719f2896147e7b68242ff2d8818dd70498bde6ef8bea AS build
ARG VERSION="1.0.0"
WORKDIR /workspace
COPY global.json Directory.Build.props Directory.Packages.props ./
COPY src/HelloApi/HelloApi.csproj src/HelloApi/
RUN dotnet restore src/HelloApi/HelloApi.csproj
COPY src/HelloApi src/HelloApi
RUN dotnet publish src/HelloApi/HelloApi.csproj -c Release --no-restore -o /out -p:Version="${VERSION}" -p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:11.0@sha256:bc0d6653979efba491ab3d6f589d691f96c309c3c3ef81325efa6978e7b7f242
LABEL org.opencontainers.image.source="https://github.com/ChristianPresley/agentic-pipelines" \
      org.opencontainers.image.title="hello-api" \
      org.opencontainers.image.licenses="MIT"
WORKDIR /app
COPY --from=build --chown=1654:1654 /out /app
USER 1654:1654
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
ENTRYPOINT ["dotnet", "/app/HelloApi.dll"]
