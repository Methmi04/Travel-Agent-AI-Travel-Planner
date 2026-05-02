# ✈️ TravelAgent – AI Travel Planner

An AI-powered travel planning web application that generates personalized itineraries, budgets, and travel recommendations based on user preferences.

---

## Overview

Planning a trip can be time-consuming and overwhelming.  
**TravelAgent simplifies this process** by using AI to instantly generate a complete travel plan tailored to the user.

Users can enter details such as destination, budget, duration, travel style, and interests, and receive a fully structured itinerary within seconds.

---

## Key Features

- 🗺 Personalized trip planning based on user input  
- 📅 Day-by-day detailed itinerary generation  
- 🏨 Accommodation suggestions based on budget  
- 🍽 Local food and experience recommendations  
- 💰 Budget breakdown in LKR  
- 💬 Interactive AI chat interface  
- 🕓 Chat history saving  
- 🎯 Custom travel preferences support  

---

## 🛠 Tech Stack

- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI Model:** Groq (LLaMA 3.3 70B)  
- **Storage:** JSON (chat history)  

---

## ⚙️ How It Works

1. User enters travel preferences (destination, budget, duration, etc.)  
2. The app structures the input into a travel profile  
3. The profile is sent to the Groq LLM  
4. AI generates a complete personalized travel plan  
5. The result is displayed in an interactive chat UI  

------------------------

## API Setup

This project uses the Groq API for AI responses.

👉 Get your free API key here:  
https://console.groq.com

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_api_key_here
