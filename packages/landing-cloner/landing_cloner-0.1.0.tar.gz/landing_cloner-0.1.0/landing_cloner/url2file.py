import docker


def url2singlefile(url:str) -> str:
    client = docker.from_env()  # Create a client instance from environment variables
    
    try:
        image = client.images.pull("capsulecode/singlefile")  # Pull the required Docker image
        
        raw_output = client.containers.run(image, url)  # Run the image in a new container
        
        html_content = raw_output.decode() # Get HTML content from the running container
    except docker.errors.APIError as e:
        print(f"Docker error: {e}")
        raise "Downloading error"
    
    return html_content

