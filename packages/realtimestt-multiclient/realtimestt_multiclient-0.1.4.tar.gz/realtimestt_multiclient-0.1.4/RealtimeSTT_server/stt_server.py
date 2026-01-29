"""
Speech-to-Text (STT) Server with Real-Time Transcription and WebSocket Interface

This server provides real-time speech-to-text (STT) transcription using the RealtimeSTT library. It allows clients to connect via WebSocket to send audio data and receive real-time transcription updates. The server supports configurable audio recording parameters, voice activity detection (VAD), and wake word detection. It is designed to handle continuous transcription as well as post-recording processing, enabling real-time feedback with the option to improve final transcription quality after the complete sentence is recognized.

### Features:
- Real-time transcription using pre-configured or user-defined STT models.
- WebSocket-based communication for control and data handling.
- Flexible recording and transcription options, including configurable pauses for sentence detection.
- Supports Silero and WebRTC VAD for robust voice activity detection.

### Starting the Server:
You can start the server using the command-line interface (CLI) command `stt-server`, passing the desired configuration options.

```bash
stt-server [OPTIONS]
```

### Available Parameters:
    - `-m, --model`: Model path or size; default 'large-v2'.
    - `-r, --rt-model, --realtime_model_type`: Real-time model size; default 'tiny.en'.
    - `-l, --lang, --language`: Language code for transcription; default 'en'.
    - `-i, --input-device, --input_device_index`: Audio input device index; default 1.
    - `-c, --control, --control_port`: WebSocket control port; default 8011.
    - `-d, --data, --data_port`: WebSocket data port; default 8012.
    - `-w, --wake_words`: Wake word(s) to trigger listening; default "".
    - `-D, --debug`: Enable debug logging.
    - `-W, --write`: Save audio to WAV file.
    - `-s, --silence_timing`: Enable dynamic silence duration for sentence detection; default True. 
    - `-b, --batch, --batch_size`: Batch size for inference; default 16.
    - `--root, --download_root`: Specifies the root path were the Whisper models are downloaded to.
    - `--silero_sensitivity`: Silero VAD sensitivity (0-1); default 0.05.
    - `--silero_use_onnx`: Use Silero ONNX model; default False.
    - `--webrtc_sensitivity`: WebRTC VAD sensitivity (0-3); default 3.
    - `--min_length_of_recording`: Minimum recording duration in seconds; default 1.1.
    - `--min_gap_between_recordings`: Min time between recordings in seconds; default 0.
    - `--enable_realtime_transcription`: Enable real-time transcription; default True.
    - `--realtime_processing_pause`: Pause between audio chunk processing; default 0.02.
    - `--silero_deactivity_detection`: Use Silero for end-of-speech detection; default True.
    - `--early_transcription_on_silence`: Start transcription after silence in seconds; default 0.2.
    - `--beam_size`: Beam size for main model; default 5.
    - `--beam_size_realtime`: Beam size for real-time model; default 3.
    - `--init_realtime_after_seconds`: Initial waiting time for realtime transcription; default 0.2.
    - `--realtime_batch_size`: Batch size for the real-time transcription model; default 16.
    - `--initial_prompt`: Initial main transcription guidance prompt.
    - `--initial_prompt_realtime`: Initial realtime transcription guidance prompt.
    - `--end_of_sentence_detection_pause`: Silence duration for sentence end detection; default 0.45.
    - `--unknown_sentence_detection_pause`: Pause duration for incomplete sentence detection; default 0.7.
    - `--mid_sentence_detection_pause`: Pause for mid-sentence break; default 2.0.
    - `--wake_words_sensitivity`: Wake word detection sensitivity (0-1); default 0.5.
    - `--wake_word_timeout`: Wake word timeout in seconds; default 5.0.
    - `--wake_word_activation_delay`: Delay before wake word activation; default 20.
    - `--wakeword_backend`: Backend for wake word detection; default 'none'.
    - `--openwakeword_model_paths`: Paths to OpenWakeWord models.
    - `--openwakeword_inference_framework`: OpenWakeWord inference framework; default 'tensorflow'.
    - `--wake_word_buffer_duration`: Wake word buffer duration in seconds; default 1.0.
    - `--use_main_model_for_realtime`: Use main model for real-time transcription.
    - `--use_extended_logging`: Enable extensive log messages.
    - `--logchunks`: Log incoming audio chunks.
    - `--compute_type`: Type of computation to use.
    - `--input_device_index`: Index of the audio input device.
    - `--gpu_device_index`: Index of the GPU device.
    - `--device`: Device to use for computation.
    - `--handle_buffer_overflow`: Handle buffer overflow during transcription.
    - `--suppress_tokens`: Suppress tokens during transcription.
    - `--allowed_latency_limit`: Allowed latency limit for real-time transcription.
    - `--faster_whisper_vad_filter`: Enable VAD filter for Faster Whisper; default False.


### WebSocket Interface:
The server supports two WebSocket connections:
1. **Control WebSocket**: Used to send and receive commands, such as setting parameters or calling recorder methods.
2. **Data WebSocket**: Used to send audio data for transcription and receive real-time transcription updates.

The server will broadcast real-time transcription updates to all connected clients on the data WebSocket.
"""

import asyncio
import base64
import json
import logging
import os
import sys
import threading
import time
import wave
from collections import deque
from datetime import datetime
from difflib import SequenceMatcher

import faster_whisper
import numpy as np
import pyaudio
import websockets
from scipy.signal import resample
from colorama import init, Fore, Style

from RealtimeSTT.audio_recorder import AudioToTextRecorder


debug_logging = False
extended_logging = False
send_recorded_chunk = False
log_incoming_chunks = False
silence_timing = False
writechunks = None
wav_file = None

hard_break_even_on_background_noise = 3.0
hard_break_even_on_background_noise_min_texts = 3
hard_break_even_on_background_noise_min_similarity = 0.99
hard_break_even_on_background_noise_min_chars = 15

text_time_deque = deque()
loglevel = logging.WARNING

FORMAT = pyaudio.paInt16
CHANNELS = 1
INIT_MODEL_TRANSCRIPTION_REALTIME = "tiny"

# Define ANSI color codes for terminal output
class bcolors:
    HEADER = '\033[95m'   # Magenta
    OKBLUE = '\033[94m'   # Blue
    OKCYAN = '\033[96m'   # Cyan
    OKGREEN = '\033[92m'  # Green
    WARNING = '\033[93m'  # Yellow
    FAIL = '\033[91m'     # Red
    ENDC = '\033[0m'      # Reset to default
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Initialize colorama
init()

# Define allowed methods and parameters for security
allowed_methods = [
    'set_microphone',
    'abort',
    'stop',
    'clear_audio_queue',
    'wakeup',
    'shutdown',
    'text',
]
allowed_parameters = [
    'language',
    'silero_sensitivity',
    'wake_word_activation_delay',
    'post_speech_silence_duration',
    'listen_start',
    'recording_stop_time',
    'last_transcription_bytes',
    'last_transcription_bytes_b64',
    'speech_end_silence_start',
    'is_recording',
    'use_wake_words',
]



# Queues and connections for control and data
control_connections = set()
# NOTE: audio_queue is created inside main_async() so it's bound to the
# actually running asyncio event loop (asyncio.run() creates a fresh loop).
audio_queue = None
client_recorder = {}
client_sockets = {}
client_prev_text = {}
client_threads = {}  # Track recorder threads per client
# NOTE: loop is assigned inside main_async() (the running loop).
loop = None

global_args = None
whisper_model = None
recorder_config = {}
recorder_thread = None
stop_recorder = False



#  <----- HELPER FUNCTIONS ----->

def preprocess_text(text):
    # Remove leading whitespaces
    text = text.lstrip()

    # Remove starting ellipses if present
    if text.startswith("..."):
        text = text[3:]

    if text.endswith("...'."):
        text = text[:-1]

    if text.endswith("...'"):
        text = text[:-1]

    # Remove any leading whitespaces again after ellipses removal
    text = text.lstrip()

    # Uppercase the first letter
    if text:
        text = text[0].upper() + text[1:]
    
    return text

def debug_print(message):
    if debug_logging:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        thread_name = threading.current_thread().name
        print(f"{Fore.CYAN}[DEBUG][{timestamp}][{thread_name}] {message}{Style.RESET_ALL}", file=sys.stderr)

def format_timestamp_ns(timestamp_ns: int) -> str:
    # Split into whole seconds and the nanosecond remainder
    seconds = timestamp_ns // 1_000_000_000
    remainder_ns = timestamp_ns % 1_000_000_000

    # Convert seconds part into a datetime object (local time)
    dt = datetime.fromtimestamp(seconds)

    # Format the main time as HH:MM:SS
    time_str = dt.strftime("%H:%M:%S")

    # For instance, if you want milliseconds, divide the remainder by 1e6 and format as 3-digit
    milliseconds = remainder_ns // 1_000_000
    formatted_timestamp = f"{time_str}.{milliseconds:03d}"

    return formatted_timestamp

def parse_arguments():
    global debug_logging, extended_logging, loglevel, writechunks, log_incoming_chunks, dynamic_silence_timing

    import argparse
    parser = argparse.ArgumentParser(
        description='Start the Speech-to-Text (STT) server with various configuration options.')

    parser.add_argument('-m', '--model', type=str, default='large-v2',
                        help='Path to the STT model or model size. Options include: tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large-v1, large-v2, or any huggingface CTranslate2 STT model such as deepdml/faster-whisper-large-v3-turbo-ct2. Default is large-v2.')

    parser.add_argument('-r', '--rt-model', '--realtime_model_type', type=str, default='tiny',
                        help='Model size for real-time transcription. Options same as --model.  This is used only if real-time transcription is enabled (enable_realtime_transcription). Default is tiny.en.')

    parser.add_argument('-l', '--lang', '--language', type=str, default='en',
                        help='Language code for the STT model to transcribe in a specific language. Leave this empty for auto-detection based on input audio. Default is en. List of supported language codes: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L11-L110')

    parser.add_argument('-i', '--input-device', '--input-device-index', type=int, default=1,
                        help='Index of the audio input device to use. Use this option to specify a particular microphone or audio input device based on your system. Default is 1.')

    parser.add_argument('-c', '--control', '--control_port', type=int, default=8011,
                        help='The port number used for the control WebSocket connection. Control connections are used to send and receive commands to the server. Default is port 8011.')

    parser.add_argument('-d', '--data', '--data_port', type=int, default=8012,
                        help='The port number used for the data WebSocket connection. Data connections are used to send audio data and receive transcription updates in real time. Default is port 8012.')

    parser.add_argument('-w', '--wake_words', type=str, default="",
                        help='Specify the wake word(s) that will trigger the server to start listening. For example, setting this to "Jarvis" will make the system start transcribing when it detects the wake word "Jarvis". Default is "Jarvis".')

    parser.add_argument('-D', '--debug', action='store_true',
                        help='Enable debug logging for detailed server operations')

    parser.add_argument('--debug_websockets', action='store_true',
                        help='Enable debug logging for detailed server websocket operations')

    parser.add_argument('-W', '--write', metavar='FILE', help='Save received audio to a WAV file')

    parser.add_argument('-b', '--batch', '--batch_size', type=int, default=16,
                        help='Batch size for inference. This parameter controls the number of audio chunks processed in parallel during transcription. Default is 16.')

    parser.add_argument('--root', '--download_root', type=str, default=None,
                        help='Specifies the root path where the Whisper models are downloaded to. Default is None.')

    parser.add_argument('-s', '--silence_timing', action='store_true', default=True,
                        help='Enable dynamic adjustment of silence duration for sentence detection. Adjusts post-speech silence duration based on detected sentence structure and punctuation. Default is False.')

    parser.add_argument('--init_realtime_after_seconds', type=float, default=0.2,
                        help='The initial waiting time in seconds before real-time transcription starts. This delay helps prevent false positives at the beginning of a session. Default is 0.2 seconds.')

    parser.add_argument('--realtime_batch_size', type=int, default=16,
                        help='Batch size for the real-time transcription model. This parameter controls the number of audio chunks processed in parallel during real-time transcription. Default is 16.')

    parser.add_argument('--initial_prompt_realtime', type=str, default="",
                        help='Initial prompt that guides the real-time transcription model to produce transcriptions in a particular style or format.')

    parser.add_argument('--silero_sensitivity', type=float, default=0.05,
                        help='Sensitivity level for Silero Voice Activity Detection (VAD), with a range from 0 to 1. Lower values make the model less sensitive, useful for noisy environments. Default is 0.05.')

    parser.add_argument('--silero_use_onnx', action='store_true', default=False,
                        help='Enable ONNX version of Silero model for faster performance with lower resource usage. Default is False.')

    parser.add_argument('--webrtc_sensitivity', type=int, default=3,
                        help='Sensitivity level for WebRTC Voice Activity Detection (VAD), with a range from 0 to 3. Higher values make the model less sensitive, useful for cleaner environments. Default is 3.')

    parser.add_argument('--min_length_of_recording', type=float, default=1.1,
                        help='Minimum duration of valid recordings in seconds. This prevents very short recordings from being processed, which could be caused by noise or accidental sounds. Default is 1.1 seconds.')

    parser.add_argument('--min_gap_between_recordings', type=float, default=0,
                        help='Minimum time (in seconds) between consecutive recordings. Setting this helps avoid overlapping recordings when there’s a brief silence between them. Default is 0 seconds.')

    parser.add_argument('--enable_realtime_transcription', action='store_true', default=True,
                        help='Enable continuous real-time transcription of audio as it is received. When enabled, transcriptions are sent in near real-time. Default is True.')

    parser.add_argument('--realtime_processing_pause', type=float, default=0.02,
                        help='Time interval (in seconds) between processing audio chunks for real-time transcription. Lower values increase responsiveness but may put more load on the CPU. Default is 0.02 seconds.')

    parser.add_argument('--silero_deactivity_detection', action='store_true', default=True,
                        help='Use the Silero model for end-of-speech detection. This option can provide more robust silence detection in noisy environments, though it consumes more GPU resources. Default is True.')

    parser.add_argument('--early_transcription_on_silence', type=float, default=0.2,
                        help='Start transcription after the specified seconds of silence. This is useful when you want to trigger transcription mid-speech when there is a brief pause. Should be lower than post_speech_silence_duration. Set to 0 to disable. Default is 0.2 seconds.')

    parser.add_argument('--beam_size', type=int, default=5,
                        help='Beam size for the main transcription model. Larger values may improve transcription accuracy but increase the processing time. Default is 5.')

    parser.add_argument('--beam_size_realtime', type=int, default=3,
                        help='Beam size for the real-time transcription model. A smaller beam size allows for faster real-time processing but may reduce accuracy. Default is 3.')

    parser.add_argument('--initial_prompt', type=str,
                        default="Incomplete thoughts should end with '...'. Examples of complete thoughts: 'The sky is blue.' 'She walked home.' Examples of incomplete thoughts: 'When the sky...' 'Because he...'",
                        help='Initial prompt that guides the transcription model to produce transcriptions in a particular style or format. The default provides instructions for handling sentence completions and ellipsis usage.')

    parser.add_argument('--end_of_sentence_detection_pause', type=float, default=0.45,
                        help='The duration of silence (in seconds) that the model should interpret as the end of a sentence. This helps the system detect when to finalize the transcription of a sentence. Default is 0.45 seconds.')

    parser.add_argument('--unknown_sentence_detection_pause', type=float, default=0.7,
                        help='The duration of pause (in seconds) that the model should interpret as an incomplete or unknown sentence. This is useful for identifying when a sentence is trailing off or unfinished. Default is 0.7 seconds.')

    parser.add_argument('--mid_sentence_detection_pause', type=float, default=2.0,
                        help='The duration of pause (in seconds) that the model should interpret as a mid-sentence break. Longer pauses can indicate a pause in speech but not necessarily the end of a sentence. Default is 2.0 seconds.')

    parser.add_argument('--wake_words_sensitivity', type=float, default=0.5,
                        help='Sensitivity level for wake word detection, with a range from 0 (most sensitive) to 1 (least sensitive). Adjust this value based on your environment to ensure reliable wake word detection. Default is 0.5.')

    parser.add_argument('--wake_word_timeout', type=float, default=5.0,
                        help='Maximum time in seconds that the system will wait for a wake word before timing out. After this timeout, the system stops listening for wake words until reactivated. Default is 5.0 seconds.')

    parser.add_argument('--wake_word_activation_delay', type=float, default=0,
                        help='The delay in seconds before the wake word detection is activated after the system starts listening. This prevents false positives during the start of a session. Default is 0 seconds.')

    parser.add_argument('--wakeword_backend', type=str, default='none',
                        help='The backend used for wake word detection. You can specify different backends such as "default" or any custom implementations depending on your setup. Default is "pvporcupine".')

    parser.add_argument('--openwakeword_model_paths', type=str, nargs='*',
                        help='A list of file paths to OpenWakeWord models. This is useful if you are using OpenWakeWord for wake word detection and need to specify custom models.')

    parser.add_argument('--openwakeword_inference_framework', type=str, default='tensorflow',
                        help='The inference framework to use for OpenWakeWord models. Supported frameworks could include "tensorflow", "pytorch", etc. Default is "tensorflow".')

    parser.add_argument('--wake_word_buffer_duration', type=float, default=1.0,
                        help='Duration of the buffer in seconds for wake word detection. This sets how long the system will store the audio before and after detecting the wake word. Default is 1.0 seconds.')

    parser.add_argument('--use_main_model_for_realtime', action='store_true',
                        help='Enable this option if you want to use the main model for real-time transcription, instead of the smaller, faster real-time model. Using the main model may provide better accuracy but at the cost of higher processing time.')

    parser.add_argument('--use_extended_logging', action='store_true',
                        help='Writes extensive log messages for the recording worker, that processes the audio chunks.')

    parser.add_argument('--compute_type', type=str, default='default',
                        help='Type of computation to use. See https://opennmt.net/CTranslate2/quantization.html')

    parser.add_argument('--gpu_device_index', type=int, default=0,
                        help='Index of the GPU device to use. Default is None.')

    parser.add_argument('--device', type=str, default='cuda',
                        help='Device for model to use. Can either be "cuda" or "cpu". Default is cuda.')

    parser.add_argument('--handle_buffer_overflow', action='store_true',
                        help='Handle buffer overflow during transcription. Default is False.')

    parser.add_argument('--suppress_tokens', type=int, default=[-1], nargs='*',
                        help='Suppress tokens during transcription. Default is [-1].')

    parser.add_argument('--allowed_latency_limit', type=int, default=100,
                        help='Maximal amount of chunks that can be unprocessed in queue before discarding chunks.. Default is 100.')

    parser.add_argument('--faster_whisper_vad_filter', action='store_true',
                        help='Enable VAD filter for Faster Whisper. Default is False.')

    parser.add_argument('--logchunks', action='store_true', help='Enable logging of incoming audio chunks (periods)')

    parser.add_argument('--host', type=str, default="localhost", help='Host to use')

    # Parse arguments
    args = parser.parse_args()

    debug_logging = args.debug
    extended_logging = args.use_extended_logging
    writechunks = args.write
    log_incoming_chunks = args.logchunks
    dynamic_silence_timing = args.silence_timing

    ws_logger = logging.getLogger('websockets')
    if args.debug_websockets:
        # If app debug is on, let websockets be verbose too
        ws_logger.setLevel(logging.DEBUG)
        # Ensure it uses the handler configured by basicConfig
        ws_logger.propagate = False  # Prevent duplicate messages if it also propagates to root
    else:
        # If app debug is off, silence websockets below WARNING
        ws_logger.setLevel(logging.WARNING)
        ws_logger.propagate = True  # Allow WARNING/ERROR messages to reach root logger's handler

    # Replace escaped newlines with actual newlines in initial_prompt
    if args.initial_prompt:
        args.initial_prompt = args.initial_prompt.replace("\\n", "\n")

    if args.initial_prompt_realtime:
        args.initial_prompt_realtime = args.initial_prompt_realtime.replace("\\n", "\n")

    return args

def decode_and_resample(audio_data, original_sample_rate, target_sample_rate):

    # Decode 16-bit PCM data to numpy array
    if original_sample_rate == target_sample_rate:
        return audio_data

    audio_np = np.frombuffer(audio_data, dtype=np.int16)

    # Calculate the number of samples after resampling
    num_original_samples = len(audio_np)
    num_target_samples = int(num_original_samples * target_sample_rate /
                                original_sample_rate)

    # Resample the audio
    resampled_audio = resample(audio_np, num_target_samples)

    return resampled_audio.astype(np.int16).tobytes()


#  <----- CALLBACK FUNCTIONS ----->

def text_detected(text, client_id, loop):
    global client_prev_text
    prev_text = client_prev_text[client_id]
    recorder = client_recorder.get(client_id)
    text = preprocess_text(text)
    if silence_timing and recorder:
        def ends_with_ellipsis(text: str):
            if text.endswith("..."):
                return True
            if len(text) > 1 and text[:-1].endswith("..."):
                return True
            return False
        def sentence_end(text: str):
            sentence_end_marks = ['.', '!', '?', '。']
            if text and text[-1] in sentence_end_marks:
                return True
            return False
        if ends_with_ellipsis(text):
            recorder.post_speech_silence_duration = global_args.mid_sentence_detection_pause
        elif sentence_end(text) and sentence_end(prev_text) and not ends_with_ellipsis(prev_text):
            recorder.post_speech_silence_duration = global_args.end_of_sentence_detection_pause
        else:
            recorder.post_speech_silence_duration = global_args.unknown_sentence_detection_pause


        # Append the new text with its timestamp
        current_time = time.time()
        text_time_deque.append((current_time, text))

        # Remove texts older than hard_break_even_on_background_noise seconds
        while text_time_deque and text_time_deque[0][0] < current_time - hard_break_even_on_background_noise:
            text_time_deque.popleft()

        # Check if at least hard_break_even_on_background_noise_min_texts texts have arrived within the last hard_break_even_on_background_noise seconds
        if len(text_time_deque) >= hard_break_even_on_background_noise_min_texts:
            texts = [t[1] for t in text_time_deque]
            first_text = texts[0]
            last_text = texts[-1]

            # Compute the similarity ratio between the first and last texts
            similarity = SequenceMatcher(None, first_text, last_text).ratio()

            if similarity > hard_break_even_on_background_noise_min_similarity and len(first_text) > hard_break_even_on_background_noise_min_chars:
                recorder.stop()
                recorder.clear_audio_queue()
                client_prev_text[client_id] = ""

    client_prev_text[client_id] = text

    # Put the message in the audio queue to be sent to clients
    message = json.dumps({
        'client_id': client_id,
        'type': 'realtime',
        'text': text
    })
    enqueue_audio_message_threadsafe(message, loop)

    # Get current timestamp in HH:MM:SS.nnn format
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

    if extended_logging:
        print(f"  client: {client_id}: [{timestamp}] Realtime text: {bcolors.OKCYAN}{text}{bcolors.ENDC}\n", flush=True, end="")
    else:
        print(f"\rclient: {client_id}: [{timestamp}] {bcolors.OKCYAN}{text}{bcolors.ENDC}", flush=True, end='')

def on_recording_start(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'recording_start'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_recording_stop(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'recording_stop'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_vad_detect_start(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'vad_detect_start'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_vad_detect_stop(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'vad_detect_stop'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_wakeword_detected(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'wakeword_detected'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_wakeword_detection_start(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'wakeword_detection_start'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_wakeword_detection_end(client_id, loop):
    message = json.dumps({
        'client_id': client_id,
        'type': 'wakeword_detection_end'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_transcription_start(_audio_bytes, client_id, loop):
    bytes_b64 = base64.b64encode(_audio_bytes.tobytes()).decode('utf-8')
    message = json.dumps({
        'client_id': client_id,
        'type': 'transcription_start',
        'audio_bytes_base64': bytes_b64
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_turn_detection_start(client_id, loop):
    print("&&& stt_server on_turn_detection_start")
    message = json.dumps({
        'client_id': client_id,
        'type': 'start_turn_detection'
    })
    enqueue_audio_message_threadsafe(message, loop)

def on_turn_detection_stop(client_id, loop):
    print("&&& stt_server on_turn_detection_stop")
    message = json.dumps({
        'client_id': client_id,
        'type': 'stop_turn_detection'
    })
    enqueue_audio_message_threadsafe(message, loop)

def make_callback(loop, callback):
    def inner_callback(*args, **kwargs):
        callback(*args, **kwargs, loop=loop)
    return inner_callback


def enqueue_audio_message_threadsafe(message: str, loop: asyncio.AbstractEventLoop):
    """Enqueue a JSON message onto audio_queue from any thread.

    We use loop.call_soon_threadsafe + put_nowait to avoid relying on
    run_coroutine_threadsafe with a potentially mismatched or non-running loop.
    """
    if loop is None:
        print(f"{bcolors.WARNING}enqueue_audio_message_threadsafe: loop is None, cannot enqueue message{bcolors.ENDC}")
        return
    if audio_queue is None:
        print(f"{bcolors.WARNING}enqueue_audio_message_threadsafe: audio_queue is None, cannot enqueue message{bcolors.ENDC}")
        return
    loop.call_soon_threadsafe(audio_queue.put_nowait, message)


# Thread used to run the recorder including the whisper model
def _recorder_thread(client_id, loop):
    global stop_recorder, whisper_model, client_recorder

    if not client_id in client_recorder or client_recorder[client_id] is None:
        client_recorder[client_id] = AudioToTextRecorder(whisper_model = whisper_model, client_id=client_id, **recorder_config)
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}RealtimeSTT recorder initialized for client: {client_id} {bcolors.ENDC}")


    def process_text(full_sentence, client_id):
        global client_prev_text
        client_prev_text[client_id] = ""
        full_sentence = preprocess_text(full_sentence)
        print(f"\nFull sentence detected for client {client_id}: {full_sentence}")
        message = json.dumps({
            'client_id': client_id,
            'type': 'fullSentence',
            'text': full_sentence
        })
        enqueue_audio_message_threadsafe(message, loop)

        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        if extended_logging:
            print(f"  [{timestamp}] Full text: {bcolors.BOLD}Sentence:{bcolors.ENDC} {bcolors.OKGREEN}{full_sentence}{bcolors.ENDC}\n", flush=True, end="")
        else:
            print(f"\r[{timestamp}] {bcolors.BOLD}Sentence:{bcolors.ENDC} {bcolors.OKGREEN}{full_sentence}{bcolors.ENDC}\n")


    try:
        while not stop_recorder:
            while client_recorder[client_id] is None:
                print(f"{bcolors.WARNING}Waiting for recorder to be initialized for client: {client_id}{bcolors.ENDC}")
                time.sleep(0.5)
                continue
            client_recorder[client_id].text(process_text)
    except KeyboardInterrupt:
        print(f"{bcolors.WARNING}Exiting application due to keyboard interrupt{bcolors.ENDC}")

# Function used to get messages from the audio queue and send them
async def broadcast_audio_messages():
    to_remove = []
    while True:
        message = await audio_queue.get()

        # Messages in audio_queue are JSON strings created with json.dumps().
        # Using ast.literal_eval() here is brittle (JSON != Python literals) and can crash
        # the broadcast task, preventing transcripts from reaching clients.
        try:
            payload = json.loads(message)
        except Exception as e:
            debug_print(f"broadcast_audio_messages: failed to parse message as JSON ({e}): {message[:200]}...")
            continue

        message_client_id = payload.get('client_id')
        if not message_client_id:
            debug_print(f"broadcast_audio_messages: missing client_id in payload: {payload}")
            continue

        if message_client_id not in client_sockets:
            debug_print(
                f"broadcast_audio_messages: no data websocket registered for client_id={message_client_id} (type={payload.get('type')})"
            )
        #print(f"\nBroadcasting message to client_id={message_client_id}: {payload.get('type')}: {payload.get('text', '')}")
        for socket_id, socket in list(client_sockets.items()):
            print(f"  Checking socket for client_id={socket_id}")
            try:
                if message_client_id != socket_id:
                    continue
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                #print(f"  [{timestamp}] Sending message: {bcolors.OKBLUE}{message}{bcolors.ENDC}\n", flush=True, end="")
                await socket.send(message)
            except websockets.exceptions.ConnectionClosed:
                to_remove.append(socket_id)
            except Exception as e:
                debug_print(f"broadcast_audio_messages: error sending to client_id={socket_id}: {e}")
                to_remove.append(socket_id)

        # Remove disconnected sockets
        for socket_id in to_remove:
            if socket_id in client_sockets:
                print(f"{bcolors.WARNING}Removing disconnected socket for client_id={socket_id}{bcolors.ENDC}")
                del client_sockets[socket_id]
        to_remove.clear()

# Main function which needs to recognize new clients and create audio queues for each
async def data_handler(websocket):
    global writechunks, wav_file, loop, client_recorder, client_prev_text, client_threads
    print(f"{bcolors.OKGREEN}Data client connected{bcolors.ENDC}")

    client_id = None
    try:
        while True:
            message = await websocket.recv()

            # Support an initial JSON handshake message to register the client_id
            # before any audio arrives. Without this, the server may enqueue transcripts
            # (recording_start/realtime/fullSentence) before we know which websocket to
            # send them to, and they get dropped.
            if isinstance(message, str):
                try:
                    hello = json.loads(message)
                except Exception:
                    print(f"{bcolors.WARNING}Received non-JSON text message on data connection{bcolors.ENDC}")
                    continue

                if hello.get('type') == 'hello' and 'client_id' in hello:
                    client_id = hello['client_id']
                    client_sockets[client_id] = websocket

                    if client_id not in client_recorder:
                        client_recorder[client_id] = None
                        t = threading.Thread(target=_recorder_thread, args=(client_id, loop))
                        t.start()
                        client_threads[client_id] = t
                        while client_recorder[client_id] is None:
                            await asyncio.sleep(0.1)
                        client_prev_text[client_id] = ""

                    debug_print(f"Data hello received, registered client_id={client_id}")
                else:
                    print(f"{bcolors.WARNING}Received unexpected text message on data connection{bcolors.ENDC}")
                continue

            if isinstance(message, bytes):
                metadata_length = int.from_bytes(message[:4], byteorder='little')
                metadata_length = int.from_bytes(message[:4], byteorder='little')
                metadata_json = message[4:4 + metadata_length].decode('utf-8')
                metadata = json.loads(metadata_json)

                #if os.getenv('API_KEY_REALTIMESTT') != metadata['api_key']:
                #    print(f"{bcolors.WARNING}Received message with invalid API key: {metadata}{bcolors.ENDC}")
                #    continue

                if 'client_id' not in metadata:
                    print(f"{bcolors.WARNING}Received message without client_id in metadata: {metadata}{bcolors.ENDC}")
                    continue  # Skip this message
                client_id = metadata['client_id']
                client_sockets[client_id] = websocket
                if client_id not in client_recorder:
                    client_recorder[client_id] = None
                    t = threading.Thread(target=_recorder_thread, args=(client_id, loop))
                    t.start()
                    client_threads[client_id] = t
                    while client_recorder[client_id] is None:
                        await asyncio.sleep(0.1)
                    print("Registered clients:")
                    for key, value in client_recorder.items():
                        print(f"id: {key} -> recorder: {value}")
                    client_prev_text[client_id] = ""
                if extended_logging:
                    debug_print(f"Received audio chunk (size: {len(message)} bytes)")
                elif log_incoming_chunks:
                    print(".", end='', flush=True)
                sample_rate = metadata['sampleRate']
                if 'server_sent_to_stt' in metadata:
                    stt_received_ns = time.time_ns()
                    metadata["stt_received"] = stt_received_ns
                    metadata["stt_received_formatted"] = format_timestamp_ns(stt_received_ns)
                    print(f"Server received audio chunk of length {len(message)} bytes, metadata: {metadata}")
                if extended_logging:
                    debug_print(f"Processing audio chunk with sample rate {sample_rate}")
                chunk = message[4+metadata_length:]
                if writechunks and isinstance(writechunks, str):
                    if not wav_file:
                        wav_file = wave.open(writechunks, 'wb')
                        wav_file.setnchannels(CHANNELS)
                        wav_file.setsampwidth(pyaudio.get_sample_size(FORMAT))
                        wav_file.setframerate(sample_rate)
                    wav_file.writeframes(chunk)
                if sample_rate != 16000:
                    resampled_chunk = decode_and_resample(chunk, sample_rate, 16000)
                    if extended_logging:
                        debug_print(f"Resampled chunk size: {len(resampled_chunk)} bytes")
                    client_recorder[client_id].feed_audio(resampled_chunk)
                else:
                    client_recorder[client_id].feed_audio(chunk)
            else:
                print(f"{bcolors.WARNING}Received non-binary message on data connection{bcolors.ENDC}")
                print(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"{bcolors.WARNING}Data client disconnected: {e}{bcolors.ENDC}")
    finally:
        if client_id is not None:
            # Clean up all per-client resources
            if client_id in client_recorder:
                client_recorder[client_id].clear_audio_queue()
                try:
                    client_recorder[client_id].stop()
                    client_recorder[client_id].shutdown()
                except Exception:
                    pass
                del client_recorder[client_id]
            if client_id in client_prev_text:
                del client_prev_text[client_id]
            if client_id in client_sockets:
                del client_sockets[client_id]
            if client_id in client_threads:
                try:
                    client_threads[client_id].join(timeout=2)
                except Exception:
                    pass
                del client_threads[client_id]

async def control_handler(websocket):
    global stop_recorder, whisper_model, client_recorder
    debug_print(f"New control connection from {websocket.remote_address}")
    print(f"{bcolors.OKGREEN}Control client connected{bcolors.ENDC}")
    control_connections.add(websocket)
    try:
        async for message in websocket:
            debug_print(f"Received control message: {message[:200]}...")
            if isinstance(message, str):
                try:
                    command_data = json.loads(message)
                    command = command_data.get("command")
                    client_id = command_data.get("client_id")

                    #if str(os.getenv('API_KEY_REALTIMESTT')) != str(command_data.get('api_key')):
                    #    print(f"{bcolors.WARNING}Received message with invalid API key: {command_data}{bcolors.ENDC}")
                    #    continue
                    print(command_data)

                    if client_id is None:
                        await websocket.send(json.dumps({"status": "error", "message": "Missing client_id in control message"}))
                        continue
                    recorder = client_recorder.get(client_id)
                    while recorder is None:
                        print(f"{bcolors.WARNING}Waiting for recorder to be initialized for client_id {client_id}{bcolors.ENDC}")
                        await asyncio.sleep(1.0)
                        recorder = client_recorder.get(client_id)
                    if command == "set_parameter":
                        parameter = command_data.get("parameter")
                        value = command_data.get("value")
                        if parameter in allowed_parameters and hasattr(recorder, parameter):
                            setattr(recorder, parameter, value)
                            if isinstance(value, float):
                                value_formatted = f"{value:.2f}"
                            else:
                                value_formatted = value
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            if extended_logging:
                                print(f"  [{timestamp}] {bcolors.OKGREEN}Set recorder.{parameter} to: {bcolors.OKBLUE}{value_formatted}{bcolors.ENDC}")
                            await websocket.send(json.dumps({"status": "success", "message": f"Parameter {parameter} set to {value}"}))
                        else:
                            if not parameter in allowed_parameters:
                                print(f"{bcolors.WARNING}Parameter {parameter} is not allowed (set_parameter){bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "error", "message": f"Parameter {parameter} is not allowed (set_parameter)"}))
                            else:
                                print(f"{bcolors.WARNING}Parameter {parameter} does not exist (set_parameter){bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "error", "message": f"Parameter {parameter} does not exist (set_parameter)"}))

                    elif command == "get_parameter":
                        parameter = command_data.get("parameter")
                        request_id = command_data.get("request_id")
                        if parameter in allowed_parameters and hasattr(recorder, parameter):
                            value = getattr(recorder, parameter)
                            if isinstance(value, float):
                                value_formatted = f"{value:.2f}"
                            else:
                                value_formatted = f"{value}"
                            value_truncated = value_formatted[:39] + "…" if len(value_formatted) > 40 else value_formatted
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            if extended_logging:
                                print(f"  [{timestamp}] {bcolors.OKGREEN}Get recorder.{parameter}: {bcolors.OKBLUE}{value_truncated}{bcolors.ENDC}")
                            response = {"status": "success", "parameter": parameter, "value": value}
                            if request_id is not None:
                                response["request_id"] = request_id
                            await websocket.send(json.dumps(response))
                        else:
                            if not parameter in allowed_parameters:
                                print(f"{bcolors.WARNING}Parameter {parameter} is not allowed (get_parameter){bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "error", "message": f"Parameter {parameter} is not allowed (get_parameter)"}))
                            else:
                                print(f"{bcolors.WARNING}Parameter {parameter} does not exist (get_parameter){bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "error", "message": f"Parameter {parameter} does not exist (get_parameter)"}))
                    elif command == "call_method":
                        method_name = command_data.get("method")
                        if method_name in allowed_methods:
                            method = getattr(recorder, method_name, None)
                            if method and callable(method):
                                args = command_data.get("args", [])
                                kwargs = command_data.get("kwargs", {})
                                method(*args, **kwargs)
                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                print(f"  [{timestamp}] {bcolors.OKGREEN}Called method recorder.{bcolors.OKBLUE}{method_name}{bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "success", "message": f"Method {method_name} called"}))
                            else:
                                print(f"{bcolors.WARNING}Recorder does not have method {method_name}{bcolors.ENDC}")
                                await websocket.send(json.dumps({"status": "error", "message": f"Recorder does not have method {method_name}"}))
                        else:
                            print(f"{bcolors.WARNING}Method {method_name} is not allowed{bcolors.ENDC}")
                            await websocket.send(json.dumps({"status": "error", "message": f"Method {method_name} is not allowed"}))
                    else:
                        print(f"{bcolors.WARNING}Unknown command: {command}{bcolors.ENDC}")
                        await websocket.send(json.dumps({"status": "error", "message": f"Unknown command {command}"}))
                except json.JSONDecodeError:
                    print(f"{bcolors.WARNING}Received invalid JSON command{bcolors.ENDC}")
                    await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON command"}))
            else:
                print(f"{bcolors.WARNING}Received unknown message type on control connection{bcolors.ENDC}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"{bcolors.WARNING}Control client disconnected: {e}{bcolors.ENDC}")
    finally:
        control_connections.remove(websocket)

async def shutdown_procedure():
    global stop_recorder, recorder_thread
    if recorder_thread is not None:
        try:
            recorder_thread.join()
            print(f"{bcolors.OKGREEN}Recorder thread finished{bcolors.ENDC}")
        except Exception:
            pass
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"{bcolors.OKGREEN}All tasks cancelled, closing event loop now.{bcolors.ENDC}")

async def main_async():
    global stop_recorder, recorder_config, global_args, whisper_model, loop, audio_queue
    args = parse_arguments()
    global_args = args

    print(f"{bcolors.BOLD}{bcolors.OKCYAN}Starting server, please wait...{bcolors.ENDC}")

    if whisper_model is None:
        whisper_model = faster_whisper.WhisperModel(
            model_size_or_path=args.model,
            device=args.device,
            compute_type=args.compute_type,
            device_index=args.gpu_device_index,
            download_root=args.root,
        )

    loop = asyncio.get_running_loop()
    # Create the queue bound to the running loop (critical for thread-safe enqueueing)
    if audio_queue is None:
        audio_queue = asyncio.Queue()


    recorder_config = {
        'model': args.model,
        'download_root': args.root,
        'realtime_model_type': args.rt_model,
        'language': args.lang,
        'batch_size': args.batch,
        'init_realtime_after_seconds': args.init_realtime_after_seconds,
        'realtime_batch_size': args.realtime_batch_size,
        'initial_prompt_realtime': args.initial_prompt_realtime,
        'input_device_index': args.input_device,
        'silero_sensitivity': args.silero_sensitivity,
        'silero_use_onnx': args.silero_use_onnx,
        'webrtc_sensitivity': args.webrtc_sensitivity,
        'post_speech_silence_duration': args.unknown_sentence_detection_pause,
        'min_length_of_recording': args.min_length_of_recording,
        'min_gap_between_recordings': args.min_gap_between_recordings,
        'enable_realtime_transcription': args.enable_realtime_transcription,
        'realtime_processing_pause': args.realtime_processing_pause,
        'silero_deactivity_detection': args.silero_deactivity_detection,
        'early_transcription_on_silence': args.early_transcription_on_silence,
        'beam_size': args.beam_size,
        'beam_size_realtime': args.beam_size_realtime,
        'initial_prompt': args.initial_prompt,
        'wake_words': args.wake_words,
        'wake_words_sensitivity': args.wake_words_sensitivity,
        'wake_word_timeout': args.wake_word_timeout,
        'wake_word_activation_delay': args.wake_word_activation_delay,
        'wakeword_backend': args.wakeword_backend,
        'openwakeword_model_paths': args.openwakeword_model_paths,
        'openwakeword_inference_framework': args.openwakeword_inference_framework,
        'wake_word_buffer_duration': args.wake_word_buffer_duration,
        'use_main_model_for_realtime': args.use_main_model_for_realtime,
        'spinner': False,
        'use_microphone': False,

        'on_realtime_transcription_update': make_callback(loop, text_detected),
        'on_recording_start': make_callback(loop, on_recording_start),
        'on_recording_stop': make_callback(loop, on_recording_stop),
        'on_vad_detect_start': make_callback(loop, on_vad_detect_start),
        'on_vad_detect_stop': make_callback(loop, on_vad_detect_stop),
        'on_wakeword_detected': make_callback(loop, on_wakeword_detected),
        'on_wakeword_detection_start': make_callback(loop, on_wakeword_detection_start),
        'on_wakeword_detection_end': make_callback(loop, on_wakeword_detection_end),
        'on_transcription_start': make_callback(loop, on_transcription_start),
        'on_turn_detection_start': make_callback(loop, on_turn_detection_start),
        'on_turn_detection_stop': make_callback(loop, on_turn_detection_stop),

        # 'on_recorded_chunk': make_callback(loop, on_recorded_chunk),
        'no_log_file': True,  # Disable logging to file
        'use_extended_logging': args.use_extended_logging,
        'level': loglevel,
        'compute_type': args.compute_type,
        'gpu_device_index': args.gpu_device_index,
        'device': args.device,
        'handle_buffer_overflow': args.handle_buffer_overflow,
        'suppress_tokens': args.suppress_tokens,
        'allowed_latency_limit': args.allowed_latency_limit,
        'faster_whisper_vad_filter': args.faster_whisper_vad_filter,
    }

    try:
        # Attempt to start control and data servers
        host = args.host

        control_server = await websockets.serve(control_handler, host, args.control)
        data_server = await websockets.serve(data_handler, host, args.data)
        print(f"{bcolors.OKGREEN}Control server started on {bcolors.OKBLUE}ws://{host}:{args.control}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Data server started on {bcolors.OKBLUE}ws://{host}:{args.data}{bcolors.ENDC}")

        # Start the broadcast and recorder threads
        broadcast_task = asyncio.create_task(broadcast_audio_messages())

        print(f"{bcolors.OKGREEN}Server started. Press Ctrl+C to stop the server.{bcolors.ENDC}")

        # Run server tasks
        await asyncio.gather(control_server.wait_closed(), data_server.wait_closed(), broadcast_task)
    except OSError as e:
        print(f"{bcolors.FAIL}Error: Could not start server on specified ports. It’s possible another instance of the server is already running, or the ports are being used by another application.{bcolors.ENDC}")
    except KeyboardInterrupt:
        print(f"{bcolors.WARNING}Server interrupted by user, shutting down...{bcolors.ENDC}")
    finally:
        # Shutdown procedures for recorder and server threads
        await shutdown_procedure()
        print(f"{bcolors.OKGREEN}Server shutdown complete.{bcolors.ENDC}")


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        # Capture any final KeyboardInterrupt to prevent it from showing up in logs
        print(f"{bcolors.WARNING}Server interrupted by user.{bcolors.ENDC}")
        exit(0)

if __name__ == '__main__':
    main()

