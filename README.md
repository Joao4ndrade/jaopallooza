# 🎪 JAOPALLOOZA

O aniversário do João com cara de festival. Um site no estilo dos apps de ingresso (pense na Ingresse), feito pra galera **garantir o ingresso com QR code** e votar no **JAOPALLOOZA Awards**, a premiação mais séria e menos imparcial do ano.

Responsivo de verdade: **sidebar no desktop** e **barra inferior no celular**, com quatro abas:

| Aba | O que tem |
| --- | --- |
| **Evento** | Cartaz, data, horário, local e descrição (tudo “Em breve” até ser definido) + botão **Garanta seu ingresso** |
| **Awards** | Uma categoria por vez, navegando por *swipe*, setas laterais `<` `>` ou setas do teclado. Um voto por categoria, sem volta |
| **Ingresso** | Carteira com o ingresso e o QR code da entrada (ou o botão de garantir, se ainda não tiver) |
| **Conta** | Nome, e-mail, categorias em que concorre, escolha de par (pra categoria de casal), sair da votação, sair da conta e cancelar presença |

**O ingresso é da conta:** quem chega sem conta vê o aviso *“Faça o login ou crie sua conta para garantir seu ingresso”*, e **cada conta garante um único QR code**. A conta tem **nome, e-mail e senha**: o login aceita nome **ou** e-mail, o cadastro avisa na hora se o nome já está em uso e dá pra **recuperar a senha por e-mail**.

---

## ▶️ Rodando no seu PC (Windows, passo a passo)

Você só precisa de **Git** e **Docker Desktop**. O Docker sobe banco, API e site sozinho, sem instalar Python nem Node.

### 1. Instale as ferramentas (uma vez só)

No PowerShell:

```powershell
winget install Git.Git
winget install Docker.DockerDesktop
```

Depois **reinicie o PC** e abra o **Docker Desktop** (ele pode pedir pra ativar o WSL 2; aceite). Espere o ícone da baleia ficar verde/“Engine running”.

### 2. Baixe o projeto

```powershell
cd C:\Projetos
git clone https://github.com/Joao4ndrade/jaopallooza.git
cd jaopallooza
```

### 3. Suba tudo

```powershell
docker compose up --build
```

A primeira vez demora uns minutos (baixa as imagens e instala as dependências). Quando aparecer `Uvicorn running`, abra **<http://localhost:8080>** 🎉

- **Primeira coisa:** crie sua conta com o nome **João**. É ele que vira admin (configurável em `ADMIN_NAMES`).
- Painel da API (admin): <http://localhost:8080/api/docs>
- Pra parar: `Ctrl + C` no terminal. Pra apagar também o banco: `docker compose down -v`.

### 4. (Opcional) Configurações

Copie o arquivo de exemplo e edite o `.env` no Bloco de Notas/VS Code:

```powershell
copy .env.example .env
```

Depois rode `docker compose up --build` de novo. Tudo que dá pra configurar está explicado dentro do arquivo.

> **Testando “esqueci minha senha” sem configurar e-mail:** sem SMTP, o e-mail não é enviado, mas o link aparece no log da API. Rode `docker compose logs api` e copie o link `http://localhost:8080/redefinir-senha?token=...`.

---

## Stack

| Camada | Escolha | Por quê |
| --- | --- | --- |
| Banco | **PostgreSQL 16** | As regras críticas (1 voto por categoria, 1 ingresso por pessoa, nome e e-mail únicos, cascatas ao excluir conta) estão em *constraints* no banco, não só no código |
| API | **Python 3.12+ / FastAPI** + SQLAlchemy 2 + Alembic | Produtivo, validação com Pydantic e Swagger automático em `/api/docs`, que serve de painel de admin |
| Front | **React 19 + Vite + TypeScript + Tailwind CSS 4** | SPA leve. O site é quase todo atrás de login, então SSR (Next.js) seria exagero |
| QR code | `qrcode.react` | Gerado no navegador a partir do código do ingresso |
| Auth | Senha com Argon2 + token JWT | Recuperação de senha por link de uso único enviado via SMTP |

## Estrutura

```
jaopallooza/
├── backend/            # FastAPI
│   ├── app/
│   │   ├── routers/    # auth, event, tickets, awards, me, admin
│   │   ├── services/   # regras do Awards e envio de e-mail
│   │   ├── models.py   # tabelas
│   │   └── schemas.py  # contratos da API
│   ├── alembic/        # migrations (0002 = dados iniciais do evento e categorias)
│   └── tests/          # pytest rodando contra Postgres de verdade
├── web/                # React + Vite
│   └── src/
│       ├── pages/      # Evento, Awards, Ingresso, Conta, Login, Senha, Check-in
│       ├── components/ # AppShell (sidebar/barra), Poster, botões, modal...
│       └── lib/        # cliente da API, auth, formatação
├── deploy/           # produção: Caddyfile, .env de exemplo e script de backup
├── docker-compose.yml       # para rodar no seu PC
├── docker-compose.prod.yml  # para a VPS (HTTPS automático)
└── .github/workflows/ci.yml
```

## 🛠️ Modo desenvolvimento (pra mexer no código com hot reload)

Além do Docker Desktop, instale o [uv](https://docs.astral.sh/uv/) (Python) e o Node 22+:

```powershell
winget install astral-sh.uv
winget install OpenJS.NodeJS.LTS
```

**1. Banco** (na raiz do projeto)

```powershell
docker compose up -d db
```

**2. API** (num terminal)

```powershell
cd backend
uv sync
copy .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**3. Site** (em outro terminal)

```powershell
cd web
npm install
npm run dev
```

Abra <http://localhost:5173>. Salvou um arquivo, a tela atualiza sozinha. O Vite repassa `/api` para a API em `localhost:8000`.

## Configuração

No Docker, as variáveis vão no `.env` da **raiz**; no modo desenvolvimento, no `backend/.env`.

| Variável | Padrão | Pra que serve |
| --- | --- | --- |
| `ADMIN_NAMES` | `João` (no Docker) | Nomes que viram admin, separados por vírgula |
| `JWT_SECRET` | segredo de dev | **Troque em produção** (`python -c "import secrets; print(secrets.token_hex(32))"`). A API avisa no log se esquecer |
| `INVITE_CODE` | vazio | “Senha da festa” para criar conta (veja abaixo) |
| `FRONTEND_URL` | endereço local | Endereço do site, usado no link do e-mail de recuperação |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SECURITY` | vazio | Envio de e-mail (veja abaixo) |
| `DATABASE_URL` | Postgres local | Conexão com o banco. Aceita `postgres://...` de provedores como Render/Railway |
| `CORS_ORIGINS` | endereço local | Origens do front, se front e API estiverem em domínios diferentes |

### 📧 E-mail de recuperação de senha (Gmail)

1. Ative a **verificação em 2 etapas** na sua conta Google.
2. Gere uma **senha de app** em <https://myaccount.google.com/apppasswords> (16 letras).
3. No `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=abcdabcdabcdabcd
SMTP_FROM=JAOPALLOOZA <seuemail@gmail.com>
```

O Gmail aguenta centenas de e-mails por dia, bem mais do que uma festa precisa. Alternativas com plano grátis: Brevo, Resend.

Como funciona por dentro: o link vale **1 hora** e **só funciona uma vez**. O banco guarda só o *hash* do token, e a resposta é sempre a mesma, exista o e-mail ou não (ninguém descobre quem tem conta). Dá pra pedir um novo a cada 60 s, e trocar a senha **desloga os outros aparelhos**.

### 🎟️ Código de convite (`INVITE_CODE`, opcional e desligado por padrão)

Sem ele, qualquer pessoa que achar o site consegue criar conta e garantir **um** ingresso. Na portaria, o check-in mostra o nome do titular, então um desconhecido aparece ali.

Se quiser barrar desconhecidos já no cadastro, defina por exemplo `INVITE_CODE=jaopa2027`: a tela de criar conta passa a pedir esse código, que você passa pra galera **por mensagem** (ele não vai no link). Quem já tem conta não precisa dele.

## Regras do Awards

- Só vota e só concorre **quem garantiu ingresso**.
- **Um voto por categoria**, garantido por constraint no banco. Não dá pra trocar, por isso existe o modal de confirmação.
- **Não vale votar em si mesmo** (nem no próprio casal).
- **Melhor casal:** cada pessoa escolhe seu par na aba Conta. O casal só passa a concorrer quando a escolha é **recíproca**, tipo pedido de namoro 💘. Quem recebe o pedido vê um botão “Confirmar”.
- **Sair da votação** = deixar de concorrer. A pessoa continua votando, os votos que ela recebeu são descartados e quem tinha votado nela ganha o voto de volta. Dá pra voltar a concorrer depois.
- Desfazer um casal ou excluir a conta também devolve os votos a quem votou.
- Os resultados ficam escondidos: só o admin vê, em `GET /api/admin/results`. Suspense até a festa 🏆

## Painel de admin (por enquanto: Swagger)

Acesse `/api/docs`, clique em **Authorize** e entre com seu nome (ou e-mail) e senha. Endpoints:

| Endpoint | Pra quê |
| --- | --- |
| `PUT /api/admin/event` | Preencher data, local etc. quando definir. Só manda o que mudou |
| `GET /api/admin/guests` | Lista de confirmados e quem já fez check-in |
| `GET /api/admin/results` | Ranking de cada categoria |
| `POST /api/admin/categories` | Nova categoria (`kind`: `individual` ou `couple`) |
| `PATCH /api/admin/categories/{id}` | Editar ou desativar (`is_active: false`) uma categoria |
| `POST /api/admin/users/reset-password` | Redefinir a senha de alguém na mão |
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

```powershell
cd backend
uv run pytest            # 43 testes contra Postgres (banco jaopallooza_test)
uv run ruff check .

cd ..\web
npm run lint
npm run build
```

Os testes precisam de um Postgres com o banco `jaopallooza_test` (crie com `docker compose exec db createdb -U postgres jaopallooza_test`). Eles rodam as migrations de verdade, e cada teste roda dentro de uma transação desfeita no fim. Para outro banco, use `TEST_DATABASE_URL`. O GitHub Actions roda tudo isso a cada push.

## 🚀 Colocando no ar (VPS, ex.: Hostinger)

> ⚠️ Na VPS use **sempre** o `docker-compose.prod.yml`. O `docker-compose.yml` comum é só para o seu PC: ele expõe o banco com a senha `postgres` e não tem HTTPS.

O `docker-compose.prod.yml` sobe banco, API, site e o **Caddy**, que cuida do **HTTPS automático** (certificado grátis do Let's Encrypt, renovado sozinho). Só as portas 80 e 443 ficam abertas para a internet.

### 1. Endereço do site

- **Com domínio (recomendado):** no painel onde comprou o domínio (na Hostinger: hPanel → Domínios → DNS), crie um registro **A** com nome `@` apontando para o **IP da VPS**. Leva de minutos a algumas horas para propagar.
- **Sem domínio (grátis, para testar):** use o IP da VPS com traços + `.sslip.io`. Ex.: IP `203.0.113.10` vira `203-0-113-10.sslip.io`. Já funciona com HTTPS, sem configurar nada.

### 2. Preparar a VPS

Use **Ubuntu 24.04** (na Hostinger, o template “Ubuntu 24.04 with Docker” já vem com Docker). No firewall do painel, libere as portas **22, 80 e 443**. Depois, do seu PC:

```bash
ssh root@IP_DA_VPS
```

Se o Docker não veio instalado:

```bash
curl -fsSL https://get.docker.com | sh
```

### 3. Baixar o código (repo privado → *deploy key*)

Na VPS, gere uma chave só para leitura deste repositório:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/jaopallooza -N "" -C "vps-jaopallooza"
cat ~/.ssh/jaopallooza.pub
```

Copie a linha que aparecer e cadastre no GitHub em **Settings → Deploy keys → Add deploy key** do repositório (deixe “Allow write access” **desmarcado**). Depois:

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/jaopallooza" git clone git@github.com:Joao4ndrade/jaopallooza.git /opt/jaopallooza
cd /opt/jaopallooza
git config core.sshCommand "ssh -i ~/.ssh/jaopallooza"
```

### 4. Configurar

```bash
cp deploy/production.env.example .env
openssl rand -hex 32   # rode 2x: um valor para POSTGRES_PASSWORD, outro para JWT_SECRET
nano .env
```

Preencha `DOMAIN`, `POSTGRES_PASSWORD`, `JWT_SECRET` e o SMTP (veja [E-mail de recuperação de senha](#-e-mail-de-recuperação-de-senha-gmail)). Salve com `Ctrl+O`, `Enter`, `Ctrl+X`.

### 5. Subir

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Acompanhe com `docker compose -f docker-compose.prod.yml logs -f` (sai com `Ctrl+C`; o site continua no ar). Em um ou dois minutos, abra `https://SEU_DOMINIO`.

### ✅ Antes de chamar a galera

1. Crie **sua** conta primeiro, com o nome que está em `ADMIN_NAMES`.
2. Preencha data/local em `https://SEU_DOMINIO/api/docs` (`PUT /api/admin/event`), ou deixe “Em breve”.
3. Teste o “Esqueci minha senha” com seu e-mail, pra ter certeza de que o SMTP funciona.
4. Abra o site no celular e garanta seu ingresso pra ver o fluxo completo.
5. Ative o backup (abaixo). Aí é só mandar o link no grupo 🎉

### Backup diário

O `deploy/backup.sh` salva o banco (contas, ingressos e votos) em `backups/`, mantendo 14 dias. Para rodar todo dia às 4h:

```bash
crontab -e
```

E adicione a linha:

```
0 4 * * * /opt/jaopallooza/deploy/backup.sh >> /var/log/jaopallooza-backup.log 2>&1
```

Para restaurar um backup:

```bash
gunzip -c backups/ARQUIVO.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U postgres jaopallooza
```

### Atualizar depois de mudar o código

```bash
cd /opt/jaopallooza
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

As migrations do banco rodam sozinhas quando a API sobe.

## Ideias para depois

- Tela de admin de verdade (resultados com revelação animada na festa 🥁)
- Prazo para encerrar a votação
- Upload de foto de perfil para os indicados
- Mais categorias: *Mais provável de sumir sem avisar*, *Rei/Rainha do karaokê*, *Pior dançarino(a)*, *“Só mais uma” do rolê*
