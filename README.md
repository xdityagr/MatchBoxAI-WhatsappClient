# MatchBox AI — WhatsApp Client

An AI-powered backend service that enables brands and agencies to manage influencer marketing campaigns end-to-end through WhatsApp.  
Built for ease of use, MatchBox AI lets users send a simple WhatsApp message with their campaign brief and automatically discovers, connects, and closes deals with the right creators.

---

## Features : 

- 📩 **WhatsApp-based Campaign Brief Intake** (Text, PDFs, Docs, Voice Notes)
- 🔍 **1-Click Creator Discovery via APIs**
- 🤖 **AutoPilot Campaign Flow** (completely automated, or manual step-by-step mode)
- 🎛️ **Multi-brand Campaign & Deal Management**
- 📊 **Campaign Performance Analytics & ROI Estimator**
- 📝 **Creator CRM with Engagement & Deal Tracking**
- 📄 **Invoice & Contract Handling via WhatsApp**
- 🌐 **Pluggable APIs for Meta, Twilio, GPT-4o, RapidAPI, Vapi, and more**

---

## 🖥️ Tech Stack

- **Python 3.11+**
- **FastAPI**
- **LangChain + Google Gemini / GPT-4o**
- **WhatsApp Cloud API (Meta)**

---

## 💾 Getting Started

### 📦 Install Dependencies
```bash
pip install -r requirements.txt
```

## 🗝️ Set Environment Variables
Create a .env file in the root directory:
```env
# === MatchBox AI Core Service Keys ===

GOOGLE_API_KEY=your_google_gemini_api_key_here
GRAPH_ACCESS_TOKEN=your_whatsapp_cloud_api_access_token_here
GRAPH_PHONE_ID=your_whatsapp_business_phone_id_here
WEBHOOK_TOKEN=your_webhook_verification_token_here
HF_API_KEY=your_huggingface_api_key_here
RAPID_API_KEY=your_rapidapi_key_here

# === Calling / Voice API Integrations (Optional for Outbound Calls & Assistants) ===

CALLING_API=your_calling_api_key_here   # For Vapi / Exotel / Plivo outbound calls
ASSISTANT_ID=your_voice_assistant_id    # If using a voice assistant bot service
PHONE_ID=your_voice_call_phone_id       # For outbound calls via API (if separate from GRAPH_PHONE_ID)
TWILIOAUTHTOKEN=your_twilio_auth_token  # Only if integrating Twilio

# === Business Config ===

CALLING_NUMBER=+919999999999            # Outbound caller ID number
CONTACT_MAIL=support@matchboxai.in      # Support or admin email for campaign clients
```

## 🚀 Run the Server
```bash
uvicorn app:app --reload
```


## License

This project is licensed under the [GPL License](LICENSE).

## Contact

For questions or feedback, please contact:

- **Email**: adityagaur.home@gmail.com
- **GitHub**: [xdityagr](https://github.com/xdityagr)

** Made with _<3_ In **India!**
