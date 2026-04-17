import google.generativeai as genai

genai.configure(api_key="AIzaSyAFEV5ElDqsqG7EopAaASeJtLQZw_Humlw")

for model in genai.list_models():
    print(model.name)