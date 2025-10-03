from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import logging
import sys
import webbrowser
import threading
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Хранилище сессий (в памяти)
active_sessions = {}

class APIHandler(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def _send_response(self, data, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self._set_cors_headers()
        self.end_headers()
        if content_type == 'application/json':
            self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))
        else:
            self.wfile.write(data.encode('utf-8'))
    
    def _get_form_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        
        post_data = self.rfile.read(content_length).decode('utf-8')
        if self.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return parse_qs(post_data)
        return {}
    
    def _get_session(self, token):
        if token not in active_sessions:
            return None
        session = active_sessions[token]
        if datetime.now() > session["expiresAt"]:
            del active_sessions[token]
            return None
        return session
    
    def _require_auth(self, form_data):
        session_token = form_data.get('sessionToken', [None])[0]
        if not session_token or not self._get_session(session_token):
            self._send_response({"error": "Invalid session"}, 401)
            return False
        return True

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self._send_swagger_ui()
        
        elif parsed_path.path == '/swagger.json':
            self._send_swagger_spec()
        
        elif parsed_path.path == '/api/health':
            self._send_response({"status": "OK"})
        
        elif parsed_path.path == '/api/info':
            self._send_response({
                "name": "AI Service", 
                "version": "1.0.0"
            })
        
        elif parsed_path.path == '/api/Root':
            self._send_response({"message": "Service API"})
        
        elif parsed_path.path == '/api/profile':
            # Проверяем сессию через query параметры
            query_params = parse_qs(parsed_path.query)
            session_token = query_params.get('sessionToken', [None])[0]
            if not session_token or not self._get_session(session_token):
                self._send_response({"error": "Invalid session"}, 401)
                return
            
            self._send_response({
                "username": "Vitaliy Shutenko",
                "email": "v_shutenko@example.com",
                "role": "User"
            })
        
        elif parsed_path.path == '/api/chat/history':
            # Проверяем сессию через query параметры
            query_params = parse_qs(parsed_path.query)
            session_token = query_params.get('sessionToken', [None])[0]
            if not session_token or not self._get_session(session_token):
                self._send_response({"error": "Invalid session"}, 401)
                return
            
            self._send_response({
                "messages": [
                    {"id": 1, "text": "Hello, how are you?", "type": "user", "timestamp": "2024-01-15T10:30:00"},
                    {"id": 2, "text": "I'm doing well, thank you!", "type": "assistant", "timestamp": "2024-01-15T10:30:05"}
                ]
            })
        
        else:
            self._send_response({"error": "Endpoint not found"}, 404)

    def _send_swagger_ui(self):
        """Отправка Swagger UI с включенной кнопкой Try it out"""
        swagger_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🔐 Ai ecosystem test API</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; background: #fafafa; }
        .swagger-ui .info h1 { color: #2c3e50; }
        .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch']
            });
            window.ui = ui;
        }
    </script>
</body>
</html>
        """
        self._send_response(swagger_html, content_type='text/html')

    def _send_swagger_spec(self):
        """Swagger спецификация как в C# версии"""
        swagger_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "🔐 Ai ecosystem test API",
                "version": "1.0.1",
                "description": "<h3><strong>API для аутентификации и проверки функций</strong></h3>" +
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
                              "<li>Копирование текста ответа</li>" +
                              "<li>Обновление сообщения</li>" +
                              "<li>Получение истории чата</li><br>" +
                              "<strong><li>Настройки модели (Settings)</li></strong>" +
                              "<li>Установка параметра температуры AI-модели</li>" +
                              "<li>Установка параметра Top-P AI-модели</li><br>" +
                              "<strong><li>Профиль (Profile)</li></strong>" +
                              "<li>Получение информации о профиле</li><br>" +
                              "<strong><li>Системные (System)</li></strong>" +
                              "<li>Проверка работоспособности сервера </li>" +
                              "<li>Получение информации о сервере</li>" +
                              "</ul>" +
                              "</div>"
            },
            "servers": [
                {
                    "url": f"http://localhost:{self.server.server_port}",
                    "description": "Локальный сервер"
                }
            ],
            "paths": {
                "/api/auth/login": {
                    "post": {
                        "tags": ["Auth"],
                        "summary": "Вход пользователя в систему",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "Login": {"type": "string"},
                                            "Password": {"type": "string"}
                                        },
                                        "required": ["Login", "Password"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Успешный вход",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/LoginResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверные учетные данные",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/auth/logout": {
                    "post": {
                        "tags": ["Auth"],
                        "summary": "Выход пользователя из системы",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Успешный выход",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/LogoutResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/auth/check-session": {
                    "post": {
                        "tags": ["Auth"],
                        "summary": "Проверка валидности сессии",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Информация о сессии",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/SessionInfoResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat/send": {
                    "post": {
                        "tags": ["Chat"],
                        "summary": "Отправка сообщения в AI-чат",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["message", "sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Ответ AI",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ChatResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat/clear": {
                    "post": {
                        "tags": ["Chat"],
                        "summary": "Очистка истории чата",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "История очищена",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ClearResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat/copy": {
                    "post": {
                        "tags": ["Chat"],
                        "summary": "Копирование текста ответа",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["text", "sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Текст скопирован",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/CopyResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat/update": {
                    "put": {
                        "tags": ["Chat"],
                        "summary": "Обновление сообщения в чате",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "messageId": {"type": "string"},
                                            "newMessage": {"type": "string"},
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["messageId", "newMessage", "sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Сообщение обновлено",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/UpdateResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat/history": {
                    "get": {
                        "tags": ["Chat"],
                        "summary": "Получение истории чата",
                        "parameters": [
                            {
                                "name": "sessionToken",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "История чата",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ChatHistoryResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/settings/temperature": {
                    "post": {
                        "tags": ["Settings"],
                        "summary": "Установка параметра температуры AI-модели",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "value": {"type": "integer", "minimum": 0, "maximum": 200},
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["value", "sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Температура установлена",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/TemperatureResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/settings/topp": {
                    "post": {
                        "tags": ["Settings"],
                        "summary": "Установка параметра Top-P AI-модели",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "value": {"type": "integer", "minimum": 0, "maximum": 100},
                                            "sessionToken": {"type": "string"}
                                        },
                                        "required": ["value", "sessionToken"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Top-P установлен",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/TopPResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/profile": {
                    "get": {
                        "tags": ["Profile"],
                        "summary": "Получение информации о профиле пользователя",
                        "parameters": [
                            {
                                "name": "sessionToken",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Информация о профиле",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ProfileResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Неверная сессия",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/health": {
                    "get": {
                        "tags": ["System"],
                        "summary": "Проверка работоспособности сервера",
                        "responses": {
                            "200": {
                                "description": "Статус сервера",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HealthResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/info": {
                    "get": {
                        "tags": ["System"],
                        "summary": "Получение информации о сервере",
                        "responses": {
                            "200": {
                                "description": "Информация о сервере",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ServerInfoResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/Root": {
                    "get": {
                        "tags": ["System"],
                        "summary": "Корневой эндпоинт",
                        "responses": {
                            "200": {
                                "description": "Сообщение сервиса",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "LoginResponse": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "redirectUrl": {"type": "string"},
                            "sessionToken": {"type": "string"}
                        }
                    },
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    },
                    "LogoutResponse": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    },
                    "SessionInfoResponse": {
                        "type": "object",
                        "properties": {
                            "valid": {"type": "boolean"},
                            "userLogin": {"type": "string"},
                            "expiresAt": {"type": "string", "format": "date-time"}
                        }
                    },
                    "ChatResponse": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"}
                        }
                    },
                    "TemperatureResponse": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer"}
                        }
                    },
                    "TopPResponse": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer"}
                        }
                    },
                    "ClearResponse": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    },
                    "CopyResponse": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    },
                    "UpdateResponse": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "messageId": {"type": "string"},
                            "newMessage": {"type": "string"}
                        }
                    },
                    "ChatHistoryResponse": {
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "text": {"type": "string"},
                                        "type": {"type": "string"},
                                        "timestamp": {"type": "string", "format": "date-time"}
                                    }
                                }
                            }
                        }
                    },
                    "ProfileResponse": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "role": {"type": "string"}
                        }
                    },
                    "HealthResponse": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"}
                        }
                    },
                    "ServerInfoResponse": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "version": {"type": "string"}
                        }
                    }
                }
            }
        }
        self._send_response(swagger_spec)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        form_data = self._get_form_data()
        
        try:
            # Аутентификация
            if parsed_path.path == '/api/auth/login':
                login = form_data.get('Login', [None])[0]
                password = form_data.get('Password', [None])[0]
                
                if login != "v_shutenko" or password != "8nEThznM":
                    self._send_response({"error": "Invalid credentials"}, 401)
                    return
                
                session_token = str(uuid.uuid4())
                active_sessions[session_token] = {
                    "userLogin": login,
                    "expiresAt": datetime.now() + timedelta(hours=1)
                }
                
                self._send_response({
                    "message": "Success",
                    "redirectUrl": "/request/model.html",
                    "sessionToken": session_token
                })
            
            elif parsed_path.path == '/api/auth/logout':
                session_token = form_data.get('sessionToken', [None])[0]
                if session_token in active_sessions:
                    del active_sessions[session_token]
                self._send_response({"message": "Logged out"})
            
            elif parsed_path.path == '/api/auth/check-session':
                session_token = form_data.get('sessionToken', [None])[0]
                session = self._get_session(session_token)
                
                if not session:
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                self._send_response({
                    "valid": True,
                    "userLogin": session["userLogin"],
                    "expiresAt": session["expiresAt"]
                })
            
            # Функции чата
            elif parsed_path.path == '/api/chat/send':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                message = form_data.get('message', [None])[0]
                
                # Простой ответ
                if message and "привет" in message.lower():
                    response = "Привет! Чем могу помочь?"
                elif message and "погода" in message.lower():
                    response = "Погода хорошая"
                elif message and "время" in message.lower():
                    response = f"Сейчас {datetime.now().strftime('%H:%M')}"
                elif message and "hello" in message.lower():
                    response = "Hello! How can I assist you today?"
                elif message and "weather" in message.lower():
                    response = "The weather is nice today"
                elif message and "capital of france" in message.lower():
                    response = "The capital of France is Paris"
                elif message and "artificial intelligence" in message.lower():
                    response = "Artificial Intelligence is the simulation of human intelligence processes by machines"
                else:
                    response = "Получил ваш запрос"
                
                self._send_response({"answer": response})
            
            elif parsed_path.path == '/api/chat/clear':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                self._send_response({"message": "Chat cleared"})
            
            elif parsed_path.path == '/api/chat/copy':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                self._send_response({"message": "Text copied"})
            
            # Настройки модели
            elif parsed_path.path == '/api/settings/temperature':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                value = int(form_data.get('value', [0])[0])
                if value < 0 or value > 200:
                    self._send_response({"error": "Value must be between 0 and 200"}, 400)
                    return
                
                self._send_response({"value": value})
            
            elif parsed_path.path == '/api/settings/topp':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                value = int(form_data.get('value', [0])[0])
                if value < 0 or value > 100:
                    self._send_response({"error": "Value must be between 0 and 100"}, 400)
                    return
                
                self._send_response({"value": value})
            
            else:
                self._send_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self._send_response({"error": "Internal server error"}, 500)

    def do_PUT(self):
        """Обработка PUT запросов"""
        parsed_path = urlparse(self.path)
        form_data = self._get_form_data()
        
        try:
            if parsed_path.path == '/api/chat/update':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                message_id = form_data.get('messageId', [None])[0]
                new_message = form_data.get('newMessage', [None])[0]
                
                self._send_response({
                    "message": "Message updated",
                    "messageId": message_id,
                    "newMessage": new_message
                })
            
            else:
                self._send_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            logger.error(f"Error processing PUT request: {e}")
            self._send_response({"error": "Internal server error"}, 500)

    def do_DELETE(self):
        """Обработка DELETE запросов"""
        parsed_path = urlparse(self.path)
        form_data = self._get_form_data()
        
        try:
            if parsed_path.path == '/api/chat/message':
                session_token = form_data.get('sessionToken', [None])[0]
                if not session_token or not self._get_session(session_token):
                    self._send_response({"error": "Invalid session"}, 401)
                    return
                
                message_id = form_data.get('messageId', [None])[0]
                
                self._send_response({
                    "message": "Message deleted",
                    "messageId": message_id
                })
            
            else:
                self._send_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            logger.error(f"Error processing DELETE request: {e}")
            self._send_response({"error": "Internal server error"}, 500)

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

def open_browser():
    """Функция для открытия браузера"""
    time.sleep(2)
    url = "http://localhost:8000"
    webbrowser.open(url)
    print(f"🌐 Браузер открыт: {url}")

def run_server():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    
    print("=" * 60)
    print("🔐 AI Ecosystem Test API Server")
    print("=" * 60)
    print(f"🚀 Сервер запущен: http://localhost:{port}")
    print(f"📚 Swagger UI: http://localhost:{port}")
    print("=" * 60)
    print("Доступные эндпоинты:")
    print("POST /api/auth/login")
    print("POST /api/auth/logout") 
    print("POST /api/auth/check-session")
    print("POST /api/chat/send")
    print("POST /api/chat/clear")
    print("POST /api/chat/copy")
    print("PUT  /api/chat/update")
    print("GET  /api/chat/history")
    print("DELETE /api/chat/message")
    print("POST /api/settings/temperature")
    print("POST /api/settings/topp")
    print("GET  /api/profile")
    print("GET  /api/health")
    print("GET  /api/info")
    print("GET  /api/Root")
    print("=" * 60)
    print("🔄 Открываю браузер автоматически...")
    print("=" * 60)
    print("👤 Логин: v_shutenko")
    print("🔑 Пароль: 8nEThznM")
    print("=" * 60)
    
    # Запускаем открытие браузера в отдельном потоке
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")

if __name__ == "__main__":
    run_server()