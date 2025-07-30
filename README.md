# 🩺 VoxMed – Voice-Based AI Health Assistant

**VoxMed** is a real-time, voice-enabled medical assistant that helps patients communicate naturally while providing doctors with structured, meaningful insights. Built using OpenAI’s GPT-4o Realtime API and WebRTC, VoxMed transforms spoken conversations into actionable medical summaries—all through a web interface.

---

## 🔍 What It Does

- 🎙️ **Real-Time Voice Interaction**  
  Patients speak naturally with an AI assistant, which responds via voice in real time.

- 🧠 **Structured Health Data Extraction**  
  At the end of a session, VoxMed generates:
  - A **natural-language summary** of the encounter
  - A **structured report** of symptoms, medications, durations, and relevant details

- 👨‍⚕️ **Doctor/Patient Roles**  
  Authenticated users are assigned roles, allowing doctors to review session histories and patients to interact with the AI.

- 📂 **Session Storage & Review**  
  All sessions are saved to a MongoDB database and viewable by doctors, including natural summaries and structured data.

---

## ⚙️ Tech Stack

| Layer         | Technology                            |
|--------------|----------------------------------------|
| Frontend      | WebRTC, JavaScript, HTML/CSS           |
| Backend       | Flask (Python)                         |
| AI            | OpenAI GPT-4o Realtime API             |
| Database      | MongoDB                                |
| Auth          | Role-based (Patient / Doctor)          |

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/voxmed.git
cd voxmed
```

### 2. Install the Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key
MONGO_URI=your-mongodb-uri
SECRET_KEY=your-secret-key
```

### 4. Run the Flask Server

```bash
python -m src.main
```

## 📸 Features in Action

- 🎙️ Real-time voice-to-voice interaction with GPT-4o  
- 📝 Transcripts displayed live on the web interface  
- 🧠 Automatic generation of structured medical summaries  
- 🗂️ Doctor dashboard with session history and details  
- 🌐 Multilingual and customizable voice support

## 📅 Roadmap
- PDF export of summaries
- Analytics dashboard for doctors

## 📫 Contact

If you’re interested in collaborating, contributing, or deploying VoxMed:
- GitHub: @Scotchex
- [LinkedIn: ](https://www.linkedin.com/in/arda-serhatli/)