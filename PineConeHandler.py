import json
import os
import re
import uuid
from datetime import datetime
import google.generativeai as genai
import streamlit
from dotenv import  load_dotenv
from pinecone import Pinecone

load_dotenv()

class PineConeHandler:
    def __init__(self , index_name : str):
        pc = Pinecone(api_key= os.getenv('PINECONE_API_KEY'))
        if not pc.has_index(index_name):
            pc.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}
                }
            )

        self.index = pc.Index(index_name)

    def generate_tags(self , prompt : str):
        # Predefined tags - both general and specific
        tags = [
            # General categories
            "Technical", "Cultural", "Sports", "Workshop", "Seminar",
            "Competition", "Networking", "Career", "Entertainment",
            "Educational", "Creative", "Leadership", "Innovation", "Research",
            "Business", "Health", "Environment", "Social", "Community",

            # Technical subcategories
            "Web Development", "Mobile Development", "Machine Learning", "Deep Learning",
            "Generative AI", "Data Science", "Cybersecurity", "Cloud Computing",
            "Blockchain", "IoT", "Robotics", "Game Development", "UI/UX Design",
            "DevOps", "Software Engineering", "Database", "API Development",
            "Frontend", "Backend", "Full Stack", "Python", "JavaScript", "Java",

            # Cultural subcategories
            "Singing", "Dancing", "Writing", "Poetry", "Literature", "Theater",
            "Photography", "Painting", "Music", "Classical Music", "Folk Dance",
            "Contemporary Dance", "Creative Writing", "Storytelling", "Drama",
            "Film Making", "Art Exhibition", "Sculpture", "Crafts", "Fashion",

            # Sports subcategories
            "Football", "Basketball", "Cricket", "Tennis", "Badminton", "Swimming",
            "Athletics", "Volleyball", "Table Tennis", "Chess", "Cycling",
            "Running", "Marathon", "Fitness", "Yoga", "Gym", "Martial Arts",
            "Boxing", "Wrestling", "Hockey", "Baseball", "Golf", "Archery"
        ]

        # Configure Gemini (set your API key here or as environment variable)
        genai.configure(api_key= os.getenv('GEMINI_API_KEY'))  # Replace with your actual API key

        model = genai.GenerativeModel('gemini-2.0-flash')

        classification_prompt = f"""
        Classify this prompt into relevant tags: "{prompt}"

        Available tags: {', '.join(tags)}

        Return only a JSON array of all relevant tags (no limit on number of tags).
        Include both general categories (like "Technical", "Sports") and specific subcategories (like "Machine Learning", "Basketball").
        Example: ["Technical", "Machine Learning", "Workshop"]
        """

        try:
            response = model.generate_content(classification_prompt)

            # Extract JSON from response
            json_match = re.search(r'\[.*?\]', response.text)
            if json_match:
                result = json.loads(json_match.group())
                return [tag for tag in result if tag in tags]

            return []

        except:
            # Enhanced fallback matching with broader categories
            prompt_lower = prompt.lower()
            matched = []

            keywords = {
                # General Technical
                "Technical": ["coding", "programming", "tech", "software", "development", "computer"],

                # Technical Specific
                "Web Development": ["web", "website", "html", "css", "javascript", "react", "angular"],
                "Machine Learning": ["machine learning", "ml", "model", "algorithm", "prediction"],
                "Deep Learning": ["deep learning", "neural network", "tensorflow", "pytorch"],
                "Generative AI": ["genai", "generative", "chatgpt", "llm", "ai generation"],
                "Data Science": ["data science", "analytics", "visualization", "pandas", "statistics"],
                "Mobile Development": ["mobile", "android", "ios", "app development", "flutter"],

                # General Cultural
                "Cultural": ["cultural", "art", "music", "dance", "traditional", "heritage"],

                # Cultural Specific
                "Singing": ["singing", "vocal", "song", "melody", "choir"],
                "Dancing": ["dancing", "dance", "choreography", "ballet", "hip hop"],
                "Writing": ["writing", "author", "novel", "story", "blog", "content"],
                "Poetry": ["poetry", "poem", "verse", "rhyme", "spoken word"],
                "Photography": ["photography", "photo", "camera", "portrait", "landscape"],

                # General Sports
                "Sports": ["sports", "game", "fitness", "tournament", "match", "athletic"],

                # Sports Specific
                "Football": ["football", "soccer", "fifa", "goal", "field"],
                "Basketball": ["basketball", "nba", "court", "dribble", "shoot"],
                "Cricket": ["cricket", "bat", "ball", "wicket", "ipl"],
                "Swimming": ["swimming", "pool", "stroke", "freestyle", "butterfly"],
                "Chess": ["chess", "checkmate", "strategy", "board game"],

                # General Categories
                "Workshop": ["workshop", "hands-on", "training", "learn", "practical"],
                "Competition": ["competition", "contest", "hackathon", "challenge", "tournament"],
                "Career": ["career", "job", "professional", "internship", "placement"]
            }

            for tag, words in keywords.items():
                if any(word in prompt_lower for word in words):
                    matched.append(tag)
        return []


    def save_embdeddings(self, user_prompt :str , email : str, mobile_no : str ,  username : str,  sem : str , section : str , branch : str):
        vector_id = str(uuid.uuid4())
        tags = self.generate_tags(user_prompt)
        try :
            self.index.upsert_records(
                "user_space",
                [
                    {
                        "_id": vector_id,
                        "chunk_text": user_prompt,
                        "email": email,
                        "username": username,
                        "generation_date": datetime.now(),
                        "tags": tags ,
                        "sem": sem,
                        "section": section,
                        "mobile_no" : mobile_no ,
                        "branch" : branch
                    }
                ]
            )
            return "User Date is Uploaded"
        except Exception as e:  # Catching a general exception
            print(f"An unexpected error occurred: {e}")


    def compare_embeddings(self , event_prompt:str , sem_to : str , sem_from : str) :
        tags = self.generate_tags(event_prompt)
        filtered_results = self.index.search(
            namespace="user_space",
            query={
                "inputs": {"text": event_prompt},
                "top_k": 100
            },
        )
        results_list = filtered_results['results']['hits']
        final_list = []
        ##results_list is a list[dict]
        for result in results_list :
            if sem_to >= result['fields']['sem'] >= sem_from:
                score = result['score']
                user_tags = result['fields']['tags']
                jaccard_similarity = self.compare_list_js(user_tags , tags)
                final_score = 0.7*score + 0.3*jaccard_similarity
                if final_score >= 0.6:
                    final_list.append(result)
        return final_list

    def compare_list_js(self , list1 , list2 )->float :
        set1 = set(list1)
        set2 = set(list2)

        # Find intersection (common strings)
        intersection = set1.intersection(set2)

        # Find union (all unique strings)
        union = set1.union(set2)

        # Calculate Jaccard similarity
        if len(union) == 0:
            return 0.0

        score = len(intersection) / len(union)
        return round(score, 3)

