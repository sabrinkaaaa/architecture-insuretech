# GraphQL API


## Проектирование GraphQL API

При развитии сервиса управления клиентскими данными (client-info) команда столкнулась с проблемой. Потребители данных (веб-приложения и сервис core-app) в разных сценариях продажи и обслуживания страховок могут требовать абсолютно разные данные. При этом карточка клиента у сервиса достаточно объёмная: общий атрибутивный состав достигает 500 штук. Из-за высокой вариативности набора запрашиваемых данных команда приняла решение в своём REST API предоставить множество отдельных ресурсов, с помощью которых можно запрашивать отдельные объекты данных клиента: контакты, документы, родственники и так далее.

Однако такая реализация кратно увеличивает нагрузку и RPS сервиса client-info, поскольку в рамках одного сценария могут потребоваться сразу несколько объектов данных — их придётся запрашивать по отдельности. Предоставить один ресурс для получения абсолютно всех данных клиента не представляется возможным: объём передаваемых данных будет настолько большим, что замедлит скорость взаимодействия с сервисами (особенно с веб-приложением).

Вы обсудили проблему с командой и приняли решение перевести REST API сервиса client-info на GraphQL.

## Что нужно сделать

Спроектируйте GraphQL на основании существующего контракта сервиса:

1. Проанализируйте Swagger контракт client-info. Оцените существующую структуру API, выделите ключевые ресурсы и операции.

```yaml
# swagger.yaml
swagger: '2.0'
info:
  description: API сервиса управления клиентскими данными
  version: 1.0.0
  title: Клиентский Сервис
host: api.client-service.com
basePath: /v1
schemes:
  - https
paths:
  /clients/{id}:
    get:
      tags:
        - Клиент
      summary: Получить информацию о клиенте по ID
      produces:
        - application/json
      parameters:
        - name: id
          in: path
          required: true
          type: string
      responses:
        '200':
          description: Успешный ответ
          schema:
            $ref: '#/definitions/Client'
  /clients/{id}/documents:
    get:
      tags:
        - Документы
      summary: Список документов клиента
      produces:
        - application/json
      parameters:
        - name: id
          in: path
          required: true
          type: string
      responses:
        '200':
          description: Успешный ответ
          schema:
            type: array
            items:
              $ref: '#/definitions/Document'
  /clients/{id}/relatives:
    get:
      tags:
        - Родственники
      summary: Информация о родственниках клиента
      produces:
        - application/json
      parameters:
        - name: id
          in: path
          required: true
          type: string
      responses:
        '200':
          description: Успешный ответ
          schema:
            type: array
            items:
              $ref: '#/definitions/Relative'
definitions:
  Client:
    type: object
    properties:
      id:
        type: string
      name:
        type: string
      age:
        type: integer
  Document:
    type: object
    properties:
      id:
        type: string
      type:
        type: string
      number:
        type: string
      issueDate:
        type: string
      expiryDate:
        type: string
  Relative:
    type: object
    properties:
      id:
        type: string
      relationType:
        type: string
      name:
        type: string
      age:
        type: integer
```

2. На основе анализа REST API разработайте эквивалентную схему GraphQL (schema.graphql), которая позволит избежать дублирования за счёт гибкости в выборе запрашиваемых данных.

3. Определите сущности, их поля, а также необходимые запросы (queries), которые покроют все операции REST API.

Когда будете сдавать решение, загрузите `swagger.yaml` и `schema.graphql` в директорию Task5 в рамках пул-реквеста.

## Решение

В существующем REST API есть три основных ресурса:

* `Client` (/clients/{id}) — основная сущность, содержит базовую информацию о клиенте.
* `Document` (/clients/{id}/documents) — список документов клиента.
* `Relative` (/clients/{id}/relatives) — список родственников клиента.

В GraphQL мы можем выразить эти сущности следующим образом:

```graphql
# schema.graphql
type Query {
  client(id: ID!): Client
}

type Client {
  id: ID!
  name: String!
  age: Int!
  documents: [Document]
  relatives: [Relative]
}

type Document {
  id: ID!
  type: String!
  number: String!
  issueDate: String!
  expiryDate: String!
}

type Relative {
  id: ID!
  relationType: String!
  name: String!
  age: Int!
}
```

## Примеры использования

### REST API

Для получения информации о клиенте и связанных сущностях требовалось делать несколько запросов:

1. `/clients/{id}` — базовая информация (id, name, age)
2. `/clients/{id}/documents` — документы (id, type, number, issueDate, expiryDate)
3. `/clients/{id}/relatives` — родственники (id, relationType, name, age)

### GraphQL

С GraphQL можно получить всё в одном запросе:

```graphql
query {
  client(id: "123") {
    id
    name
    age
    documents {
      id
      type
      number
      issueDate
      expiryDate
    }
    relatives {
      id
      name
      relationType
      age
    }
  }
}
```

Преимущество в гибкости: можно убрать ненужные поля или сущности и получать **только нужные данные**, экономя трафик и нагрузку на сервер.



