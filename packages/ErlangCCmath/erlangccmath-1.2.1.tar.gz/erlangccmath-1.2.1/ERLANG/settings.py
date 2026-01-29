# =============================================================================
# REQUIRED PACKAGES
# =============================================================================
import requests

# =============================================================================
# POST REQUEST & USER AUTHENTICATION
# This function sends a post request to given URL and encodes the return in JSON.
# =============================================================================

session_UID = None

def setUID(UID):
    global session_UID
    session_UID = UID
    
def getUID():
    return session_UID


output={}
def request(output):
    """
    Sends a POST request to the given URL and returns the result encoded in JSON format.

    Args:
        output (dict): Dictionary containing the input data for the request.

    Returns:
        The response data from the server, decoded from JSON format.

    Raises:
        requests.exceptions.RequestException: If an error occurs while sending the request.
    """

    if session_UID:
        print("UID in output")
        output['UID'] = session_UID
    # response = requests.post('https://erlangaddin.ccmath.com/erlang/main.php', json=output)
    response = requests.post('https://erlangaddin.ccmath.com/erlang/v3.7/main.php', json=output)
    print("Response (raw):", response.text)
    result = response.json()
    return check_result(result)


def check_result(result):
    """
    Checks the response status and returns the result.

    Args:
        result (dict): Dictionary containing the response data from the server.

    Returns:
        The response result if the status is 1 and there is only one result, or a list of results if there are more than one.

    Raises:
        ValueError: If the status is not 1.
    """
    if result['status'] == 1:
        if len(result['result']) == 1:
            return result['result'][0]
        else:
            return result['result']
        return result
    else:
        if result['message'] == "User is not authenticated":
            print("authenticating user")
            return authenticate_user(output)

def authenticate_user(output):
    """
    Authenticates the user by sending a POST request to the authentication URL.

    Args:
        output (dict): Dictionary containing the input data for the request.

    Returns:
        The response data from the server, decoded from JSON format.

    Raises:
        requests.exceptions.RequestException: If an error occurs while sending the request.
    """
    UID = input("Enter your user ID: ")
    output['UID'] = UID
    response = requests.post('https://erlangaddin.ccmath.com/erlang/authenticate.php', json=output)
    result = response.json()
    if result['message'] == "User authenticated":
        print("User authenticated!")
        return request(output)
    else:
        raise ValueError("User ID is not valid!")