from flask import Flask
from graphene import ObjectType, String, Int, ID, List, Field, Schema
from flask_graphql import GraphQLView

class DocumentType(ObjectType):
    id = ID()
    type = String()
    number = String()
    issueDate = String()
    expiryDate = String()

class RelativeType(ObjectType):
    id = ID()
    relationType = String()
    name = String()
    age = Int()

class ClientType(ObjectType):
    id = ID()
    name = String()
    age = Int()
    documents = List(DocumentType)
    relatives = List(RelativeType)

class Query(ObjectType):
    client = Field(ClientType, id=ID(required=True))

    def resolve_client(root, info, id):
        return {
            "id": id,
            "name": "John Doe",
            "age": 30,
            "documents": [
                {"id": "doc1", "type": "passport", "number": "1234", "issueDate": "2020-01-01", "expiryDate": "2030-01-01"}
            ],
            "relatives": [
                {"id": "rel1", "relationType": "spouse", "name": "Jane Doe", "age": 28}
            ]
        }

schema = Schema(query=Query)

app = Flask(__name__)
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

if __name__ == "__main__":
    app.run(debug=True)
