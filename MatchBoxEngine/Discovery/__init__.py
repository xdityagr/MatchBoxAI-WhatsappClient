"""
MatchBoxAIEngine.DiscoveryEngine:
Discovery engine for finding influencers, starting negotiation process.

Developed and maintained by Aditya Gaur / @xdityagr at Github / adityagaur.home@gmail.com
© 2025 MatchBox AI. All rights reserved.
"""


import requests, json
from enum import Enum, auto
from dotenv import load_dotenv
import os
from MatchBoxEngine.Model import ModelHandler
from MatchBoxEngine.Outreach.callingEngine import VapiClient
from MatchBoxEngine.Query.parser import *

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv(override=True)

class Engine:
    def __init__(self):
        self.base_url = "https://instagram-social-api.p.rapidapi.com/v1/"
        self._api_key = os.getenv("RAPID_API_KEY")
        self.CONTACT_EMAIL = os.getenv("CONTACT_MAIL")
        
        self.post_headers = {
            "x-rapidapi-key": self._api_key,
            "x-rapidapi-host": "instagram-social-api.p.rapidapi.com"
        }
        self.mH = ModelHandler()
        self.min_followers = 1000

    def _search_hashtags(self, query=''):
        query_url = self.base_url + 'search_hashtags'
        querystring = {"search_query":query}
        response = requests.get(query_url, headers=self.post_headers, params=querystring)
        data = response.json()
        # print(data)
        root = data['data']['items']
        hashtags = []
        for hashtag_info in root: hashtags.append(hashtag_info['name'])
        return hashtags
    
    def _get_posts_by_hashtag(self, hashtag):
        url = self.base_url + 'hashtag'
        params = {'hashtag': hashtag}
        resp = requests.get(url, headers=self.post_headers, params=params).json()
        with open('hashtag_search.json', 'w') as f: json.dump(resp, f, indent=4)
        return resp['data']['items']
    
    def get_user_info(self, username_or_userid):
        url = self.base_url + 'info'
        params = {"username_or_id_or_url":username_or_userid}
        resp = requests.get(url, headers=self.post_headers, params=params).json()
        with open('user_info.json', 'w') as f: json.dump(resp, f, indent=4)
        return resp['data']

    def is_valid_influencer(self, user_data):
        if not user_data.get("is_business"):
            return False
        if not user_data.get("public_email"):
            return False
        if user_data.get("follower_count", 0) < self.min_followers:
            return False
        if user_data.get("media_count", 0) < 20:
            return False
        return True

    def _load_from_file(self, path):
        with open(path, 'r') as f:
            dataset = json.load(f)

        all_influencers = []
        for influencers in dataset.values():
            all_influencers.extend(influencers)

        unique_influencers = { influencer['id']: influencer for influencer in all_influencers }
        final_list = list(unique_influencers.values())
        return final_list
    

    def format_profiles_for_whatsapp(self, top_profile_data):

        if not top_profile_data:
            return "No creator profiles to display."

        whatsapp_message_parts = ["*✨ Top Creator Profiles ✨*\n"]

        for i, profile in enumerate(top_profile_data):
            username, full_name, public_email, category, media_count, follower_count = profile
            
            # Format each profile entry
            profile_entry = (
                f"🌟 *Creator #{i+1}*\n"
                f"👤 *Username:* @{username}\n"
                f"📛 *Name:* {full_name}\n"
                f"📧 *Email:* {public_email if public_email else 'N/A'}\n"
                f"🎯 *Category:* {category}\n"
                f"📸 *Posts:* {media_count:,}\n"
                f"📈 *Followers:* {follower_count:,}\n"
            )
            whatsapp_message_parts.append(profile_entry)

        # Join all parts with an extra newline for spacing between entries
        return "\n".join(whatsapp_message_parts)
    
    def start(self, campaign_info, call_backs, callback_arg, emailEngine):
        callback1, callback2_img = call_backs
        callback1(callback_arg, "Creator Search has started ...")
        category = campaign_info.get('category')
        self.min_followers = campaign_info.get('min_followers', 1000)

        hashtags = self._search_hashtags(category)
        
        print('\n\n\n\nHashtags : ')
        print(hashtags)
        print('\n\n\n')
        resp_hashtag = self.mH.instant_chat('You are a social media expert with advanced data analysis abilities whose one and only task is to filter out the best hashtags (Top 10) out of a bunch given to you as a python list, on the basis of how well they fit with the category provided & how probable it is for influencers to post to that hashtag. You only have to reply with JSON object as follows : {result:[]}',f"Category : {category}, Hashtags : {hashtags}")

        print('\n\n\n\n')
        print(resp_hashtag)
        print('\n\n\n')
        hashtags_filtered = llm_fromJSON(resp_hashtag).get('result')
        print(f'{hashtags_filtered=}')
        dataset_path = f'influencer_dataset_{category}.json'
        if os.path.exists(dataset_path):
            creators_list_raw = self._load_from_file(dataset_path)
        else:
            creators_list_raw = self.run_userprofile_processor(hashtags_filtered, max_users_per_hashtag=35, output_file=f'influencer_dataset_{category}.json')
        
        bios = [info['biography'] for info in creators_list_raw]
        print('here 1.')
        resp_bios = self.mH.instant_chat('You are a social media expert with advanced data analysis abilities whose one and only task is to filter out the bios out of a bunch given to you as a python list, on the basis of how well they fit with the category provided & how probable it is that the bio is from an influencer which should be considered a parameter of upmost priority. You only have to reply with JSON object with the indices of the best bios (Make sure to provide this indices the python way and make SURE that the indices do not exceed length of the list.) : {result:[]}',f"Category : {category}, Bios : {bios}")
        bios_filtered = llm_fromJSON(resp_bios).get('result')
        print(len(creators_list_raw), bios_filtered)
        final_creator_list = [creators_list_raw[idx] if idx < len(creators_list_raw) else creators_list_raw[idx-1] for idx in bios_filtered]
        print('here 2.')
        callback1(callback_arg, f"Creator Search has ended.\nSuccessfully found {len(final_creator_list)} creators.\nHere are the top few creators found :")
        pfp_links = [profile['profile_pic_url_hd'] for profile in final_creator_list[:4]]
        for link in pfp_links:
            callback2_img(callback_arg, link)
        
        top_profile_data = [(profile['username'], profile['full_name'], profile['public_email'], profile['category'], profile['media_count'], profile['follower_count']) for profile in final_creator_list[:4]]
        string_data = self.format_profiles_for_whatsapp(top_profile_data)
    
        callback1(callback_arg, f"{string_data}")
        if len(final_creator_list) > 1:
            callback1(callback_arg, f"Now, I will outreach to them via Mail, I will make sure to update you! 📨📩")
                            
            # OUTREACHING WILL START HERE : 
            self.emailEngine = emailEngine
            
            influencer =  final_creator_list[0]
            self.globals = {'campaign_info':campaign_info, 'influencer_info':{
                'name': influencer['full_name'], 
                'email': influencer['public_email'], 
                'niche': category, 
                'followers': influencer['media_count'], 
                'bio':influencer['biography'], 
                'engagement_rate': '78',
                'roi_score': 9.0,
                'language': 'English',
                'age_range': 'All'

            }}

            emailEngine.register_reply_callback(self.mail_callback)
            prompt, content = self._generate_email_prompt(self.globals.get('influencer_info'), self.globals.get('campaign_info'))
            resp = self.mH.instant_chat(prompt , content)
            if resp:
                subject, body = self._extract_emailctx(resp)
            

            emailEngine.send_email_with_followup(self.CONTACT_EMAIL, subject, body, timeout_hours=2)
            # emailEngine.send_email_with_followup('adityagaur.home@gmail.com', subject, body, timeout_hours=2)

            callback1(callback_arg, f"Mails have been sent to the creators, Waiting for them to get back! 📩✅")
            

    def _extract_emailctx(self, response_text):
        subject_match = re.search(r"<subject>(.*?)</subject>", response_text, re.DOTALL)
        body_match = re.search(r"<body>(.*?)</body>", response_text, re.DOTALL)

        subject = subject_match.group(1).strip() if subject_match else ""
        body_raw = body_match.group(1) if body_match else ""

        body = "\n".join(line.lstrip() for line in body_raw.splitlines())   
        return subject, body
    

    def _generate_email_prompt(self, influencer_info:dict, campaign_info:dict):
        # Update campaign_info variable assignments based on new structure
        campaign_title = campaign_info.get("title", "N/A")
        campaign_description = campaign_info.get("description", "N/A")
        campaign_budget = campaign_info.get("budget", "N/A")
        campaign_platforms = campaign_info.get("platform", "N/A")
        
        # New campaign_info fields
        campaign_category = campaign_info.get("category", "N/A")
        campaign_products_services = ", ".join(campaign_info.get("products_services", [])) if campaign_info.get("products_services") else "N/A"
        campaign_creator_requirements = ", ".join(campaign_info.get("creator_requirements", [])) if campaign_info.get("creator_requirements") else "N/A"
        campaign_budget_per_creator = campaign_info.get("budget_per_creator", "N/A")
        campaign_deliverables = ", ".join(campaign_info.get("deliverables", [])) if campaign_info.get("deliverables") else "N/A"
        campaign_min_followers = campaign_info.get("min_followers", "N/A")
        campaign_location = campaign_info.get("location", "N/A")
        campaign_tat = campaign_info.get("tat", "N/A")
        campaign_notes = campaign_info.get("notes", "N/A")
        # num_creators_target is a dict, so handle it carefully if it needs to be detailed in the prompt
        campaign_num_creators_target = campaign_info.get("num_creators_target", {})
        # Flatten num_creators_target for prompt if needed, otherwise just represent as string
        num_creators_target_str = str(campaign_num_creators_target)
        
        company_name = campaign_info.get("company_name", "N/A")
        company_contact_info = campaign_info.get("contact_info", "N/A")

        # Update influencer_info variable assignments based on new structure
        influencer_name = influencer_info.get("name", "N/A") # This will be full_name from source
        influencer_email = influencer_info.get("email", "N/A") # This will be public_email from source
        influencer_niche = influencer_info.get("niche", "N/A") # This will be category from source
        influencer_followers = influencer_info.get("followers", "N/A") # This will be media_count from source
        influencer_engagement_rate = influencer_info.get("engagement_rate", "N/A")
        influencer_bio = influencer_info.get("bio", "N/A") # This will be biography from source
        influencer_roi_score = influencer_info.get("roi_score", "N/A")
        influencer_language = influencer_info.get("language", "N/A")
        influencer_age_range = influencer_info.get("age_range", "N/A")
        
        # Removed 'influencer_past_collabs' as per new structure

        # Update the prompt with the new agent name
        prompt = f"""You are an automation bot from MatchBox AI Agent (use this as your name) made for writing emails to influencers for a brand/agency. Please make sure to include every detail about the campaign & make sure to write it well so that the creator is impressed. The tone should be respectful, confident, and clear. The email should reflect leadership, professionalism, and purpose. Your respone must include a subject line, appropriate greeting, a concise body with key information or requests, and a professional closing signature. At the end, Your goal is to get the contact number of the influencer for further negotiation & finally a deal. Make use of tags in your response, do not provide response out of these tags. Use <subject> tag and wrap the generated subject in it and use a closing </subject> tag as well. Move to next line use <body> tag for the whole body and end with a </body> tag."""

        # Update the content string with new/changed campaign and influencer info
        content = f"""Write a formal and courteous email to the influencer '{influencer_name}' (Can be a name or a username) to integrate with the marketing campaign.
Campaign info is as follows:
Campaign name - {campaign_title}
Campaign Description - {campaign_description}
Campaign category - {campaign_category}
Campaign products/services - {campaign_products_services}
Campaign platforms - {campaign_platforms}
Campaign budget - {campaign_budget}
Campaign budget per creator - {campaign_budget_per_creator}
Campaign deliverables - {campaign_deliverables}
Campaign minimum followers - {campaign_min_followers}
Campaign location - {campaign_location}
Campaign TAT - {campaign_tat}
Campaign notes - {campaign_notes}
Campaign target number of creators - {num_creators_target_str}
Campaign creator requirements - {campaign_creator_requirements}

Here is the influencer info you will be writing to:
Email - {influencer_email}
Influencer niche(s) - {influencer_niche}
Number of followers - {influencer_followers}
Engagement rate - {influencer_engagement_rate}
Their Bio/Description - {influencer_bio}
ROI Score - {influencer_roi_score}
Preferred language - {influencer_language}
Their audience's age range - {influencer_age_range}
"""
        return prompt , content
    

    def mail_callback(self, sender_email, subject, body, original_sent_info):
        print(f"\n📧 Reply from {sender_email} - Subject: {subject}")
        try:
            prompt = """You are an automation bot from MatchBox AI (use this as your name) made for analyzing the reply of the client (influencer) to a mail which was sent in order to get their phone number to proceed further negotiation & finally get a deal. You must analyze their reply & give out only a tag as a response, Three case can happen: [1] if their reply is a query & they want to ask something, use tag <follow-up-reply> [2] If they deny the deal, return tag <follow-up-cancel>. [3] If they share their contact info (Their phone number) use tag <init-call> with their correct phone number next to it with contry code (Mostly india).
            Your reponse must contain only 1 tag. The mail will be provided in the content. If none of the cases are met or error occurs, return only an <error> tag with enclosing the error info in it."""
            mail = f"""Subject : {subject}
        {body}"""
            
            resp = self.mH.instant_chat(prompt, mail)
            print(f"LLM Response: {resp}")

            if resp : 
                tag, num = self.emailEngine._process_ifc(resp)
                print(tag, num)
                print("\n\n\n CHECK OUT THE TAGS ABOVE.")
                if tag == '<init-call>' and num:
                    vapi_client = VapiClient()
                    try:
                        updated_assistant_info = vapi_client.update_assistant_prompt(self.globals.get('campaign_info'), self.globals.get('influencer_info'))
                        print("\n--- Assistant Update Complete ---")
                    except Exception as e:
                        print("Exiting due to assistant update failure.")
                        exit()

                    try:
                        CALLING_NUMBER = os.getenv("CALLING_NUMBER")

                        call_details = vapi_client.initiate_call(CALLING_NUMBER, '')
                        print("\n--- Call Initiation Complete ---")

                        return True
                    except Exception as e:
                        print("Exiting due to call initiation failure.")
                        print(f'{e}')
                        return False
                    
        except Exception as e:
            print(f"ModelHandler processing failed: {e}")



    def fetch_user_with_caption(self, user_id, caption_text):
        user_data = self.get_user_info(user_id)
        user_data['post_caption_text'] = caption_text
        return user_data
    
    def run_userprofile_processor(self, hashtags, max_users_per_hashtag=30, output_file='influencer_dataset.json'):
        
        from collections import defaultdict
        dataset = defaultdict(list)
        dataset_lock = threading.Lock()

        def process_hashtag(hashtag):
            print('Processing Hashtags ')
            print(f"[+] Fetching posts for #{hashtag}")
            try:
                posts = self._get_posts_by_hashtag(hashtag)
                user_caption_pairs = []
                for post in posts:
                    try:
                        user_id = post['caption']['user']['id']
                        caption_text = post['caption'].get('text', '')
                        user_caption_pairs.append((user_id, caption_text))
                    except KeyError:
                        continue

                # Remove duplicate users, keep only one caption per user (first one encountered)
                unique_pairs = {}
                for uid, caption in user_caption_pairs:
                    if uid not in unique_pairs:
                        unique_pairs[uid] = caption

                selected_pairs = list(unique_pairs.items())[:max_users_per_hashtag]

                with ThreadPoolExecutor(max_workers=5) as user_executor:
                    user_futures = []
                    for uid, caption_text in selected_pairs:
                        user_futures.append(user_executor.submit(self.fetch_user_with_caption, uid, caption_text))

                    for user_future in as_completed(user_futures):
                        user_data = user_future.result()
                        # Basic Filtering.
                        if self.is_valid_influencer(user_data):
                            with dataset_lock:
                                dataset[hashtag].append(user_data)
                                print(f"[+] Taken {user_data.get('username')} — meets criteria.")
                        else:
                            print(f"[x] Skipped {user_data.get('username')} — doesn't meet criteria.")

                        # with dataset_lock:
                        #     dataset[hashtag].append(user_data)

            except Exception as e:
                print(f"[!] Error processing #{hashtag}: {e}")

            return f"Done with #{hashtag}"

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_hashtag, tag) for tag in hashtags]
            for future in as_completed(futures):
                print('prosessing a-d-sd-asd')
                print(future.result())

        all_influencers = []
        for influencers in dataset.values():
            all_influencers.extend(influencers)

        unique_influencers = { influencer['id']: influencer for influencer in all_influencers }
        final_list = list(unique_influencers.values())
        results = {'creators':final_list}
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=4)
        print(f"\n[✓] All data saved to {output_file}")

        return final_list

