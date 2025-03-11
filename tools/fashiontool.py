from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os
import base64
from openai import OpenAI

class DressVisionInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="User provided description about his dressing style")

class DressVisionTool(BaseTool):
    name: str = "Dress_vision_tool"
    description: str = "This tool find the user dressing style and sense based on the user provided images."
    args_schema: Type[BaseModel] = DressVisionInput
    client: Optional[str] = None

    def __init__(self):
        super().__init__()  # Call the parent class's __init__ if necessary
        load_dotenv()
        self.client = OpenAI()

    

    def _run(self, argument: str) -> str:

        # Directory containing images
        image_directory = os.path.join(os.getcwd(),"images")

        # Dictionary to store base64-encoded images
        base64_images = []
        contents_list=[]

        # Supported image formats
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]

        # Iterate through all files in the directory
        for filename in os.listdir(image_directory):
            # Check if the file is an image
            if any(filename.lower().endswith(ext) for ext in supported_formats):
                # Full path to the image
                image_path = os.path.join(image_directory, filename)

                # Read the image file and encode it in base64
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")

                # Store the base64-encoded image in the dictionary
                base64_images.append(base64_image)

        print("Successfully Converted the images to base64 format.")
        user_query=f"""Create a detailed fashion analysis report by analyzing my images.
                        The report start with brief summary about my fashion followed by listing
                        fashion factors(user category, user personal style, body type and proportions, color preference
                        and skin tone, fabric and material preferences and accessories preferences)
                        with detailed explanation under each fashion factor. At last list all important key fashion terms under name of User sutable fashion terms.
                        please find below mentioned small description about my dressing style for your reference.
                        description : {argument}
                        """ 
        contents_list.append({"type": "text","text":user_query})

        for i in base64_images:
            contents_list.append({"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{i}"}})
   
       
        response = self.client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": """You are a highly skilled fashion designer and personal stylist 
             specializing in analyzing user images to determine the below mentioned and fashion factors i,e
             - user category(Identify the user comes under(Men's category or Boy's category or Women's category or Girl's category))
             - user personal style(Identify the user unique dressing style and sense)
             - body type and proportions(Identify the user body type (hourglass, pear, apple, rectangle, inverted triangle))
             - color preference and skin tone(Identify user favorite color palettes)
             - fabric and material preferences(Identify the type of fabrics the user mostly to wears (eg: cotton, silk, denim, leather, wool, etc.) and their lifestyle suitability)
             - accessories preferences(Identify what accessories user using. If nothing found, suggest accessories based on the user dressing style and sense)"""},
            {"role": "user", "content":contents_list}
        ])
        return response.choices[0].message.content