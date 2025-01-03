from langchain import hub
from langchain_openai import ChatOpenAI

gpt_o1 = ChatOpenAI(model="o1-preview", temperature=1)
gpt_4o = ChatOpenAI(model="gpt-4o")


async def collate_reports(research_topic, digests):
    prompt = hub.pull("vagabond/mycelium_collation")
    chain = prompt | gpt_o1
    output = await chain.ainvoke({"research_topic": research_topic, "reports": digests})
    return output.content


async def generate_search_query(research_topic, existing_queries):
    prompt = hub.pull("vagabond/mycelium_search_query_generator")
    chain = prompt | gpt_o1
    output = await chain.ainvoke({"research_topic": research_topic, "search_queries": existing_queries})
    return output.content


async def extract_relevant_urls(search_query, web_content):
    prompt = hub.pull("vagabond/mycelium_url_extraction")
    chain = prompt | gpt_4o
    output = await chain.ainvoke({"search_query": search_query, "web_content": web_content})
    return output.get("urls")


async def determine_relevance(research_topic, web_content):
    prompt = hub.pull("vagabond/mycelium_relevance")
    chain = prompt | gpt_4o
    output = await chain.ainvoke({"research_topic": research_topic, "web_content": web_content})
    return output.get("relevance")


async def generate_digest(research_topic, web_content):
    prompt = hub.pull("vagabond/mycelium_digest")
    chain = prompt | gpt_4o
    output = await chain.ainvoke({"research_topic": research_topic, "web_content": web_content})
    return output.content


async def generate_spore(research_topic, search_queries, digest):
    prompt = hub.pull("vagabond/mycelium_spore")
    chain = prompt | gpt_o1
    output = await chain.ainvoke({"research_topic": research_topic, "search_queries": search_queries, "digest": digest})
    return output.content
