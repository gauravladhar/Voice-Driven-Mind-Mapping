# MappedOut | Voice-Driven-Mind-Mapping with AI

🚀 Introduction

In today's fast-paced world, ideas often come and go faster than we can capture them. Whether you're brainstorming, journaling, or taking class notes, the process of organizing your thoughts shouldn't slow you down. That's why we built MappedOut — a voice-powered web application that instantly transcribes speech and converts it into an interactive mind map, helping users visually structure their ideas with the power of AI.

Our project was developed during a hackathon with the goal of streamlining ideation, note-taking, and personal expression. We wanted to make it easier for users to externalize and organize their thoughts by simply speaking, without the burden of typing or structuring. Powered by OpenAI Whisper, Neo4j, and an intuitive React frontend, OutOfYourMind offers a seamless, intelligent, and creative experience.

🛠️ Tech Stack

| Layer        | Tools Used                                 |
| ------------ | ------------------------------------------ |
| 🧠 AI        | OpenAI Whisper (Speech-to-Text)            |
| 🎯 Frontend  | React, JavaScript, CSS                     |
| ⚙️ Backend   | FastAPI (Python)                           |
| 🧩 Database  | Neo4j (Graph-based semantic node storage)  |
| 🔐 Auth      | Firebase Authentication                    |
| 🧪 Dev Tools | VSCode, Ngrok, Python virtual environments |

✨ Features

🎤 Speech to Mind Map – Speak your thoughts, and see them organized into a connected graph.

🧠 Semantic Node Mapping – Related ideas are intelligently linked using Neo4j.

🔐 User Authentication – Secure login and user isolation using Firebase.

🌐 Full-Stack Integration – React frontend communicates seamlessly with Python-based FastAPI backend.

⚡ Real-Time Feedback – Fast audio transcription and dynamic rendering of user data.

📦 Getting Started
1. Clone the Repository
<pre>git clone https://github.com/gauravladhar/Voice-Driven-Mind-Mapping.git
cd Voice-Driven-Mind-Mapping</pre>

2. Backend Setup (FastAPI + Whisper)
<pre>pip install -r requirements.txt
  
Or manually:
  
pip install fastapi uvicorn openai-whisper torch neo4j ffmpeg-python python-dotenv python-multipart</pre>

📦 Run the FastAPI Server
<pre>uvicorn main:app --reload</pre>

3. Frontend Setup (React)
<pre>cd client
npm install
npm start</pre> 
