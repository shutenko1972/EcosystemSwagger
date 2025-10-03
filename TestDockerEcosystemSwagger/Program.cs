using System.Collections.Concurrent;
using Microsoft.OpenApi.Models;
using Swashbuckle.AspNetCore.SwaggerGen;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "🔐 Ai ecosystem test API",
        Version = "1.0.1",
        Description = "<h3><strong>API для аутентификации и проверки функций</strong></h3>" +
                      "<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #3498db;'>" +
                      "<h3 style='color: #2c3e50; margin-top: 0;'>Функциональность:</h3>" +
                      "<ul style='color: #7f8c8d;'>" +
                      "<strong><li>Аутентификация (Auth)</li></strong>" +
                      "<li>Вход пользователя в систему</li>" +
                      "<li>Выход пользователя из системы</li>" +
                      "<li>Проверка валидности сессии</li><br>" +
                      "<strong><li>Чат (Chat)</li></strong>" +
                      "<li>Отправка сообщения в AI-чат</li>" +
                      "<li>Очистка истории чата</li>" +
                      "<li>Копирование текста ответа</li><br>" +
                      "<strong><li>Настройки модели (Settings)</li></strong>" +
                      "<li>Установка параметра температуры AI-модели</li>" +
                      "<li>Установка параметра Top-P AI-модели</li><br>" +
                      "<strong><li>Системные (System)</li></strong>" +
                      "<li>Проверка работоспособности сервера </li>" +
                      "<li>Получение информации о сервере</li>" +
                      "</ul>" +
                      "</div>"
    });

    // Добавляем поддержку form-data
    c.OperationFilter<SwaggerFileOperationFilter>();
});

builder.Services.AddSingleton<ConcurrentDictionary<string, SessionInfo>>();
builder.Services.AddScoped<SessionService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();

// Модели данных
public class LoginRequest
{
    public string Login { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public class LoginResponse
{
    public string Message { get; set; } = string.Empty;
    public string RedirectUrl { get; set; } = string.Empty;
    public string SessionToken { get; set; } = string.Empty;
}

public class ErrorResponse
{
    public string Error { get; set; } = string.Empty;
}

public class LogoutResponse
{
    public string Message { get; set; } = string.Empty;
}

public class SessionInfoResponse
{
    public bool Valid { get; set; }
    public string UserLogin { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
}

public class SessionInfo
{
    public string UserLogin { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime ExpiresAt { get; set; }
}

public class ChatResponse
{
    public string Answer { get; set; } = string.Empty;
}

public class TemperatureResponse
{
    public int Value { get; set; }
}

public class TopPResponse
{
    public int Value { get; set; }
}

public class ClearResponse
{
    public string Message { get; set; } = string.Empty;
}

public class CopyResponse
{
    public string Message { get; set; } = string.Empty;
}

public class HealthResponse
{
    public string Status { get; set; } = string.Empty;
}

public class ServerInfoResponse
{
    public string Name { get; set; } = string.Empty;
    public string Version { get; set; } = string.Empty;
}

// Сервис для работы с сессиями
public class SessionService
{
    private readonly ConcurrentDictionary<string, SessionInfo> _sessions;

    public SessionService(ConcurrentDictionary<string, SessionInfo> sessions)
    {
        _sessions = sessions;
    }

    public string CreateSession(string userLogin)
    {
        var sessionToken = Guid.NewGuid().ToString();
        var sessionInfo = new SessionInfo
        {
            UserLogin = userLogin,
            CreatedAt = DateTime.Now,
            ExpiresAt = DateTime.Now.AddHours(1)
        };

        _sessions[sessionToken] = sessionInfo;
        return sessionToken;
    }

    public bool ValidateSession(string sessionToken)
    {
        if (string.IsNullOrEmpty(sessionToken) || !_sessions.TryGetValue(sessionToken, out var session))
            return false;

        if (session.ExpiresAt < DateTime.Now)
        {
            _sessions.TryRemove(sessionToken, out _);
            return false;
        }

        return true;
    }

    public SessionInfo GetSession(string sessionToken)
    {
        if (_sessions.TryGetValue(sessionToken, out var session))
            return session;

        throw new UnauthorizedAccessException("Invalid session");
    }

    public void RemoveSession(string sessionToken)
    {
        _sessions.TryRemove(sessionToken, out _);
    }
}

// Контроллер аутентификации
[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly SessionService _sessionService;

    public AuthController(SessionService sessionService)
    {
        _sessionService = sessionService;
    }

    [HttpPost("login/Вход пользователя в систему")]
    [Tags("Auth")]
    public IActionResult Login([FromForm] LoginRequest request)
    {
        if (request.Login != "v_shutenko" || request.Password != "8nEThznM")
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid credentials" });
        }

        var sessionToken = _sessionService.CreateSession(request.Login);

        return Ok(new LoginResponse
        {
            Message = "Success",
            RedirectUrl = "/request/model.html",
            SessionToken = sessionToken
        });
    }

    [HttpPost("logout/Выход пользователя из системы")]
    [Tags("Auth")]
    public IActionResult Logout([FromForm] string sessionToken)
    {
        _sessionService.RemoveSession(sessionToken);
        return Ok(new LogoutResponse { Message = "Logged out" });
    }

    [HttpPost("check-session/Проверка валидности сессии")]
    [Tags("Auth")]
    public IActionResult CheckSession([FromForm] string sessionToken)
    {
        try
        {
            var session = _sessionService.GetSession(sessionToken);
            return Ok(new SessionInfoResponse
            {
                Valid = true,
                UserLogin = session.UserLogin,
                ExpiresAt = session.ExpiresAt
            });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }
}

// Контроллер чата
[ApiController]
[Route("api/chat")]
public class ChatController : ControllerBase
{
    private readonly SessionService _sessionService;

    public ChatController(SessionService sessionService)
    {
        _sessionService = sessionService;
    }

    [HttpPost("send/Отправка сообщения в AI-чат")]
    [Tags("Chat")]
    public IActionResult SendMessage([FromForm] string message, [FromForm] string sessionToken)
    {
        try
        {
            _sessionService.GetSession(sessionToken);

            string response;
            if (message.ToLower().Contains("привет"))
            {
                response = "Привет! Чем могу помочь?";
            }
            else if (message.ToLower().Contains("погода"))
            {
                response = "Погода хорошая";
            }
            else if (message.ToLower().Contains("время"))
            {
                response = $"Сейчас {DateTime.Now:HH:mm}";
            }
            else
            {
                response = "Получил ваш запрос";
            }

            return Ok(new ChatResponse { Answer = response });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }

    [HttpPost("clear/Очистка истории чата")]
    [Tags("Chat")]
    public IActionResult ClearChat([FromForm] string sessionToken)
    {
        try
        {
            _sessionService.GetSession(sessionToken);
            return Ok(new ClearResponse { Message = "Chat cleared" });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }

    [HttpPost("copy/Копирование текста ответа")]
    [Tags("Chat")]
    public IActionResult CopyText([FromForm] string text, [FromForm] string sessionToken)
    {
        try
        {
            _sessionService.GetSession(sessionToken);
            return Ok(new CopyResponse { Message = "Text copied" });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }
}

// Контроллер настроек
[ApiController]
[Route("api/settings")]
public class SettingsController : ControllerBase
{
    private readonly SessionService _sessionService;

    public SettingsController(SessionService sessionService)
    {
        _sessionService = sessionService;
    }

    [HttpPost("temperature/Установка параметра температуры AI-модели")]
    [Tags("Settings")]
    public IActionResult SetTemperature([FromForm] int value, [FromForm] string sessionToken)
    {
        try
        {
            _sessionService.GetSession(sessionToken);

            if (value < 0 || value > 200)
            {
                return BadRequest(new ErrorResponse { Error = "Value must be between 0 and 200" });
            }

            return Ok(new TemperatureResponse { Value = value });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }

    [HttpPost("topp/Установка параметра Top-P AI-модели")]
    [Tags("Settings")]
    public IActionResult SetTopP([FromForm] int value, [FromForm] string sessionToken)
    {
        try
        {
            _sessionService.GetSession(sessionToken);

            if (value < 0 || value > 100)
            {
                return BadRequest(new ErrorResponse { Error = "Value must be between 0 and 100" });
            }

            return Ok(new TopPResponse { Value = value });
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new ErrorResponse { Error = "Invalid session" });
        }
    }
}

// Системный контроллер
[ApiController]
[Route("api")]
public class SystemController : ControllerBase
{
    [HttpGet("health/Проверка работоспособности сервера")]
    [Tags("System")]
    public IActionResult HealthCheck()
    {
        return Ok(new HealthResponse { Status = "OK" });
    }

    [HttpGet("info/Получение информации о сервере")]
    [Tags("System")]
    public IActionResult ServerInfo()
    {
        return Ok(new ServerInfoResponse
        {
            Name = "AI Service",
            Version = "1.0.0"
        });
    }

    [HttpGet("Root/Корневой эндпоинт")]
    public IActionResult Root()
    {
        return Ok(new { message = "Service API" });
    }
}

// Фильтр для Swagger для поддержки form-data
public class SwaggerFileOperationFilter : IOperationFilter
{
    public void Apply(OpenApiOperation operation, OperationFilterContext context)
    {
        var formContent = context.ApiDescription.ParameterDescriptions
            .Any(p => p.Source.Id == "Form");

        if (formContent)
        {
            operation.RequestBody = new OpenApiRequestBody
            {
                Content =
                {
                    ["application/x-www-form-urlencoded"] = new OpenApiMediaType
                    {
                        Schema = new OpenApiSchema
                        {
                            Type = "object",
                            Properties = context.ApiDescription.ParameterDescriptions
                                .ToDictionary(
                                    p => p.Name,
                                    p => new OpenApiSchema { Type = "string" }
                                )
                        }
                    }
                }
            };
        }
    }
}

// Атрибут Tags для Swagger
public class TagsAttribute : Attribute
{
    public string[] Tags { get; }

    public TagsAttribute(params string[] tags)
    {
        Tags = tags;
    }
}