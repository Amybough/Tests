from behave import given, when, then, step
from config import settings
from os.path import join
from os import environ
from subprocess import Popen, PIPE
from hamcrest import assert_that, is_, equal_to
from features.funtions import read_data_from_file, dict_diff_with_exclusions
from json import loads, dumps
from json.decoder import JSONDecodeError
from requests import get, post, patch, delete, put, RequestException
from xml.dom import minidom
from features.funtions import set_xml_data, change_context

global adminId
global userId
global domainId
global policyId
global revisions
global policySetId


@when('I set the "AuthZForce" to the domain url')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.operation = 'set domain'
    context.url = f'http://localhost:8080/authzforce-ce/domains'


@when('I set the "AuthZForce" {entity} url with the previous "domainId"')
def step_impl(context, entity):
    """
    :param entity: XACML operation
    :type context: behave.runner.Context
    """
    global domainId

    context.operation = entity
    if entity == 'domains':
        context.url = f'http://localhost:8080/authzforce-ce/domains/{domainId}'
    elif entity == 'pap policies':
        context.url = f'http://localhost:8080/authzforce-ce/domains/{domainId}/pap/policies'
    elif entity == 'to the pdp endpoint':
        context.url = f'http://localhost:8080/authzforce-ce/domains/{domainId}/pdp'
    elif entity == 'pap policies with pdp.properties':
        context.url = f'http://localhost:8080/authzforce-ce/domains/{domainId}/pap/pdp.properties'


@when('I set the "AuthZForce" {entity} url with the "domainId" and "policyId"')
def step_impl(context, entity):
    """
    :type context: behave.runner.Context
    """
    global domainId
    global policyId

    if entity == 'a pap policy set':
        context.url = \
            f'http://localhost:8080/authzforce-ce/domains/{domainId}/pap/policies/{policyId}'
        context.operation = entity


@when('I set the "AuthZForce" {entity} url with the "domainId" and "policyId" and version 2')
def step_impl(context, entity):
    """
    :type context: behave.runner.Context
    """
    global domainId
    global policyId

    if entity == 'to a single version of a pap policy set':
        context.url = \
            f'http://localhost:8080/authzforce-ce/domains/{domainId}/pap/policies/{policyId}/2'
        context.operation = entity


@given(u'I set the tutorial 401')
def step_impl_tutorial_203(context):
    context.data_home = join(join(join(settings.CODE_HOME, "features"), "data"),
                             "401.Administrating_Users_and_Organizations")


@when("I request the information from user table")
@when("I update the information into the user table")
@step("I request the information from user table")
def step_impl(context):
    my_env = environ.copy()
    temp = Popen(context.command, shell=True, stdout=PIPE, stderr=PIPE, env=my_env)

    if temp.returncode == 0 or temp.returncode is None:  # is 0 or None if success
        (output, stderr) = temp.communicate()

        if len(output) != 0:  # Update command return no data
            output = output.decode('utf-8').replace('\t', ' ').split('\n')

            del output[2]
            output[0] = output[0].split(" ")
            output[1] = output[1].split(" ")

            aux = dict()
            for i in range(0, len(output[0])):
                aux[output[0][i]] = output[1][i]

            context.output = aux
        else:
            context.output = ''
    else:
        raise AssertionError('An docker error was produced during the execution of the command')


@given("I connect to the MySQL docker instance with the following data")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    # docker exec -it <docker instance> mysql -u<user> -p<password> <database>
    #             -e 'select id, username, email, password from user;'

    for element in context.table.rows:
        valid_response = dict(element.as_dict())
        # | DockerInstance | User | Password | Database | Columns | Table |
        docker_instance = valid_response['DockerInstance']
        user = valid_response['User']
        password = valid_response['Password']
        database = valid_response['Database']
        columns = valid_response['Columns']
        table = valid_response['Table']

        select_stmt = f"'select {columns} from {table};'"

        context.command = f"docker exec {docker_instance} mysql -u{user} -p{password} {database} -e {select_stmt}"


@then("I obtain the following data from MySQL")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    for element in context.table.rows:
        valid_response = dict(element.as_dict())
        user_id = valid_response['id']
        username = valid_response['username']
        email = valid_response['email']

        obtained_user_id = context.output['id']
        obtained_username = context.output['username']
        obtained_email = context.output['email']

        assert (user_id == obtained_user_id), \
            f"\nThe id value is not the expected, obtained {user_id}, but expected: {obtained_user_id}"

        assert (username == obtained_username), \
            f"\nThe id value is not the expected, obtained {username}, but expected: {obtained_username}"

        assert (email == obtained_email), \
            f"\nThe id value is not the expected, obtained {email}, but expected: {obtained_email}"

        assert ('password' in context.output.keys()), \
            f'There should be a password data in the obtained values'


@then("I receive a HTTP response with the following data in header and payload")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    for element in context.table.rows:
        valid_response = dict(element.as_dict())

        assert (context.statusCode == valid_response['Status-Code']), \
            f"Status Code wrong, expected \"{valid_response['Status-Code']}\" but was received \"{context.statusCode}\""

        v_connection = valid_response['Connection']
        r_connection = context.responseHeaders['Connection']
        assert (r_connection == v_connection), \
            f"Invalid Connection value, expected \"{v_connection}\" but was received \"{r_connection}\""

        assert ('X-Subject-Token' in context.responseHeaders), \
            f"Unable to get X-Subject-Token in the header of the response"

        if valid_response['X-Subject-Token'] == "any":
            settings.token = context.responseHeaders['X-Subject-Token']
        else:
            settings.token = valid_response['X-Subject-Token']

        # Check the HTTP response
        body = loads(read_data_from_file(context, valid_response['data']))

        diff = dict_diff_with_exclusions(context, body, context.response, valid_response['excluded'])

        assert_that(diff.to_dict(), is_(dict()),
                    f'Response from Keyrock has not got the expected HTTP response body:\n  {diff.pretty()}')


@when('I send a GET HTTP request to "{url}" with equal X-Auth-Token and X-Subject-Token')
def step_impl(context, url):
    """
    :param url: the url of the HTTP operation
    :type context: behave.runner.Context
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-token': settings.token,
            'X-Subject-token': settings.token
        }

        response = get(url, headers=headers, verify=False)

        # override encoding by real educated guess as provided by chardet
        response.encoding = response.apparent_encoding
    except RequestException as e:
        raise SystemExit(e)

    context.response = response.json()
    context.statusCode = str(response.status_code)


@then(u'I receive a HTTP "{code}" status code from {server} with the body "{file}" and exclusions "{excl_file}"')
def receive_post_iot_dummy_response_with_data(context, code, server, file, excl_file):
    global adminId

    if 'user' in context.response:
        if context.response['user']['username'] == 'alice':
            adminId = context.response['user']['id']
    elif 'organization' in context.response:
        settings.organizationId = context.response['organization']['id']
    elif 'access_token' in context.response:
        assert (context.response['access_token'] == settings.token), \
            f"Wrong access_token received, expected {settings.token}, but received {context.response['access_token']}"
    elif 'application' in context.response:
        settings.applicationId = context.response['application']['id']
    elif 'permission' in context.response:
        settings.permissionId = context.response['permission']['id']
    elif 'role' in context.response:
        settings.roleId = context.response['role']['id']

    body = loads(read_data_from_file(context, file))

    # We need to change the core context based on the new versions and the brokers
    change_context(data=body, context=context.core_context)

    diff = dict_diff_with_exclusions(context, body, context.response, excl_file)

    assert (context.statusCode == code), \
        f'\nWrong Status Code, received \"{context.statusCode}\", but it was expected \"{code}\"'

    assert len(diff) == 0, f'\nResponse from {server} has not got the expected HTTP response body:\n{diff.pretty()}'


@step("With the body request containing the previous token")
@when("We defined a payload with token equal to the previous token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.payload = {
        "token": settings.token
    }

    context.payload = dumps(context.payload)


@step("With the X-Auth-Token header with the previous obtained token")
@when("I set the X-Auth-Token header with the previous obtained token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    try:
        context.header['X-Auth-Token'] = settings.token
    except AttributeError:
        # Context object has no attribute 'header'
        context.header = {'X-Auth-Token': settings.token}


@given("I connect to the MySQL docker instance to grant user with the following data")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    # docker exec -it <docker instance> mysql -u<user> -p<password> <database>
    #             -e "update user set admin = 1 where username='alice';"

    for element in context.table.rows:
        valid_response = dict(element.as_dict())
        # | DockerInstance | User | Password | Database | Table | Username |
        docker_instance = valid_response['DockerInstance']
        user = valid_response['User']
        password = valid_response['Password']
        database = valid_response['Database']
        table = valid_response['Table']
        username = valid_response['Username']

        update_stmt = f"\"update {table} set admin = 1 where username='{username}';\""

        context.command = f"docker exec {docker_instance} mysql -u{user} -p{password} {database} -e {update_stmt}"


@then('I can check the table with the following data')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    # docker exec -it <docker instance> mysql -u<user> -p<password> <database>
    #             -e 'select id, username, email, password from user;'

    for element in context.table.rows:
        valid_response = dict(element.as_dict())
        # | DockerInstance | User | Password | Database | Table | Column | Username |
        docker_instance = valid_response['DockerInstance']
        user = valid_response['User']
        password = valid_response['Password']
        database = valid_response['Database']
        table = valid_response['Table']
        column = valid_response['Column']
        username = valid_response['Username']

        select_stmt = f"\"select {column} from {table} where username = \'{username}\';\""

        context.command = f"docker exec {docker_instance} mysql -u{user} -p{password} {database} -e {select_stmt}"


@then('I obtain the value "{value}" from the select')
def step_impl(context, value):
    """
    :param value: The returned value of the select operation
    :type context: behave.runner.Context
    """
    obtained_value = context.output['admin']

    assert (value == obtained_value), \
        f"\nThe id value is not the expected, obtained {obtained_value}, but expected: {value}"


@step('With the body request with "{username}", "{email}", and "{password}" data')
def step_impl(context, username, email, password):
    """
    :type context: behave.runner.Context
    :type username: str
    :type email: str
    :type password: str
    """
    context.payload = {
        "user": {
            "username": username,
            "email": email,
            "password": password
        }
    }

    context.payload = dumps(context.payload)


@then('I receive a HTTP "{code}" response with the corresponding "{username}" and "{email}" data')
def step_impl(context, code, username, email):
    """
    :param username: the name of the user
    :param code: the status code of the response
    :param email: the email of the user
    :type context: behave.runner.Context
    """
    assert (context.statusCode == code), \
        f'The status code is not the expected value, received {context.statusCode}, expected {code}'

    assert (context.response['user']['username'] == username), \
        f"The username is not the expected, received {context.response['user']['username']}, expected {username}"

    assert (context.response['user']['email'] == email), \
        f"The email value is not the expected value, received {context.response['user']['email']}, expected {email}"

    assert (context.response['user']['enabled'] is True), \
        f"The enabled value is not the expected value, received {context.response['user']['enabled']}, expected True"

    assert (context.response['user']['admin'] is False), \
        f"The admin value is not the expected value, received {context.response['user']['admin']}, expected False"


@when('I send a GET HTTP request to the url "{url}"')
def step_impl(context, url):
    """
    :param url: The url of the HTTP GET operation
    :type context: behave.runner.Context
    """
    try:
        response = get(url, headers=context.header)
    except RequestException as e:
        raise SystemExit(e)

    context.responseHeaders = response.headers
    context.statusCode = str(response.status_code)

    try:
        context.response = response.json()
    except JSONDecodeError:
        context.response = ""


@step('I send a GET HTTP request to "{url}" with the admin user id from previous execution')
def step_impl(context, url):
    """
    :param url: The HTTP GET operation url
    :type context: behave.runner.Context
    """
    global adminId
    url = url + f'/{adminId}'

    try:
        response = get(url, headers=context.header)
    except RequestException as e:
        raise SystemExit(e)

    context.responseHeaders = response.headers
    context.statusCode = str(response.status_code)

    try:
        context.response = response.json()
    except JSONDecodeError:
        context.response = ""


@then('I receive a HTTP "{code}" status code from Keyrock with the following data for each created user')
def step_impl(context, code):
    """
    :param code: The HTTP response status code
    :type context: behave.runner.Context
    """
    assert (context.statusCode == code), \
        f'The status code is not the expected value, received {context.statusCode}, expected {code}'

    number_users = len(context.response['users'])

    index = 0
    for element in context.table.rows:
        valid_response = dict(element.as_dict())
        # | id | username | email | enabled | gravatar | date_password | description | website |
        username = valid_response['username']
        email = valid_response['email']
        enabled = valid_response['enabled']
        gravatar = valid_response['gravatar']
        description = valid_response['description']
        website = valid_response['website']

        assert ("id" in context.response['users'][index]), \
            f"The id is not in the description of the user {index}, data received: \n{context.response['users'][index]}"

        assert (context.response['users'][index]['username'] == username), \
            f"The username is not the expected, received {context.response['users'][index]['username']}, " \
            f"expected {username}"

        assert (context.response['users'][index]['email'] == email), \
            f"The email value is not the expected value, received {context.response['users'][index]['email']}, " \
            f"expected {email}"

        assert (context.response['users'][index]['enabled'] == enabled), \
            f"The enabled value is not the expected value, received {context.response['users'][index]['enabled']}, " \
            f"expected {enabled}"

        assert (context.response['users'][index]['gravatar'] == gravatar), \
            f"The enabled value is not the expected value, received {context.response['users'][index]['enabled']}, " \
            f"expected {gravatar}"

        assert ("date_password" in context.response['users'][index]), \
            f"The date_password is not in the description of the user {index}, " \
            f"data received: \n{context.response['users'][index]}"

        assert (context.response['users'][index]['description'] == description), \
            f"The description value is not the expected value, " \
            f"received {context.response['users'][index]['description']}, expected {description}"

        assert (context.response['users'][index]['website'] == website), \
            f"The website value is not the expected value, " \
            f"received {context.response['users'][index]['website']}, expected {website}"

        index += 1

    assert (index == number_users), \
        f'The number of received users are not the expected value, received {number_users}, expected {index}'


@step('the body request described in file "{file}"')
@when('I define the body request described in file "{file}"')
def step_impl(context, file):
    """
    :param file: the expected response content of the HTTP operation
    :type context: behave.runner.Context
    """
    file = join(context.data_home, file)
    with open(file) as f:
        context.payload = f.read()


@step('I send a {op} HTTP request to the url "{url}" with the "{resource}" id from previous execution')
def step_impl(context, op, url, resource):
    """
    :param resource: The specific resource of the HTTP operation {admin user, organization}
    :param url: The url of the HTTP operation
    :param op: The corresponding HTTP operation {patch, delete, get}
    :type context: behave.runner.Context
    """
    global adminId

    if resource == 'admin user':
        url = url + f'/{adminId}'
    elif resource == 'organization':
        url = url + f'/{settings.organizationId}'
    elif resource == 'application':
        url = url + f'/{settings.applicationId}'

    op = op.lower()
    try:
        if op == 'patch':
            response = patch(url, data=context.payload, headers=context.header)
        elif op == 'delete':
            response = delete(url, headers=context.header)
        elif op == 'get':
            response = get(url, headers=context.header)
        else:
            raise Exception(f'HTTP operation not allowed or unknown: {op}')
    except RequestException as e:
        raise SystemExit(e)

    context.responseHeaders = response.headers
    context.statusCode = str(response.status_code)

    try:
        context.response = response.json()
    except JSONDecodeError:
        context.response = ""


@when('I send a POST HTTP request to "{url}"')
def step_impl(context, url):
    """
    :param url: the url of the HTTP operation
    :type context: behave.runner.Context
    """
    try:
        response = post(url, json=loads(context.payload), headers=context.header)
    except RequestException as e:
        raise SystemExit(e)

    context.responseHeaders = response.headers
    context.statusCode = str(response.status_code)

    try:
        context.response = response.json()
    except JSONDecodeError:
        context.response = ""


@step('the content-type header key equal to "{value}"')
@when('the content-type header key equal to "{value}"')
def step_impl(context, value):
    """
    :param value: The corresponding value of the Content-Type key
    :type context: behave.runner.Context
    """
    try:
        context.header['Content-Type'] = value
    except AttributeError:
        context.header = {'Content-Type': value}


@step('I receive a HTTP "{code}" status code from Keyrock and extract the id from "{user}" user')
def step_impl(context, code, user):
    """
    :param user: the username of the Keyrock user
    :param code: HTTP Response Status Code
    :type context: behave.runner.Context
    """
    global userId

    assert (context.statusCode == code), \
        f'Wrong Status Code, received \"{context.statusCode}\", but it was expected \"{code}\"'

    out = list(filter(lambda x: x['username'] == user, context.response['users']))
    context.userId = out[0]['id']


@step('I set the organization_roles as "{role}" url with organizationId and userId')
def step_impl(context, role):
    """
    :param role: the corresponding role of the organization
    :type context: behave.runner.Context
    """
    global userId

    context.url = f'http://localhost:3005/v1/organizations/{settings.organizationId}' \
                  f'/users/{userId}/organization_roles/{role}'


@when("I send a {op} HTTP request to that url")
def step_impl(context, op):
    """
    :param op: HTTP Operation {patch, delete, get, put, post}
    :type context: behave.runner.Context
    """
    op = op.lower()

    try:
        if op == 'put':
            if context.payload is None:
                response = put(context.url, headers=context.header)
            else:
                response = put(context.url, data=context.payload, headers=context.header)
        elif op == 'get':
            kwargs = dict()
            if hasattr(context, 'header'):
                kwargs['headers'] = context.header

            if hasattr(context, 'params'):
                kwargs['params'] = context.params

            response = get(url=context.url, **kwargs)
        elif op == 'delete':
            response = delete(context.url, headers=context.header)
        elif op == 'post':
            if context.payload is None:
                response = post(context.url, headers=context.header)
            else:
                response = post(context.url, data=context.payload, headers=context.header)
        elif op == 'patch':
            if context.payload is None:
                response = patch(context.url,  headers=context.header)
            else:
                response = patch(context.url,  data=context.payload, headers=context.header)
        else:
            raise Exception(f'HTTP operation not allowed or unknown: {op}')
    except RequestException as e:
        raise SystemExit(e)

    context.responseHeaders = response.headers
    context.statusCode = str(response.status_code)

    try:
        if response.text != '':
            context.response = response.json()
        else:
            context.response = ''
    except JSONDecodeError:
        # Tutorial 405 and 406 send XML content, we need to parse it
        context.response = response.text
        context.xml = dict()
        parser = minidom.parseString(response.text)

        get_xml_data(context=context, parser=parser)


@then('I receive a HTTP "{code}" status code with the same organizationId and userId and role equal to "{role}"')
def step_impl(context, code, role):
    """
    :param role: the corresponding role of the organization
    :param code: the HTTP Response Status Code
    :type context: behave.runner.Context
    """
    assert (context.statusCode == code), \
        f'Wrong Status Code, received \"{context.statusCode}\", but it was expected \"{code}\"'

    raise NotImplementedError(
        u'STEP: And   I receive a HTTP "200" status code from Keyrock and extract the id from the first organization')


@step('I receive a HTTP "{code}" status code from Keyrock and extract the id from the first organization')
def step_impl(context, code):
    """
    :param code: the HTTP Response Status Code
    :type context: behave.runner.Context
    """
    assert (context.statusCode == code), \
        f'Wrong Status Code, received \"{context.statusCode}\", but it was expected \"{code}\"'

    # We need to extract the organizaitonId from this operation

    raise NotImplementedError(
        u'STEP: And   I receive a HTTP "200" status code from Keyrock and extract the id from the first organization')


@step("I set the organization users url with organizationId from the previous scenario")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.url = f'http://localhost:3005/v1/organizations/{settings.organizationId}/users'


@step('I set the organization roles url with organizationId from the previous scenario and userId from "bob"')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.url = f'http://localhost:3005/v1/organizations/{settings.organizationId}' \
                  f'/users/{context.userId}/organization_roles'


def get_xml_data(context, parser):
    """
    Return the xml data from the response based on the received structure
    :type context: behave.runner.Context
    :param context: The behave context
    :param parser: The XML parser
    :return:
    """
    tag = parser.firstChild.tagName

    if 'resources' in tag:
        analyze_resources(context=context, parser=parser, tag=tag)
    elif 'link' in tag:
        analyze_link(context=context, parser=parser, tag=tag)
    elif 'productMetadata' in tag:
        analyze_product_metadata(context=context, parser=parser, tag=tag)
    elif 'domain' in tag:
        # We need to extract properties.externalId, and for each childResources.link href and title
        analyze_domain(context=context, parser=parser, tag=tag)
    elif 'PolicySet' in tag:
        # We need to extract PolicySetId, Version, Description, Policy.PolicyId, Policy.Version, Policy.Description,
        # Policy.Rule.RuleId, Policy.Rule.Effect
        analyze_policy_set(context=context, parser=parser, tag=tag)
    elif 'Response' in tag:
        analyze_response(context=context, parser=parser, tag=tag)
    elif 'pdpProperties' in tag:
        analyze_pdp_properties(context=context, parser=parser, tag=tag)


def analyze_pdp_properties(context, parser, tag):
    # Get the rootPolicyRefExpression data
    data = [x for x in parser.getElementsByTagName(tag)[0].childNodes if 'rootPolicyRefExpression' in x.localName or 'applicablePolicies' in x.localName]

    if len(data) != 2:
        raise Exception("It is expected that the response include the Nodes "
                        "'rootPolicyRefExpression' and 'applicablePolicies'")
    else:
        rootPolicyRefExpression = (
            [x for x in data if 'rootPolicyRefExpression' in x.localName][0].childNodes[0].data)

        rootPolicyRef = (
            [x for x in data if 'applicablePolicies' in x.localName][0].childNodes[0].childNodes[0].data)

        assert_that(rootPolicyRefExpression, equal_to(rootPolicyRef))

        context.xml['rootPolicyRef'] = rootPolicyRef


def analyze_response(context, parser, tag):
    context.xml['decision'] = parser.getElementsByTagName(tag)[0].childNodes[0].childNodes[0].childNodes[0].nodeValue


def analyze_policy_set(context, parser, tag):
    context.xml['id'] = parser.getElementsByTagName(tag)[0].attributes['PolicySetId'].value
    context.xml['version'] = parser.getElementsByTagName(tag)[0].attributes['Version'].value
    context.xml['policyCombiningAlgId'] = parser.getElementsByTagName(tag)[0].attributes['PolicyCombiningAlgId'].value

    node_name = [x.nodeName for x in list(parser.getElementsByTagName(tag)[0].childNodes)]

    context.xml['description'] = dict()
    context.xml['policies'] = list()

    # Look for Description and Policy tags
    for element in parser.getElementsByTagName(tag)[0].childNodes:
        match element.localName:
            case 'Description':
                context.xml['description'] = element.childNodes[0].nodeValue
            case 'Policy':
                # There could be a list of policies
                policy = dict()

                policy['id'] = element.attributes['PolicyId'].value
                policy['version'] = element.attributes['Version'].value
                policy['policyCombiningAlgId'] = element.attributes['RuleCombiningAlgId'].value
                policy['rules'] = list()

                childs = [x for x in element.childNodes if 'Policy' in element.localName]

                for child in childs:
                    match child.localName:
                        case 'Description':
                            policy['description'] = child.childNodes[0].nodeValue
                        case 'Rule':
                            rule = dict()
                            rule['id'] = child.attributes['RuleId'].value
                            rule['effect'] = child.attributes['Effect'].value
                            policy['rules'].append(rule)

                context.xml['policies'].append(policy)

    print(context.xml)


def analyze_domain(context, parser, tag):
    local_name = [x.localName for x in list(parser.getElementsByTagName(tag)[0].childNodes)]

    if 'properties' in local_name:
        context.xml['properties'] = parser.getElementsByTagName('properties')[0].attributes['externalId'].value
    else:
        context.xml['properties'] = None

    if 'childResources' in local_name:
        child_resources = list(parser.getElementsByTagName('childResources')[0].childNodes)
        context.xml['childResources'] = [{"href": x.attributes['href'].value, "title": x.attributes['title'].value}
                                         for x in child_resources]


def analyze_product_metadata(context, parser, tag):
    tag = parser.getElementsByTagName(tag)

    if 'name' in tag[0].attributes:
        name = tag[0].attributes['name'].value
        context.xml['name'] = name

    if 'version' in tag[0].attributes:
        context.xml['version'] = True
    else:
        context.xml['version'] = False

    if 'release_date' in tag[0].attributes:
        context.xml['release_date'] = True
    else:
        context.xml['release_date'] = False

    if 'uptime' in tag[0].attributes:
        context.xml['uptime'] = True
    else:
        context.xml['uptime'] = False

    if 'doc' in tag[0].attributes:
        context.xml['doc'] = True
    else:
        context.xml['doc'] = False


def analyze_link(context, parser, tag):
    global domainId
    global policySetId

    tag = parser.getElementsByTagName(tag)

    if 'rel' in tag[0].attributes:
        rel = tag[0].attributes['rel'].value

        if rel == 'item':
            set_xml_data(tag=tag)

    if 'href' in tag[0].attributes:
        match context.operation:
            case 'pap policies':
                policySetId = tag[0].attributes['href'].value
                context.xml['policySetId'] = policySetId
            case 'set domain':
                domainId = tag[0].attributes['href'].value
                context.xml['domainId'] = domainId


def analyze_resources(context, parser, tag):
    # We receive a resource, therefore we extract the domainID from ns2:link
    global domainId
    global revisions
    global policyId

    tag = parser.firstChild.firstChild.tagName
    tag = parser.getElementsByTagName(tag)

    if 'title' in tag[0].attributes:
        context.xml['domainId'] = True
        domainId = tag[0].attributes['title'].value
    else:
        context.xml['domainId'] = False

        if len(list(tag)) > 1:
            if context.operation == 'a pap policy set':
                # We are obtaining the List all revisions of a pap policies available for a policyId
                context.xml['policyId'] = False
                context.xml['revisions'] = \
                    [{'href': x.attributes['href'].value, 'rel': x.attributes['rel'].value} for x in list(tag)]

                revisions = [x for x in context.xml['revisions'] if x['href'] != 'root'][0]['href']
            else:
                # We are obtaining the List all PolicySets available within a Domain through the resources tag
                context.xml['policies'] = \
                    [{'href': x.attributes['href'].value, 'rel': x.attributes['rel'].value} for x in list(tag)]

                policyId = [x for x in context.xml['policies'] if x['href'] != 'root'][0]['href']
