gemini_api='AIzaSyAxrDqHcwX0UCoGiURzxHCgdKiiF71pu6A'
# pip install google-generativeai
api_key='AIzaSyDY9wjuzr7N4TXDF6f93JUzDOId6iZhha0'
genai.configure(api_key=api_key)
genmini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
import google.generativeai as genai
response = genmini_model.generate_content([image, """You are an exprt in describing an image and you are as assistant tasked with detailed description of image or text for retrieval. \
    These summaries will be embedded and used to retrieve the raw text elements \
    Give a detailed description and summary  of the text or an  image   that is well optimized for retrieval. """])