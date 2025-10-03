FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 80

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["DockerAutotestesEcosystemSwagger.csproj", "."]
RUN dotnet restore "DockerAutotestesEcosystemSwagger.csproj"
COPY . .
WORKDIR "/src"
RUN dotnet build "DockerAutotestesEcosystemSwagger.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "DockerAutotestesEcosystemSwagger.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "DockerAutotestesEcosystemSwagger.dll"]