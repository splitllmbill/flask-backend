from models.common import DatabaseManager, Prompts, toJson

dbManager = DatabaseManager()

def getPrompt(promptType):
    query = {
        "type": promptType
    }
    prompt = dbManager.findAll(Prompts,query,'version')[0]
    return prompt