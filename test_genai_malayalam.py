import google.generativeai as genai
from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Malayalam normalizer
normalizer = IndicNormalizerFactory().get_normalizer('ml')

# Configure the API key from environment variable
api_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

# Example Malayalam text
malayalam_text = """
മലയാളം ഒരു ദ്രാവിഡ ഭാഷയാണ്. ഇന്ത്യയിലെ കേരള സംസ്ഥാനത്തിന്റെ ഔദ്യോഗിക ഭാഷയാണിത്.
"""

# Normalize the Malayalam text
normalized_text = normalizer.normalize(malayalam_text)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

try:
    # Generate a response
    response = model.generate_content(f"Translate this Malayalam text to English: {normalized_text}")
    print("Original Malayalam text:", malayalam_text)
    print("\nTranslation:", response.text)
except Exception as e:
    print("Error:", str(e))
    print("Make sure you've set up your API key correctly!")