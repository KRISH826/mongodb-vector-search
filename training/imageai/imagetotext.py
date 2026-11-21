from langchain_nvidia_ai_endpoints import ChatNVIDIA
from pathlib import Path
from langchain_core.messages import HumanMessage
import os
import base64

print(list(Path("training/images").glob("*")))
client = ChatNVIDIA(
  model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
  api_key="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",
  temperature=0.6,
  top_p=0.95,
  max_completion_tokens=65536,
)

MEDIA_TYPES = {".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".png": "image/png"}

def describe_image(image_path:str, prompt: str) -> str:
    path = Path(image_path)
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    media_types = MEDIA_TYPES[path.suffix.lower()]
    
    message = HumanMessage(
        content= [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url":f"data:{media_types};base64,{data}"}
            }
        ]
    )
    
    response = client.invoke([message])
    return str(response.content)

if __name__ == "__main__":
    describeImage = describe_image("training/images/page1_img.jpeg", "Describe the image perfectfully")
    print(describeImage)