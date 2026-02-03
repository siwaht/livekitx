# LiveKit Voice Agent

A simple LiveKit voice agent using STT (AssemblyAI), LLM (OpenAI), and TTS (Cartesia) via LiveKit Inference. The agent greets users and answers questions conversationally.

## Code overview

- **`main.py`** – Agent server: registers the `simple-agent` and runs the voice pipeline. Uses explicit dispatch (`agent_name="simple-agent"`), so the agent only joins when a room requests it (via token room config or dispatch API).
- **`token_server.py`** – Small HTTP server that issues access tokens with **agent dispatch**: when a user joins with this token, LiveKit dispatches `simple-agent` to the room.
- **`simple-videochat.html`** – Web client: connect to a room with a token and optional LiveKit URL.

**Fixes applied:** Removed unused `livekit.rtc` import in `main.py` and fixed the Dockerfile typo (`pplication` → `application`).

## Prerequisites

- Python 3.13+
- A LiveKit server (e.g. [LiveKit Cloud](https://cloud.livekit.io) or self-hosted)
- Credentials in `.env` or `.env.local` (see below):
  - `LIVEKIT_URL` – e.g. `wss://your-project.livekit.cloud`
  - `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`
  - `OPENAI_API_KEY` (used by the agent’s LLM)

LiveKit Inference (used for AssemblyAI STT and Cartesia TTS in this app) is included with LiveKit Cloud; no extra API keys are required for those models when using Cloud.

### LiveKit Cloud auth (recommended)

To authenticate with LiveKit Cloud and have the CLI write credentials for you:

1. Install the [LiveKit CLI](https://docs.livekit.io/agents/start/voice-ai-quickstart/#livekit-cli) (`winget install LiveKit.LiveKitCLI` on Windows).
2. From this project directory, run:
   ```bash
   lk cloud auth
   ```
   Sign in in the browser and select your LiveKit Cloud project.
3. Write the project’s API keys and URL into a local env file:
   ```bash
   lk app env -w
   ```
   This creates/updates `.env.local` with `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
4. Add your OpenAI key to `.env` or `.env.local`:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

This app loads `.env` first, then `.env.local`, so credentials from `lk app env -w` are used when present.

## Local testing

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the agent worker

This connects to LiveKit and waits for jobs:

```bash
python main.py start
```

Leave this running.

### 3. Start the token server

In a second terminal:

```bash
python token_server.py
```

By default it serves at `http://localhost:8090`. Get a token (and the LiveKit URL) with:

```text
GET http://localhost:8090/token?room=my-room&identity=user1
```

Response: `{"token": "<jwt>", "url": "<LIVEKIT_URL>"}`.

### 4. Open the frontend

1. Serve the frontend (required for "Get token" to work: browsers block `file://` from calling localhost). For example: `python -m http.server 8080` then open `http://localhost:8080/simple-videochat.html`.
2. **WebSocket URL:** use your `LIVEKIT_URL` from `.env` (e.g. `wss://testing-bn5g3ihh.livekit.cloud`).
3. **Access token:** paste the `token` from the token server response.
4. Click **Connect**.

The token includes agent dispatch for `simple-agent`, so the agent should join the room and greet you. Allow microphone access to talk to the agent.

**Quick token:** in the browser console or a REST client:

```text
fetch('http://localhost:8090/token?room=my-room&identity=user1').then(r=>r.json()).then(d=>console.log('Token:', d.token, 'URL:', d.url))
```

## Deploy

### Docker

Build and run the agent container:

```bash
docker build -t livekitx-agent .
docker run --env-file .env livekitx-agent
```

Ensure `.env` (or the environment passed to `docker run`) contains `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and `OPENAI_API_KEY`. The container runs `python main.py download-files` at build time and `python main.py start` at runtime.

### Token server in production

For production, run a proper backend that issues tokens (and optionally the same agent-dispatch room config) instead of using `token_server.py` on a public port. Implement your own auth and use the same pattern:

- `api.AccessToken()` with identity and `VideoGrants(room_join=True, room=room_name)`
- `with_room_config(api.RoomConfiguration(agents=[api.RoomAgentDispatch(agent_name="simple-agent")]))`
- Return the JWT (and your frontend’s LiveKit URL) to the client.

### Deploying the agent to a host (Railway, Fly, etc.)

1. Build the Docker image (as above) or use a platform that runs `pip install -r requirements.txt` and `python main.py start`.
2. Set the same env vars (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`) in the host’s environment.
3. Point `LIVEKIT_URL` to your LiveKit server (e.g. your LiveKit Cloud project URL).
4. Deploy the token endpoint (or your own API) so the frontend can get tokens that include agent dispatch for `simple-agent`.

Once the worker is running and can reach LiveKit, any client that joins with a token that requests `simple-agent` (via room config or dispatch API) will get the voice agent in the room.
