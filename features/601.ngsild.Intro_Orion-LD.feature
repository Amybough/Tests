Feature: test tutorial 601 Introduction to Linked Data (Orion-LD)

#
#   Parameters to be considered (aka INTERESTING_FEATURES_STRINGS)
#
    url: https://fiware-tutorials.readthedocs.io/en/latest/linked-data.html
    git-clone: https://github.com/FIWARE/tutorials.Linked-Data.git
    git-directory: /tmp/tutorials.Linked-Data-Intro

    shell-commands: git checkout NGSI-v2 ; ./services create; ./services start
    clean-shell-commands: ./services stop


    Background:
        Given I set the tutorial 601

    Scenario: [1] Checking the Orion-LD service health
        When  I prepare a GET HTTP request to "http://localhost:1026/version"
        And   I perform the query request
        Then  I receive a HTTP "200" response code

    #
    #   Request 2, 3: Creating an Entity
    #
    Scenario Outline: [2, 3] Creating an Entity
      When I prepare a POST HTTP request for "creating an entity" to "http://localhost:1026/ngsi-ld/v1/entities"
      And  I set header Content-Type to application/ld+json
      And  I set the body request as described in <file>
      And  I perform the request
      Then I receive a HTTP response with the following Orion-LD data
        | Status-Code | Location   |
        | 201         | <location> |

      Examples:
        | file               | location                                           |
        | request601-02.json | /ngsi-ld/v1/entities/urn:ngsi-ld:Building:store001 |
        | request601-03.json | /ngsi-ld/v1/entities/urn:ngsi-ld:Building:store002 |


    Scenario: [4] OBTAIN ENTITY DATA BY FQN TYPE
      When I prepare a GET HTTP request for "obtaining an entity data" to "http://localhost:1026/ngsi-ld/v1/entities"
      And  I set header Accept to application/ld+json
      And  the params equal to "type=https://smartdatamodels.org/dataModel.Building/Building"
      And  I perform the request
      Then I receive a HTTP "200" response code from Orion-LD with the body equal to "response601-04.json"


    Scenario: [5] OBTAIN ENTITY DATA BY ID
      When  I prepare a GET HTTP request for "obtaining entity data by Id" to "http://localhost:1026/ngsi-ld/v1/entities/urn:ngsi-ld:Building:store001"
      And   I set header Accept to application/ld+json
      And   I perform the request
      Then  I receive a HTTP "200" response code from Orion-LD with the body equal to "response601-05.json"


    Scenario: [6] OBTAIN ENTITY DATA BY TYPE
      When  I set the "Accept" header with the value "application/ld+json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   the params equal to "type=Building"
      And   the params equal to "options=keyValues"
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-06.json"


    Scenario: [7] FILTER CONTEXT DATA BY COMPARING THE VALUES OF AN ATTRIBUTE
      When  I set the "Accept" header with the value "application/ld+json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities?type=Building&q=name==%22Checkpoint%20Markt%22&options=keyValues"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-07.json"


    Scenario: [8] FILTER CONTEXT DATA BY COMPARING THE VALUES OF AN ATTRIBUTE IN AN ARRAY
      When  I set the "Accept" header with the value "application/ld+json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   the params equal to "type=Building"
      And   the params equal to "q=category==%22commercial%22,%22office%22"
      And   the params equal to "options=keyValues"
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-08.json"


    Scenario: [9] FILTER CONTEXT DATA BY COMPARING THE VALUES OF A SUB-ATTRIBUTE
      When  I set the "Accept" header with the value "application/ld+json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities?type=Building&q=address%5BaddressLocality%5D==%22Kreuzberg%22&options=keyValues"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-09.json"


    Scenario: [10] FILTER CONTEXT DATA BY QUERYING METADATA
      When  I set the "Accept" header with the value "application/json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   the params equal to "type=Building"
      And   the params equal to "q=address.verified==true"
      And   the params equal to "options=keyValues"
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-10.json"


    Scenario: [11] FILTER CONTEXT DATA BY COMPARING THE VALUES OF A GEO:JSON ATTRIBUTE
      When  I set the "Accept" header with the value "application/json"
      And   I set the "Link" header with the value "<https://smart-data-models.github.io/dataModel.Building/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json""
      And   I set the url to "http://localhost:1026/ngsi-ld/v1/entities?type=Building&geometry=Point&coordinates=%5B13.3777,52.5162%5D&georel=near%3BmaxDistance==2000&options=keyValues"
      And   I send a GET HTTP request to that url
      Then  I receive from Orion-LD "200" response code with the body equal to "response601-11.json"
