import runpod

def generate_video():
    # This will NOT work - trying to create new endpoints
    runpod.api_key = "your-restricted-api-key"

    # This will work - running inference on endpoints
    endpoint = runpod.Endpoint("YOUR_ENDPOINT_ID")
    result = endpoint.run_sync({"input": {"prompt": "..."}})

if __name__ == "__main__":
    # generate_video()
    pass