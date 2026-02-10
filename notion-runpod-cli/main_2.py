import runpod
import os
from dotenv import load_dotenv

def generate_video():
    #This will NOT work - trying to create new endpoints
    load_dotenv()

    runpod.api_key = os.getenv("RUNPOD_API_KEY")

    data = {
        "input": {
            "prompt": (
                "A confident person stands inside a massive underground vault, "
                "slowly turning a heavy steel wheel to unlock it. As the vault door "
                "creaks open, an overwhelming flood of glowing gold coins and bars "
                "bursts out, cascading forward in slow motion and filling the room. "
                "The person steps back in awe, shielding themselves as gold pours "
                "past their feet, light reflecting brilliantly off every surface. "
                "Cinematic lighting, dramatic shadows, ultra-detailed gold reflections, "
                "smooth motion, epic scale, magical realism, award-winning cinematography."
            ),
            "duration": 5,
            "enable_prompt_expansion": False,
            "negative_prompt": "",
            "seed": -1,
            "shot_type": "single",
            "size": "1280*720"
        }
    }

    # Run inference on an existing endpoint
    endpoint = runpod.Endpoint("wan-2-6-t2v")
    result = endpoint.run_sync(data)

    print(result)

if __name__ == "__main__":
    generate_video()
    print("main.py called...")