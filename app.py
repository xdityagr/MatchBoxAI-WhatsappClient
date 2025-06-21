"""
MatchBox AI - WhatsApp AI Campaign Automation Service

A backend AI-powered service for managing influencer marketing campaigns via WhatsApp.  
This system handles campaign brief intake, creator discovery, outreach, and deal management, with support for both manual and automated workflows.

Features:
- Campaign brief processing via text, document, and voice message
- Influencer discovery and outreach automation
- Persistent AI-driven conversation management per WhatsApp user
- User-selectable workflow modes: Manual or AutoPilot
- Integrated with LangChain, Google Gemini, and WhatsApp Cloud API

Developed and maintained by Aditya Gaur / @xdityagr at Github / adityagaur.home@gmail.com
© 2025 MatchBox AI. All rights reserved.
"""


from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
import uvicorn
from dotenv import load_dotenv
import os
import json
import requests
from MatchBoxEngine.Model import ModelHandler
import time

from MatchBoxEngine.Query.parser import *
from MatchBoxEngine.Discovery import Engine
from MatchBoxEngine.Outreach import emailEngine
from MatchBoxEngine.Outreach.callingEngine import VapiClient


load_dotenv(override=True) 

app = FastAPI()

VERIFY_TOKEN = os.getenv("WEBHOOK_TOKEN")
ACCESS_TOKEN = os.getenv("GRAPH_ACCESS_TOKEN")
PHONE_ID = os.getenv("GRAPH_PHONE_ID")

print(ACCESS_TOKEN)

WELCOME_MESSAGE = """Hello {}! 👋
Welcome to *MatchBox AI* — _your all-in-one tool for discovering, contacting, and closing deals with creators._

📩 Send your campaign brief (Text, PDF, Doc, or Voice) — we'll find the perfect creators and lock your deals right here.

✨ You can:

- Reply `Get Started` to begin🔥 

- Reply `Connect Account` to link your MatchBox account 🔗

- Reply `Help` for support 🤖

Let's get this rolling! 🚀

"""

active_conversations = {} # later redis will be used.

WP_SYSTEM_PROMPT = """You are an AI conversation assistant for **MatchBox AI**, a platform that helps brands and agencies discover, contact, and close deals with influencers for their marketing campaigns — all from one place.
MatchBox AI automates the tedious parts of influencer marketing: from campaign brief intake to influencer discovery, outreach, negotiation, and deal management, with options for users to control or fully automate the process.
You operate via **WhatsApp** and must follow this structured conversation workflow.
You can talk to the user in whatever language they are talking to you, Can be Hindi & English.

Interaction Rules : 

1. Greetings : 
The User's name is '%s'
If the user sends a greeting (e.g. *Hi*, *Hello*, *Hey*, etc. ) as the first message, reply just with this template with user name filled in, nothing else : 

"
Hello <username>! 👋 
Welcome to MatchBox AI — your all-in-one tool for discovering, contacting, and closing deals with creators.

📩 Send your campaign brief (Text, PDF, Word Doc, or Voice Note) and we'll do the rest — from finding the perfect creators to managing deals right here on WhatsApp.

✨ You can:
- 🔥 Reply **Get Started** to begin  
- 🔗 Reply **Connect Account** to link your MatchBox account  
- 🤖 Reply **Help** for assistance  

Let's get started! 🚀
"

2. Unnecessary questions need not be answered unless the user wants help with something, or sends 'Help'. - if their reply does not fit what you have been told, You have slight freedom to reply but don't deviate much from what you are supposed to do or just kindly reply with a request that you are only capable of helping them with queries related to MatchBox AI & let you know if the user needs help getting started, etc.

3. If the user replies with :

- 'Get Started' → Ask:

  > "Before getting started, Would you like to proceed in **Manual Mode** (you'll review and control each step) or **AutoPilot Mode** (we'll handle everything end-to-end for you)?"

- 'Connect Account' → Respond:

  "Sure — please send your **MatchBox account email**.
  If your email is linked to an existing MatchBox account, we'll register this phone number with it.
  If not, we'll create a new MatchBox account for you using your name, phone number, and the email you provide."


- 'Help' → Enter Help mode, where you can answer user queries about the following and other MatchBox Related queries and questions, You can entertain other questions only for you to turn the conversation about and around MatchBox AI related queries, campaign creation, etc.

  - What is MatchBox AI
  - How campaign management works
  - How creator discovery and deal finalization happens
  - Available campaign management modes
  - Supported file types for briefs
  - How account linking works
    Provide clear, platform-specific answers only — no unrelated or open-ended conversations.


4. Campaign Brief Handling :

Once a mode is selected:

- Prompt for the campaign brief.
- Brief can be provided to you by the user as just normal text input like you always reciever or will be parsed from audio/pdf/document and be given to you as text in the input as "Parsed Text (from <source>)" parameter. Fields like title, description can be infered by you from the given data.
- if an input message is directly sent with a parsed text parameter or campaign brief in plain text, make sure the flow isn't broken, do process the brief and convert to JSON but also prompt about the Mode (auto/manual).
- You should strictly avoid replying with anything else but the extracted JSON. Nothing else. No extra commentary or text.
- Extract and convert it into this JSON structure:

{{
  "title" : "",
  "description": ""
  "company_name" : "",
  "contact_info: "",
  "category": "",
  "products_services": [],
  "creator_requirements": [],
  "budget_per_creator": "",
  "budget": "",
  "deliverables": [],
  "min_followers": 1000,
  "location": "",
  "tat": "",
  "notes": "",
  "num_creators_target": {{}},
  "platform": []
}}

* In **Manual Mode**, display the extracted data to the user, allow edits, and get confirmation before proceeding.
* In **AutoPilot Mode**, proceed directly with creator discovery and keep the user updated.

5. Always stay within this workflow unless in 'Help' mode.**

6. Maintain a friendly, joyous & helpful tone aligned with MatchBox AI's brand voice.

7. If the campaign is already processed, do not process another campaign or ask the user for campaign brief or send the get started template again.

"""


emailEngine.start_email_engine()

    # email_system.send_with_followup(
    #     to_email='adityagaur.home@gmail.com', # Replace with a test email you can reply from
    #     subject='Important Meeting Request - Test',
    #     message='Hello,\n\nI would like to schedule a meeting with you next week. Please let me know your availability.\n\nBest regards',
    #     timeout_hours=24
    # )


def init_search(campaign_info, callback, callback_arg):
    global emailEngine
    s  = Engine()
    s.start(campaign_info, callback, callback_arg, emailEngine)
    
def get_media_url(media_id):
    url = f"https://graph.facebook.com/v19.0/{media_id}"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print(json.dumps(response.json(), indent=4))
    media_url = response.json()["url"]
    return media_url


def download_media_file(media_url, save_as):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    response = requests.get(media_url, headers=headers)
    with open(save_as, "wb") as f:
        f.write(response.content)
    print(f"📥 Downloaded file as {save_as}")

def send_image(phone, image_url):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "image",
        "image": {
            "link": image_url
        }
    }
    response = requests.post(url, headers=headers, json=payload)

    print("📤 Reply status:", response.status_code)
    print("Response:", response.json())

def send_reply_text(phone, message_text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("📤 Reply status:", response.status_code)
    print("Response:", response.json())

def send_welcome_template(to_number, user_name):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": 'onboard_intro', 
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": user_name  # The value for {{Name}}
                        }
                    ]
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Status:", response.status_code)
    print("Response:", response.json())


recent_messages = set()

@app.api_route("/webhook", methods=["GET", "POST"])
async def whatsapp_webhook(request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):

    if request.method == "GET":
        if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
            return PlainTextResponse(hub_challenge)
        else:
            return PlainTextResponse("Verification failed", status_code=403)

    elif request.method == "POST":
        try:
            data = await request.json()
            # print(json.dumps(data, indent=2))

            # Check for incoming messages
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            reciever_name = value.get('contacts', [{'profile':{'name':'User'}}])[0]['profile']['name']
            messages = value.get("messages", [])

            # conv = init_model(reciever_name)
            # send_image('918368763700', 'https://scontent-dfw5-1.cdninstagram.com/v/t51.2885-19/491453887_18498027235044694_4000454013745828234_n.jpg?stp=dst-jpg_s640x640_tt6&_nc_ht=scontent-dfw5-1.cdninstagram.com&_nc_cat=110&_nc_oc=Q6cZ2QEPJ3vxFjVXI-pYViERec1WNM2PGvwmCA15rhVe6ga3pugEPv1QJ6vOj5nr_qWf0QE&_nc_ohc=imcjzlLLmaEQ7kNvwFUHRha&_nc_gid=dUbn-SwH-5bEQ8sDZ6SEYA&edm=AGqCYasBAAAA&ccb=7-5&oh=00_AfNFZDLO-joCItuzEKo_C8enKp1IghatLrFaDUnFbznoBw&oe=685BE63A&_nc_sid=6c5dea')

            if messages:
                msg = messages[0]
                message_id = msg.get("id")

                if message_id in recent_messages:
                    print("Duplicate webhook call ignored.")
                    return {"status": "duplicate"}


                recent_messages.add(message_id)

                if len(recent_messages) > 1000:
                    recent_messages.clear()


                from_number = msg.get("from")
                msg_type = msg.get("type")
                
                text_message = None
                parsed_text = None
                parsed_from = None

                if msg_type in ('media', 'image', 'document', 'audio'):
                    media_id = msg[msg_type]["id"]
                    fname = msg[msg_type].get('filename', None)            

                    extension = ''
                    if fname : 
                        extension = fname
                        
                    url = get_media_url(media_id)

                    if msg_type == 'audio':
                        extension = '.mp3'
                        parsed_from = 'Voice message audio (mp3)'
                        storage_id = f'storage_{msg_type}_{media_id}_{extension}'
                        audio_response = requests.get(url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
                        audio_bytes = audio_response.content
                        print(f"Audio bytes size: {len(audio_bytes)}")

                        resp, error = parse_audio_from_bytes(audio_bytes)
                        print("Parsed text:", resp)
                        print("Error:", error)
                
                        if error.get('error', None) is None and resp is not None:
                            parsed_text = resp
                            # send_reply_text(from_number, f"Did you say? : {parsed_text}")
                        else:
                            send_reply_text(from_number, f"We couldn't parse your audio file, Please try again.")
                            
                    elif msg_type == 'document':
                        storage_id = f'storage_{msg_type}_{media_id}_{extension}'
                        download_media_file(url, storage_id)  

                        if '.pdf' in fname:
                            parsed_from = 'PDF Document'
                            resp, error = parse_pdf(storage_id)
                            if not error.get('error', None) and not resp:
                                parsed_text = resp
                            else:
                                send_reply_text(from_number, f"There was an error parsing your PDF Document, Error: '{error}'")                                  

                        elif '.docx' in fname : 
                            parsed_from = 'Word Document'
                            resp, error = parse_docx(storage_id)
                            if not error.get('error', None) and not resp:
                                parsed_text = resp           
                            else:
                                send_reply_text(from_number, f"There was an error parsing your Word Document, Error: '{error}'")       
                        else:
                            send_reply_text(from_number, f"We couldn't parse your document '{fname}', Please try again.")

                    elif msg_type == 'image':
                        extension='.jpeg'

                elif msg_type == "text":
                    text_message = msg["text"]["body"]

                print(f'Parsed Text : {parsed_text}')
                if from_number not in active_conversations:                
                    # init model only once per user
                    mlh = ModelHandler()
                    conv, err = mlh.persist_chat_init(WP_SYSTEM_PROMPT % reciever_name)

                    if not err.get('error', None):
                        active_conversations[from_number] = conv
                    else:
                        pass
                
                conv = active_conversations[from_number]
                # if parsed_text : 
                    # input_builder(text_mess)
                input = text_message if text_message else f"Parsed Text (from {parsed_from}) : {parsed_text}"
                response = conv.run(input=input)
                response.strip()

                if response.startswith('```'):
                    if 'json' in response:
                        raw_text = response.lstrip("```json").replace('```', '')
                        print(raw_text)
                        campaign_info = json.loads(raw_text)

                        print(f'Campaign Info Extracted : {campaign_info}')
                        send_reply_text(from_number, f"""Thanks for the brief, {reciever_name}! ✨ The campaign has been created.\nI will get started with discovering the creators for you!\nI'll keep you updated on our progress every step of the way! 🚀""")
                        init_search(campaign_info, (send_reply_text, send_image), from_number)
                else:
                    print(response)
                    send_reply_text(from_number, response)

                # send_reply_text(from_number, WELCOME_MESSAGE.format(reciever_name))
                print(f"📩 From {from_number}: {text_message}")
        
        except Exception as e:
            print(f"Webhook processing error: {e}")
        finally:
            return {"status": "received"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

