from behave import given, when, then, step
from config.settings import CODE_HOME
from os.path import join
from sys import stdout
from requests import get, post, patch, exceptions
from logging import getLogger
from hamcrest import assert_that, is_, has_key
from json import dumps
from pymongo import MongoClient

__logger__ = getLogger(__name__)


@given(u'I set the tutorial 301')
def step_impl(context):
    context.data_home = join(join(join(CODE_HOME, "features"), "data"), "301.Persisting_Flume")


@given(u'The fiware-service header is "{fiware_service}" and the fiware-servicepath header is "{fiware_servicepath}"')
def fiware_service_headers(context, fiware_service, fiware_servicepath):
    context.headers = {"fiware-service": fiware_service, "fiware-servicepath": fiware_servicepath}


@step(u'I send GET HTTP request to "{url}" with fiware-service and fiware-servicepath')
def send_query_with_service(context, url):
    try:
        response = get(url, headers=context.headers, verify=False)
        # override encoding by real educated guess as provided by chardet
        response.encoding = response.apparent_encoding
    except exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

    context.response = response.json()
    context.statusCode = str(response.status_code)


@then(u'I receive a HTTP "{status_code}" response code with all the services information')
def response_services_information(context, status_code):
    assert_that(context.statusCode, is_(status_code),
                "Response to CB notification has not got the expected HTTP response code: Message: {}"
                .format(context.response))

    aux = list(map(lambda x: {x['entity_type']: {"resource": x['resource'], 'apikey': x['apikey']}},
                   context.response['services']))

    context.services_info = dict((key, d[key]) for d in aux for key in d)


@then('I receive a HTTP "{status_code}" response')
def step_impl(context, status_code):
    assert_that(context.statusCode, is_(status_code),
                "Response to CB notification has not got the expected HTTP response code: Message: {}"
                .format(context.response))


@step("I send PATCH HTTP request with the following data")
def step_impl(context):
    for element in context.table.rows:
        valid_response = dict(element.as_dict())

        url = join(join(join(valid_response['Url'], 'entities'), valid_response['Entity_ID']), 'attrs')

        payload = '''{"%s": {"type": "command","value": ""}}''' % valid_response['Command']

        context.headers['Content-Type'] = 'application/json'

        try:
            response = patch(url, data=payload, headers=context.headers)
            # override encoding by real educated guess as provided by chardet
            response.encoding = response.apparent_encoding
        except exceptions.RequestException as e:  # This is the correct syntax
            raise SystemExit(e)

        context.statusCode = str(response.status_code)
        context.response = response.reason


@when('I send a subscription to the Url "{url}" and payload "{file}"')
def step_impl(context, url, file):
    file = join(context.data_home, file)
    with open(file) as f:
        payload = f.read()

    context.headers['Content-Type'] = 'application/json'

    try:
        response = post(url, data=payload, headers=context.headers)
        # override encoding by real educated guess as provided by chardet
        response.encoding = response.apparent_encoding
    except exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

    context.statusCode = str(response.status_code)
    context.response = response.reason


@given('We connect to the MongoDB with the host "{host}" and the port "{port}"')
def step_impl(context, host, port):
    connection_string = 'mongodb://' + host + ':' + port
    context.client = MongoClient(connection_string)


@when("We request the available MongoDB databases")
def step_impl(context):
    context.obtained_dbs = context.client.list_database_names()


@then("We obtain the following databases")
def step_impl(context):
    for element in context.table.rows:
        valid_response = dict(element.as_dict())

        expected_dbs = valid_response['Databases']

        result = list(set(context.obtained_dbs) - set(expected_dbs)) + \
                 list(set(expected_dbs) - set(context.obtained_dbs))

        assert_that(len(result), is_(0),
                    "There are some databases not presented in the tuturial: {}"
                    .format(result))


@when('We request the available MongoDB collections from the database "{database}"')
def step_impl(context, database):
    context.mydb = context.client['sth_openiot']


@then('We obtains "{total}" total collections from MongoDB')
def step_impl(context, total):
    # list the collections should be 4 sensors per store (4 stores) mal 2 for the aggregation: 32
    my_collections = context.mydb.list_collection_names()
    number_collections = len(my_collections)

    assert_that(number_collections, is_(total),
                "There total number of collections found is different: {}"
                .format(number_collections))


@when('We request "{elements}" elements from the collection "{collection}"')
def step_impl(context, elements, collection):
    my_collection = context.mydb[collection]

    context.myresults = list(my_collection.find().limit(elements))


@then('I receive a list with "{elements}" elements')
def step_impl(context, elements):
    # should have data and the data
    number_elements = len(context.myresults)

    assert_that(number_elements, is_(elements),
                "There total number of elements found is different: {}"
                .format(number_elements))


@step("with the following keys")
def step_impl(context):
    for element in context.table.rows:
        valid_response = dict(element.as_dict())

        expected_keys = valid_response['Keys']
        obtained_keys = list(context.myresults[0].keys())

        aux = list(set(obtained_keys) - set(expected_keys)) + list(set(expected_keys) - set(obtained_keys))

        assert_that(aux, is_([]),
                    "The expected keys and obtained keys are not the same, difference: {}"
                    .format(aux))


@when('We request "{elements}" elements from the collection "{collection}" with the filter {filter}')
def step_impl(context, elements, collection, filter):
    my_collection = context.mydb[collection]
    context.myresults = list(my_collection.find(filter).limit(elements))
