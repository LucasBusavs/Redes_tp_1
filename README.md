// ...existing code...
# Redes_tp_1

Projeto de exemplo de API de chat construída com FastAPI, SQLAlchemy, PostgreSQL e Redis (WebSockets).

## Sumário
- [Requisitos](#requisitos)
- [Configuração](#configura%C3%A7%C3%A3o)
- [Executar com Docker Compose (recomendado)](#executar-com-docker-compose-recomendado)
- [Executar localmente sem Docker](#executar-localmente-sem-docker)
- [Endpoints principais / WebSockets](#endpoints-principais--websockets)
- [Observações](#observa%C3%A7%C3%B5es)

## Requisitos
- Docker & Docker Compose (recomendado) OU Python 3.11+ e Postgres + Redis instalados localmente.
- Variáveis de ambiente — copie o exemplo e ajuste: [.env.example](.env.example)

## Configuração
1. Duplique o arquivo de exemplo de variáveis de ambiente:
   ```sh
   cp .env.example .env
   ```
   Edite `.env` conforme necessário (usuário/senha do Postgres, DATABASE_URL, SECRET_KEY, etc).

2. Verifique as dependências em [requirements.txt](requirements.txt).

## Executar com Docker Compose (recomendado)
1. Construir e subir containers:
   ```sh
   docker-compose up --build
   ```
   - O serviço `api` usa o script [wait-for-db.sh](wait-for-db.sh) para aguardar o Postgres.
   - Serviços disponíveis por padrão:
     - API: http://localhost:8000
     - Postgres: 5432
     - Redis: 6379

2. Documentação interativa OpenAPI:
   - Abra http://localhost:8000/docs

Arquivos relevantes: [docker-compose.yml](docker-compose.yml), [Dockerfile](Dockerfile), [wait-for-db.sh](wait-for-db.sh).

## Executar localmente sem Docker
1. Criar ambiente virtual e instalar dependências:
   ```sh
   python -m venv .venv
   source .venv/bin/activate   # ou .venv\Scripts\activate no Windows
   pip install -r requirements.txt
   ```

2. Garanta que um PostgreSQL e Redis estejam disponíveis e que `DATABASE_URL` em `.env` aponte para o banco. O projeto cria as tabelas automaticamente ao iniciar (veja [`app.main.app`](app/main.py)).

3. Iniciar a aplicação:
   ```sh
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Endpoints principais / WebSockets
- Rotas REST (ver implementações):
  - Usuários: [`app/routers/users.py`](app/routers/users.py)
    - POST /users — criar usuário
    - POST /users/login — login (OAuth2 password)
    - GET /users — listar (autenticado)
    - GET /users/{user_id} — obter usuário (autenticado)
  - Salas: [`app/routers/rooms.py`](app/routers/rooms.py)
    - POST /rooms — criar sala
    - DELETE /rooms/{room_id} — remover sala
    - POST /rooms/{room_id}/enter — entrar na sala
    - DELETE /rooms/{room_id}/leave — sair da sala
    - POST /rooms/{room_id}/messages — enviar mensagem para sala
    - GET /rooms/{room_id}/messages — listar mensagens da sala
  - Mensagens diretas: [`app/routers/messages.py`](app/routers/messages.py)
    - POST /messages/direct/{receiver_id} — enviar DM
    - GET /messages/direct/{receiver_id} — listar DMs

- WebSocket:
  - Sala: `/ws/rooms/{room_id}` — implementação em [`app.main.websocket_endpoint`](app/main.py)
  - Mensagens diretas: `/ws/dm` — implementação em [`app.main.dm_websocket`](app/main.py)

Autenticação / Token:
- A validação e extração do usuário a partir do token estão em [`app/auth_utils.py`](app/auth_utils.py). A dependência de DB é provida por [`app.db.get_db`](app/db.py).

## Observações
- O projeto cria as tabelas automaticamente em tempo de execução (linha com `Base.metadata.create_all(bind=engine)` em [`app/main.py`](app/main.py)) — útil para protótipos.
- Para produção, recomenda-se aplicar migrações (Alembic), rotinas de segurança para SECRET_KEY e variáveis sensíveis, e configuração adequada de volumes/backups para Postgres.
- Arquivos importantes:
  - [.env.example](.env.example)
  - [requirements.txt](requirements.txt)
  - [docker-compose.yml](docker-compose.yml)
  - [Dockerfile](Dockerfile)
  - [wait-for-db.sh](wait-for-db.sh)
  - Código da API: [app/main.py](app/main.py), [app/db.py](app/db.py), [app/auth_utils.py](app/auth_utils.py), [app/routers/users.py](app/routers/users.py), [app/routers/rooms.py](app/routers/rooms.py), [app/routers/messages.py](app/routers/messages.py)
