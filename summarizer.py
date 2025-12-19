import os
from openai import OpenAI

def summarize(text):
    """
    Summarizes the given text using OpenAI API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file with your key.")
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using a capable model
            messages=[
                {"role": "system", "content": "You are a specialized financial analyst assistant. Your goal is to extract stock market information, ticker symbols, and financial analysis from video transcripts. You must output your summary in Chinese."},
                {"role": "user", "content": f"Please summarize the following transcript in Chinese. \n\nFocus on:\n1. Key stock tickers mentioned.\n2. Market sentiment (Bullish/Bearish).\n3. Key financial data or events.\n4. Actionable investment advice implications.\n\nTranscript:\n{text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during summarization: {e}"
