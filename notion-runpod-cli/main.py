import runpod

def generate_video():
    # This will NOT work - trying to create new endpoints
    runpod.api_key = ""

    data = {
        'input': {"prompt": "A stylish young male artist is spray-painting a colorful mural of flowers on a brick wall in a sunny city alleyway. Suddenly, the painted flowers magically detach from the wall and transform into glowing, semi-transparent 3D butterflies. The artist looks surprised and then delighted, reaching out his hand to let one butterfly land on his finger. The scene is bathed in warm natural sunlight, dust motes dancing in the air. Vibrant colors, smooth motion, magical realism, award-winning cinematography.", "duration": 5, "enable_prompt_expansion": False, "negative_prompt": "", "seed": -1, "shot_type": "single", "size": "1280*720"}
    }

    # # This will work - running inference on endpoints
    endpoint = runpod.Endpoint("wan-2-6-t2v")
    result = endpoint.run_sync(data)
    print(result)

if __name__ == "__main__":
    generate_video()
    print("main.py called...")