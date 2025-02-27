################################################################
#                        RAG APP                               #
################################################################

#-> streamlit run rag_app.py

## for db
import chromadb #0.5.0
## for ai
import ollama  #0.5.0
## for app
import streamlit as st #1.35.0

import sys

#######
# ToDo
# [ ] Allow the user pick the file - keyword_generator to query
# [ ] Allow the user pick the model to chat
# [ ] Ask the user which _language (ES, EN)_ would like to get the answers. OPTIONAL: Because it seems that dependes of the language udes in the question
# [ ] Review and compare the answers to the same questions from different models
#######

######################## Backend ##############################
class AI():
    def __init__(self, collection_name):
        db = chromadb.PersistentClient()
        self.collection = db.get_or_create_collection(collection_name)

    def query(self, q, top=10):
        res_db = self.collection.query(query_texts=[q])["documents"][0][0:top]
        context = ' '.join(res_db).replace("\n", " ")
        return context
      
    def getCollection(self):
        return self.collection.name

    def respond(self, lst_messages, model="phi3", use_knowledge=False):
        q = lst_messages[-1]["content"]
        context = self.query(q)

        if use_knowledge:
            prompt = "Give the most accurate answer using your knowledge and the following additional information: \n"+context
        else:
            prompt = "Give the most accurate answer using only the following information: \n"+context

        res_ai = ollama.chat(model=model, 
                             messages=[{"role":"system", "content":prompt}]+lst_messages,
                             stream=True)
        for res in res_ai:
            chunk = res["message"]["content"]
            app["full_response"] += chunk
            yield chunk

######################## Frontend #############################
## Layout

# Get the list of collections from ChromaDB
db = chromadb.PersistentClient()
collections = db.list_collections()
collection_names = [collection.name for collection in collections]

# Allow the user to pick the collection
selected_collection = st.sidebar.selectbox("Select Collection", collection_names)

# Allow the user to pick the model
models = ["deepseek-r1:1.5b", "phi3"]
selected_model = st.sidebar.selectbox("Select Model", models)

# Initialize AI with the selected collection
ai = AI(selected_collection)

st.title('💬 Write your questions about the document ' + ai.getCollection())

st.sidebar.title("Chat History")
app = st.session_state

if "messages" not in app:
    app["messages"] = [{"role":"assistant", "content":"I'm ready to retrieve information"}]

if 'history' not in app:
    app['history'] = []

if 'full_response' not in app:
    app['full_response'] = '' 

## Keep messages in the Chat
for msg in app["messages"]:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="😎").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar="👾").write(msg["content"])

## Chat
if txt := st.chat_input():
    ### User writes
    app["messages"].append({"role":"user", "content":txt})
    st.chat_message("user", avatar="😎").write(txt)

    ### AI responds with chat stream
    app["full_response"] = ""
    st.chat_message("assistant", avatar="👾").write_stream( ai.respond(app["messages"], model=selected_model) )
    app["messages"].append({"role":"assistant", "content":app["full_response"]})
    
    ### Show sidebar history
    app['history'].append("😎: "+txt)
    app['history'].append("👾: "+app["full_response"])
    st.sidebar.markdown("<br />".join(app['history'])+"<br /><br />", unsafe_allow_html=True)

## Add a button to stop the application
if st.sidebar.button("Finalizar aplicación"):
    st.write("La aplicación se ha detenido.")
    st.stop() # detener la ejecución del código actual pero dejar la app en funcionamiento.
    # sys.exit() # cerrar completamente la app. Didn't work in streamlit

# app example
# {'history': ['😎: how much is the revenue?', 
#              '👾: The total revenue reported in the given information is 60million'], 
#
#  'messages': [{'role':'assistant', 'content':'I'm ready to retrieve information'}, 
#               {'role':'user', 'content':'how much is the revenue?'}, 
#               {'role':'assistant', 'content':'The total revenue reported in the given information is 60million'}], 
#
#  'full_response': 'The total revenue reported in the given information is 60million'}
