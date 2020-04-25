import argparse
import boto3
import sys
import json

from .channel import Channel
from .ladder_generator import Ladder_generator
from .errors import MissingStreamError, WrongCodecError

def extract_data(data):
    """ Extracts and validates values of json object generated by ffprobe.
    """
    supported_codecs = ['aac', 'h264']
    
    streams = json.loads(data)['streams']
    if len(streams) != 2:
        raise MissingStreamError(streams)

    if streams[0]['codec_name'] not in supported_codecs:
        raise WrongCodecError(streams[0]['codec_name'])
    
    # Identify wich stream contains audio/video
    audio = streams[0] if streams[0]['codec_name'] == 'aac' else streams[1]
    video = streams[0] if streams[0]['codec_name'] == 'h264' else streams[1]

    return {
            'audio_codec': audio['codec_name'],
            'audio_sample_rate': int(audio['sample_rate']),
            'audio_bitrate': int(audio['bit_rate']),
            'video_codec': video['codec_name'],
            'video_profile': video['profile'],
            'video_width': int(video['width']),
            'video_height': int(video['height']),
            'video_fps': int(video['r_frame_rate'].split('/')[0]),
            'video_bitrate': round(int(video['bit_rate'])/1000)
           }


def debug(key, data, inputType):
    data = extract_data(data)
    print("Stream key is \"{key}\" \n".format(key=key))
    print("Input data is: \n================\n")
    print(json.dumps(data, indent=4, sort_keys=True))
    print("\n==============\n")
    print("Generating channel object...\n")
    channel = Channel(key, data['video_width'], data['video_height'], data['video_fps'],\
                        data['video_bitrate'], data['audio_bitrate'], None)
    print("Channel status is: {status}".format(status=channel.check_status()))
    print("\nProposed video ladder is: \n================\n")
    ladder = Ladder_generator()
    print(json.dumps(ladder.generate(data['video_height'], data['video_bitrate'], \
                                        data['video_fps'], data['audio_bitrate'], []),  indent=4, sort_keys=True))
    print("\n==============\n")


def create_channel(key, data, inputType):
    """ Create and start a AWS Medialive Channel """
    data = extract_data(data)
    channel = Channel(key, data['video_width'], data['video_height'], data['video_fps'],\
                    data['video_bitrate'], data['audio_bitrate'], inputType)
    channel.create_channel_input()
    channel.create_channel()
    
def main():
    parser = argparse.ArgumentParser(description='Dev.')
    parser.add_argument('--action', action='store', type=str, required=True, choices=['Create', 'Delete'])
    parser.add_argument('--key', type=str)
    parser.add_argument('--data', type=str)
    parser.add_argument('--input', type=str, required=False, choices=['Pull', 'Push'])
    parser.add_argument('--debug', type=bool)
    args = parser.parse_args()
    
    if args.action == 'Create':
        if args.data == None or args.key == None:
            parser.error("Action \"Create\" needs --data and --key flags. Check -h or --help for more info.")
        if args.input != None:
            args.input = "Pull"
        if args.debug:
            debug(args.key, args.data, args.input)
        #create_channel(args.key, args.data, inputType)
    
    
