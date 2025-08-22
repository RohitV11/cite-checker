import requests
from newspaper import Article
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
from groq import Groq
import requests
from sentence_transformers import SentenceTransformer, util
import nltk
import spacy
# Download the punkt tokenizer if you haven't already
nltk.download('punkt')
nltk.download('punkt-tab')

#CLAIM OPTIMIZATION
nlp = spacy.load("en_core_web_sm")

note = input("User note: ")
doc = nlp(note)

entities = [(ent.text, ent.label_) for ent in doc.ents]

keywords = [token.lemma_ for token in doc if not token.is_stop]
print(entities)

params = {
  'access_key': '706d07187ca86d63d4f708a158893d1c',
  'query': 'iran',
}

api_result = requests.get('https://api.serpstack.com/search', params)

api_response = api_result.json()

print ("Total results: ", api_response['search_information'])

for number, result in enumerate(api_response['organic_results'], start=1):
    print(f"{number}. {result['url']}")

r = requests.get('https://www.mcdonalds.com/us/en-us.html', auth=('user', 'pass'))

target_month = 6 #user input
target_year = 2025 #user input
if target_month in {4,6,9,11}:
  target_end_date = f"{target_year}-{target_month:02d}-30"
elif target_month == 2:
  target_end_date = f"{target_year}-{target_month:02d}-28"
else:
  target_end_date = f"{target_year}-{target_month:02d}-31"

target_start_date = f"{target_year}-{target_month:02d}-01"

params = {
  'access_key': SERP_API_KEY,
  'query': 'iran'
  }

api_result = requests.get('https://api.serpstack.com/search', params)

api_response = api_result.json()
if api_response['request']['success']:
  print ("Total results: ", api_response['search_information']['total_results'])

  for number, result in enumerate(api_response['organic_results'], start=1):
      print ("%s. %s" % (number, result['url']))

test_article = Article("https://www.mercurynews.com/2025/06/21/trump-says-us-has-bombed-three-nuclear-sites-in-iran/")
test_article.download()
test_article.parse()
date = test_article.publish_date
if date.month == 6:
  test_article_text = test_article.text
  print(test_article_text)

"""## **NOTE to CLAIM**"""

# LLM-BASED NOTE-TO-CLAIM MAKER

from groq import Groq
import json

def generate_claims(note):
    client = Groq(
        api_key=GROQ_API_KEY,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Given jumbled notes, come up with three potential claims that could be made from the content. The claims should be slightly varied in their emphasis while remaining tightly focused on the core information.. Output the claims like so: [\"claim 1\", \"claim 2\", \"claim 3\"] with each claim enclosed in double quotes.",
            },
            {
                "role": "user",
                "content": note,
            }
        ],
        model="llama-3.3-70b-versatile",
        stream=False,
    )

    claims_string = chat_completion.choices[0].message.content
    return json.loads(claims_string) #turns string into list

#CLAIM CHOOSING LOGIC

def pick_claims(note):
  print("From the following notes: '" + note + "', here are the likely claims that can be made:");
  claims = generate_claims(note)
  for i, claim in enumerate(claims, 1):
    print(f"{i}. {claim}")
  print("0. Enter my own claim")

  while True:
    try:
      choice = int(input("Please select the number of the claim you'd like to pursue: "))
      if 1 <= choice <= len(claims):
        print("You've selected:", claims[choice - 1])
        return claims[choice - 1]
      elif choice == 0:
        return input("Please enter your custom claim: ")
      else:
        print("Invalid choice. Please enter a number from the list.")
    except ValueError:
      print("Invalid input. Please enter a number.")

"""## **SEARCH OPTIMIZATION**"""

from nltk.corpus import wordnet

def extract_keywords(note):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(note)

    # Extract named entities
    named_entities = [ent for ent in doc.ents]

    # List of non-critical verbs
    non_critical_verbs = ["am", "is", "are", "was", "were", "be", "being", "been", "do", "does", "did", "have", "has", "had", "can", "could", "may", "might", "must", "shall", "should", "will", "would"]

    # Extract critical verbs
    critical_verbs = {token.lemma_: token.idx for token in doc if token.pos_ == "VERB" and token.lemma_ not in non_critical_verbs}

    # Extract and print all noun chunks that don't contain a named entity for or statement in search bar
    or_blocks = {}
    for chunk in doc.noun_chunks:
        if not any(ent.text in chunk.text for ent in doc.ents):
            or_blocks[chunk.text] = chunk.start_char
            if (chunk.text != chunk.root.text):
              or_blocks[chunk.root.text] = chunk.root.idx

    # Create a new list called clean_named_entities that remove any entities with this type
    excluded_labels = ["DATE", "TIME", "MONEY", "PERCENT", "QUANTITY", "CARDINAL", "ORDINAL"]
    clean_named_entities = {ent.text: ent.start_char for ent in doc.ents if ent.label_ not in excluded_labels}

    return or_blocks, clean_named_entities, critical_verbs

or_blocks, clean_named_entities, critical_verbs = extract_keywords("The US is reducing major investment in globe hotdog $1 billion")
print("Or Blocks:", or_blocks)
print("Clean Named Entities:", clean_named_entities)
print("Critical Verbs:", critical_verbs)

from nltk.corpus import wordnet

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace('_', ' '))
    return list(synonyms)

def create_search_query(note, site=None):
    or_blocks, clean_named_entities, critical_verbs = extract_keywords(note)

    # Combine all terms with their original indices
    all_terms = []
    for term, index in or_blocks.items():
        synonyms = get_synonyms(term)
        # Add the original term to the list of synonyms
        synonyms.insert(0, term)
        # Only add the OR string if there are synonyms (including the original term)
        if synonyms:
            # Remove quotes around the words in the OR block
            or_string = '(' + ' OR '.join([s for s in synonyms]) + ')'
            all_terms.append((or_string, index))

    for entity, index in clean_named_entities.items():
        all_terms.append((f'"{entity}"', index))

    for verb, index in critical_verbs.items():
        all_terms.append((verb, index))

    # Sort terms by their original index
    sorted_terms = sorted(all_terms, key=lambda item: item[1])

    # Construct the search query string, filtering out empty strings
    query_string = " ".join([term[0] for term in sorted_terms if term[0]])

    # Add site: tag if site is provided
    if site:
        query_string = f"site:{site} {query_string}"


    return query_string

# Example usage:
note = "The US is reducing major investment in Iran $1 billion"
search_query = create_search_query(note, site="nytimes.com")
print(search_query)

from serpapi.google_search import GoogleSearch
params = {
  "engine": "google",
  "q": search_query,
  "api_key": SERPAPI_KEY
}

search = GoogleSearch(params)
results = search.get_dict()
organic_results = results["search_information"]
print(organic_results)

test_article = Article("https://www.mercurynews.com/2025/06/21/trump-says-us-has-bombed-three-nuclear-sites-in-iran/")
test_article.download()
test_article.parse()
date = test_article.publish_date
if date.month == 6:
  test_article_text = test_article.text
  print(test_article_text)