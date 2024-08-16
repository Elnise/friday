import asyncio
from os import remove

import websockets
import subprocess
import requests
import logging
import sounddevice as sd
import argparse
import json
import taskProcessor

sample_rate = 8000
num_channels = 2
bytes_per_sample = 2
muted = False

def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

async def listen():
    global args
    global loop
    global audio_queue

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(description="ASR Server",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parser])
    parser.add_argument('-u', '--uri', type=str, metavar='URL',
                        help='Server URL', default='ws://localhost:63000')
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    parser.add_argument('-r', '--samplerate', type=int, help='sampling rate', default=16000)
    args = parser.parse_args(remaining)
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    logging.basicConfig(level=logging.INFO)
    await run()

def callback(indata, frames, time, status):
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

async def run():
    global muted
    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 4000, device=args.device, dtype='int16',
                           channels=1, callback=callback) as device:

        async with websockets.connect(args.uri) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (device.samplerate))

            audio_queue.empty()
            while True:
                data = await audio_queue.get()
                await websocket.send(data)
                json_data = json.loads(await websocket.recv())
                if 'text' in json_data and len(json_data['text']) >= 4:
                    text = json_data['text']
                    if muted :
                        unmute_position = text.count('unmute')
                        if unmute_position > 0:
                            muted = False
                            continue
                    if not muted:
                        mute_position = text.count('mute')
                        if mute_position > 0:
                            muted = True
                            continue
                        else:
                            audio_queue.empty()
                            process_by_brain(text)

def process_by_brain(texted_speech):
    url = "http://localhost:63001/api/chat"
    wrapped_speech = [{'role':'user', 'content':texted_speech}]
    request_params = {'messages':wrapped_speech, 'model':'friday', 'stream':False}
    r = requests.post(url = url, json = request_params)
    data = r.json()
    if 'message' in data :
        try:
            parsed_message = json.loads(data['message']['content'])
            task = parsed_message['data']['task']
            success_message = parsed_message['data']['success']
            fail_message = parsed_message['data']['error']
            execute_task(task, fail_message, success_message)
        except ValueError:
            talk(data['message']['content'])

def talk(message):
    url = "http://localhost:63002/api/tts"
    request_params = {'':message}
    r = requests.post(url = url, json = request_params)
    audio_file = './tts.wav'
    with open(audio_file, 'wb') as f:
        f.write(r.content)
    subprocess.call(["aplay", audio_file])
    remove(audio_file)

def work():
    asyncio.run(listen())
    
def execute_task(task, fail_message, success_message):
    subprocess.run(["echo","task"])
    try :
        taskProcessor.execute_task(task)
        talk(success_message)
    except:
        talk(fail_message)

if __name__ == "__main__":
    work()

