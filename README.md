# 🎪 JAOPALLOOZA

O aniversário do João com cara de festival. Um site no estilo dos apps de ingresso (pense na Ingresse), feito pra galera **garantir o ingresso com QR code** e votar no **JAOPALLOOZA Awards**, a premiação mais séria e menos imparcial do ano.

Responsivo de verdade: **sidebar no desktop** e **barra inferior no celular**, com quatro abas:

| Aba | O que tem |
| --- | --- |
| **Evento** | Cartaz, data, horário, local e descrição (tudo “Em breve” até ser definido) + botão **Garanta seu ingresso** |
| **Awards** | Uma categoria por vez, navegando por *swipe*, setas laterais `<` `>` ou setas do teclado. Um voto por categoria, sem volta |
| **Ingresso** | Carteira com o ingresso e o QR code da entrada (ou o botão de garantir, se ainda não tiver) |
| **Conta** | Nome, categorias em que concorre, escolha de par (pra categoria de casal), sair da votação, sair da conta e cancelar presença |

## Stack

| Camada | Escolha | Por quê |
| --- | --- | --- |
| Banco | **PostgreSQL 16** | Pedido do dono da festa 😄. As regras críticas (1 voto por categoria, 1 ingresso por pessoa, cascatas ao excluir conta) estão em *constraints* no banco, não só no código |
| API | **Python 3.12+ / FastAPI** + SQLAlchemy 2 + Alembic | Produtivo, validação com Pydantic e Swagger automático em `/api/docs`, que serve de painel de admin |
| Front | **React 19 + Vite + TypeScript + Tailwind CSS 4** | SPA leve. O site é quase todo atrás de login, então SSR (Next.js) seria exagero |
| QR code | `qrcode.react` | Gerado no navegador a partir do código do ingresso |
| Auth | Nome + senha (Argon2) e token JWT | Do jeito pedido: sem e-mail |

## Estrutura

```
jaopallooza/
├── backend/            # FastAPI
│   ├── app/
│   │   ├── routers/    # auth, event, tickets, awards, me, admin
│   │   ├── services/   # regras do Awards (votos, casais, opt-out)
│   │   ├── models.py   # tabelas
│   │   └── schemas.py  # contratos da API
│   ├── alembic/        # migrations (0002 = dados iniciais do evento e categorias)
│   └── tests/          # pytest rodando contra Postgres de verdade
├── web/                # React + Vite
│   └── src/
│       ├── pages/      # Evento, Awards, Ingresso, Conta, Login, Check-in
│       ├── components/ # AppShell (sidebar/barra), Poster, botões, modal...
│       └── lib/        # cliente da API, auth, formatação
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Rodando localmente

Pré-requisitos: [Docker Desktop](https://www.docker.com/products/docker-desktop/), [uv](https://docs.astral.sh/uv/) (gerenciador Python) e Node 22+.

### Opção 1: tudo no Docker (mais rápido)

```bash
docker compose up --build
```

Abra <http://localhost:8080>. A API fica em <http://localhost:8000/api/docs>.

### Opção 2: modo desenvolvimento (hot reload)

**1. Banco**

```bash
docker compose up -d db
```

**2. API** (em `backend/`)

```bash
cd backend
uv sync
copy .env.example .env        # no Linux/macOS: cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**3. Front** (em `web/`, outro terminal)

```bash
cd web
npm install
npm run dev
```

Abra <http://localhost:5173>. O Vite repassa `/api` para a API em `localhost:8000`.

> 💡 **Primeiro passo depois de subir:** crie sua conta com o nome que está em `ADMIN_NAMES` (padrão: `João`) **antes** de divulgar o link. Quem se cadastra com esse nome vira admin.

## Configuração (`backend/.env`)

| Variável | Padrão | Pra que serve |
| --- | --- | --- |
| `DATABASE_URL` | Postgres local | Conexão com o banco. Aceita `postgres://...` de provedores como Render/Railway |
| `JWT_SECRET` | segredo de dev | **Troque em produção** (`python -c "import secrets; print(secrets.token_hex(32))"`). A API avisa no log se esquecer |
| `ADMIN_NAMES` | vazio | Nomes que viram admin, separados por vírgula |
| `INVITE_CODE` | vazio | Se preenchido, o cadastro exige o código. Compartilhe o link como `https://site/?convite=CODIGO` que ele é preenchido sozinho |
| `CORS_ORIGINS` | `http://localhost:5173` | Origens do front, se front e API estiverem em domínios diferentes |

No front, `VITE_API_URL` (opcional) aponta para a API quando ela não está no mesmo domínio (padrão: `/api`).

## Regras do Awards

- Só vota e só concorre **quem garantiu ingresso**.
- **Um voto por categoria**, garantido por constraint no banco. Não dá pra trocar, por isso existe o modal de confirmação.
- **Não vale votar em si mesmo** (nem no próprio casal).
- **Melhor casal:** cada pessoa escolhe seu par na aba Conta. O casal só passa a concorrer quando a escolha é **recíproca**, tipo pedido de namoro 💘. Quem recebe o pedido vê um botão “Confirmar”.
- **Sair da votação** = deixar de concorrer. A pessoa continua votando, os votos que ela recebeu são descartados e quem tinha votado nela ganha o voto de volta. Dá pra voltar a concorrer depois.
- Desfazer um casal ou excluir a conta também devolve os votos a quem votou.
- Os resultados ficam escondidos: só o admin vê, em `GET /api/admin/results`. Suspense até a festa 🏆

## Painel de admin (por enquanto: Swagger)

Acesse `/api/docs`, clique em **Authorize** e entre com seu nome e senha. Endpoints:

| Endpoint | Pra quê |
| --- | --- |
| `PUT /api/admin/event` | Preencher data, local etc. quando definir. Só manda o que mudou |
| `GET /api/admin/guests` | Lista de confirmados e quem já fez check-in |
| `GET /api/admin/results` | Ranking de cada categoria |
| `POST /api/admin/categories` | Nova categoria (`kind`: `individual` ou `couple`) |
| `PATCH /api/admin/categories/{id}` | Editar ou desativar (`is_active: false`) uma categoria |
| `POST /api/admin/users/reset-password` | Pra quem esqueceu a senha (não tem e-mail, lembra?) |
| `POST /api/admin/tickets/{code}/check-in` | Check-in manual |

Exemplo de `PUT /api/admin/event`:

```json
{
  "starts_at": "2027-03-20T20:00:00-03:00",
  "venue_name": "Usina Cultural",
  "city": "Sorocaba, SP",
  "maps_url": "https://maps.app.goo.gl/..."
}
```

**Check-in na portaria:** o QR code do ingresso aponta para `/checkin/<código>`. Escaneie com a câmera do celular logado como admin e confirme a entrada com um toque. Se escanear duas vezes, o site avisa que a pessoa já entrou.

## Testes

```bash
cd backend
uv run pytest            # 31 testes contra Postgres (usa o banco jaopallooza_test)
uv run ruff check .

cd ../web
npm run lint
npm run build
```

Os testes rodam as migrations de verdade e cada teste roda dentro de uma transação desfeita no fim. Para outro banco, use `TEST_DATABASE_URL`.

## Deploy (sugestão)

- **Banco:** [Neon](https://neon.tech) ou [Supabase](https://supabase.com), ambos com plano grátis.
- **API:** [Render](https://render.com) ou [Railway](https://railway.app) usando o `backend/Dockerfile`, que já roda as migrations ao subir.
- **Front:** o `web/Dockerfile` (nginx com proxy de `/api`), ou Vercel/Netlify com `VITE_API_URL` apontando para a API e `CORS_ORIGINS` configurado.

## Ideias para depois

- Tela de admin de verdade (resultados com revelação animada na festa 🥁)
- Prazo para encerrar a votação
- Upload de foto de perfil para os indicados
- Mais categorias: *Mais provável de sumir sem avisar*, *Rei/Rainha do karaokê*, *Pior dançarino(a)*, *“Só mais uma” do rolê*
