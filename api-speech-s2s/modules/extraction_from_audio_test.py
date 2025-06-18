from modules.extraction_from_audio import run_extract_entities_from_audio
import json

if __name__ == "__main__":

    # Agregamos el nombre del bucketgs
    path_to_file = "gs://speech_s2s_bucket/20250112_110549_Skill_V02_RipleyB_PrestamosNS_0549037D6D4AE088_113651_986585843.mp3"
    my_list = run_extract_entities_from_audio(path_to_file)
    print(my_list)