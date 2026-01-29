# RealtimeSTT Multiclient

An extended RealtimeSST server that supports multiple clients connecting simultaneously, and API key authentication. Developed for the [SCS](https://scs.techfak.uni-bielefeld.de/) group. Built using FastAPI and Docker for easy deployment.
Adatped from the original [RealtimeSTT server](https://github.com/KoljaB/RealtimeSTT) project.

---

## Installation

**Pull the repository**

```bash
git clone git@gitlab.ub.uni-bielefeld.de:scs/enrico/modules/realtimestt_multiclient.git
cd realtimestt_multiclient
```

Create a .env file containing your desired api key:

```.dotenv
API_KEY_REALTIMESTT=your_api_key
```

### Using Docker

1. **Build the Docker image**

```bash
docker build -t realtimestt_multiclient .
```

2. **Run the Docker container**

```bash
docker run -d --gpus all --env-file .env --name realtimestt_multiclient -p 8011:8011 -p 8012:8012 realtimestt_multiclient
```

---

### Running Without Docker

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Start the FastAPI app**

```bash
python RealtimeSTT_server/stt_server.py --model large-v2 --language de --open_lan --debug
```
