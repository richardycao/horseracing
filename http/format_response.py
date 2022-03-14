import json

id = 3

with open('response'+str(id)+'.txt', 'r') as reader:
    content = reader.read()
    formatted_content = json.dumps(json.loads(content), sort_keys=True, indent=2, separators=(',', ': '))

    with open('formatted_response'+str(id)+'.txt', 'w') as writer:
        writer.write(formatted_content)
