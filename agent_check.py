

import os
# from utils import get_openai_api_key
from crewai import Agent, Task, Crew
from langchain_community.llms import HuggingFaceHub
from langchain_community.chat_models import ChatLiteLLM
from dotenv import load_dotenv
from IPython.display import Markdown
from crewai import Task

import os

load_dotenv()

hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

openai_api_key = os.getenv("OPENAI_API_KEY")
# openai_api_base = os.getenv("OPENAI_API_BASE")
# openai_model_name = os.getenv("OPENAI_MODEL_NAME")

llm = ChatLiteLLM(
    model=os.getenv("LITELLM_MODEL_NAME"),
    provider=os.getenv("LITELLM_PROVIDER"),
    api_base=os.getenv("LITELLM_API_BASE"),
    api_key=os.getenv("LITELLM_API_KEY")
)

# openai_api_key = get_openai_api_key()
# os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

# hf_llm = HuggingFaceHub(repo_id="mistralai/Mistral-7B-Instruct-v0.1", model_kwargs={"temperature": 0.7})
# '''Defining agents'''

extractor = Agent(
    role="Expert Data Extractor",
    goal="Extract the data from the given craigslist listing {content}",
    backstory="You are a data extractor intern who is tasked with extracting data from a given craigslist listing."
        "You are given a craigslist listing url and you need to report data in a structured format."
        "Start date: 'YYYY-MM-DD'"
        "Price: 'USD'"
        "Per week or Month : 'Per week' or 'Per month'"
        "Neighbourhood: 'Neighbourhood of the listing'"
        "Description: 'Description of the listing'"
        "Amenities: 'Amenities of the listing'"
        "Utilities: 'Utilities of the listing'"
        "Furnished: 'Furnished or Unfurnished'"
        "Separate Bathroom: 'Yes or No'"
        "Separate Kitchen: 'Yes or No'",
    allow_delegation=False,
    verbose=True,
    llm=llm
)

qa_agent = Agent(
    role="Quality Assurance Manager",
    goal="Check the accuracy and data format of the data extracted by the Expert Data Extractor {content}",
    backstory="You are a quality assurance manager who is tasked with checking the accuracy and data format of the data extracted by the Expert Data Extractor."
        "you are given the data by the Expert Data Extractor and you need to check if the data is accurate and in the correct format. the data was wxtracted from the {content}"
        "Start date: 'YYYY-MM-DD'"
        "Price: 'USD'"
        "Per week or Month : 'Per week' or 'Per month'"
        "Neighbourhood: 'Neighbourhood of the listing'"
        "Description: 'Description of the listing'"
        "Amenities: 'Amenities of the listing'"
        "Utilities: 'Utilities of the listing'"
        "Furnished: 'Furnished or Unfurnished'"
        "Separate Bathroom: 'Yes or No'"
        "Separate Kitchen: 'Yes or No'",
    allow_delegation=True,
    verbose=True,
    llm=llm
)



# Task 1: Extract structured data from Craigslist listing
extractor_task = Task(
    description=(
        "Given a Craigslist listing URL, extract structured data including:\n"
        "- Start date (format: YYYY-MM-DD)\n"
        "- Price (in USD)\n"
        "- Per week or per month\n"
        "- Neighbourhood\n"
        "- Description\n"
        "- Amenities\n"
        "- Utilities\n"
        "- Furnished or Unfurnished\n"
        "- Separate Bathroom (Yes or No)\n"
        "- Separate Kitchen (Yes or No)"
    ),
    expected_output=(
        "A structured JSON object with keys: start_date, price, billing_cycle, neighbourhood, "
        "description, amenities, utilities, furnished, separate_bathroom, separate_kitchen"
    ),
    agent=extractor,
)

# Task 2: QA on extracted data
qa_task = Task(
    description=(
        "Review the structured data extracted by the Data Extractor. Check for:\n"
        "- Completeness of all required fields\n"
        "- Correct formatting (e.g., dates, currencies)\n"
        "- Plausibility and logical consistency\n"
        "- Flags or errors in any fields that look suspicious or are missing\n\n"
        "Make necessary corrections and return the cleaned and verified JSON output."
    ),
    expected_output=(
        "A cleaned and verified JSON object or a list of issues found with corrected values."
    ),
    agent=qa_agent,
)

crew = Crew(
    agents=[extractor, qa_agent],
    tasks=[extractor_task, qa_task],
    verbose=True
)

result = crew.kickoff(inputs={"content": "<PASTE CRAIGSLIST LISTING TEXT HERE OR URL>"})

Markdown(result.raw)


crew = Crew(
    agents=[extractor, qa_agent],
    tasks=[extractor_task, qa_task],
    verbose=True
)

result = crew.kickoff(inputs={"content": "Artificial Intelligence"})

Markdown(result.raw)






