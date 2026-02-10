import runpod
import os
from dotenv import load_dotenv

def generate_video():
    #This will NOT work - trying to create new endpoints
    load_dotenv()

    runpod.api_key = os.getenv("RUNPOD_API_KEY")
    data = {
        'input': {"prompt": "A cinematic scene on a quiet city rooftop during heavy rain at dusk. Dark storm clouds fill the sky while rain falls steadily across wet buildings and reflective streets. Puddles shimmer with soft reflections, and distant city lights glow through the mist. Wind moves loose fabric, plants, and small objects naturally. A young person stands at the rooftop center and slowly raises their hand toward the sky. As they do, the rain begins to slow, and the thick storm clouds start to part in a circular opening above them. Warm golden sunlight breaks through the clouds, creating dramatic volumetric light rays that illuminate the scene. The surrounding rain stops within the light circle while the rest of the city remains under rainfall. Water droplets sparkle in the sunlight, steam rises softly from warm surfaces, and the sky transitions from dark gray to bright blue with glowing clouds. Ultra-realistic cinematic atmosphere, dramatic weather transition, natural rain physics, wet surface reflections, volumetric sunlight, atmospheric depth, soft lens flare, HDR lighting, smooth motion, emotional mood, slow cinematic camera movement, photorealistic textures, global illumination, award-winning cinematography, 4K quality..", 
                  "duration": 5, 
                  "enable_prompt_expansion": False, 
                  "negative_prompt": "low quality, blurry, pixelated, noise, grain, flickering, frame glitches, jittery motion, motion artifacts, cartoon, anime style, illustration, CGI look, unrealistic rain, unrealistic clouds, oversaturated colors, flat lighting, overexposed, underexposed, plastic textures, distorted buildings, warped perspective, duplicate objects, unnatural physics, floating objects, text, watermark, logo, subtitles, borders", 
                  "seed": -1, 
                  "shot_type": "single", 
                  "size": "1280*720"}
    }

    #This will work - running inference on endpoints
    endpoint = runpod.Endpoint("wan-2-6-t2v")
    result = endpoint.run_sync(data)
    print(result)

if __name__ == "__main__":
    generate_video()
    print("main.py called...")