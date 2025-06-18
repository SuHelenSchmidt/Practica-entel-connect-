from audio_list import get_files
import json

if __name__ == "__main__":
    nombre_bucket = "speech_s2s_bucket"
    my_list = get_files(nombre_bucket)

    for data in my_list:
        print(json.dumps(data, indent=4))
