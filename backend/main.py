from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI()
llm = ChatOpenAI(api_key=openai_api_key, model_name="gpt-3.5-turbo")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CityRequest(BaseModel):
    city_name: str

def get_weather(city_name: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={openweather_api_key}&units=imperial"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="City not found")
    weather_data = response.json()
    return {
        "location": weather_data['name'],
        "temperature": weather_data['main']['temp'],
        "condition": weather_data['weather'][0]['description'],
        "wind_speed": weather_data['wind']['speed'],
        "humidity": weather_data['main']['humidity']
    }

def get_response_from_openai(weather_report: str):
    prompt_template = PromptTemplate(
        input_variables=["weather_report"],
        template="Provide a detailed report of the weather with the information. After that, recommend clothes to wear:\n{weather_report}"
    )
    sequence = prompt_template | llm
    response = sequence.invoke({"weather_report": weather_report})
    return response

@app.post("/get_weather/")
async def get_weather_report(request: CityRequest):
    weather_report = get_weather(request.city_name)
    weather_report_str = (
        f"Location: {weather_report['location']}\n"
        f"Temperature: {weather_report['temperature']}°F\n"
        f"Condition: Current weather condition: {weather_report['condition']}\n"
        f"Wind Speed: {weather_report['wind_speed']} mph\n"
        f"Humidity: {weather_report['humidity']}%"
    )
    openai_response = get_response_from_openai(weather_report_str)
    return {"weather_report": weather_report_str, "openai_response": openai_response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
