import logging

logger = logging.getLogger(__name__)


def _auth_userpass(client, config):
    username = config['username']
    password = config['password']
    auth_response = client.auth.userpass.login(username=username, password=password)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using userpass")


def _auth_token(client, config):
    client.token = config['token']
    logger.info("Vault authenticated using token")


def _auth_approle(client, config):
    approle_config = config.get('app_role', {})
    role_id = approle_config.get('role_id')
    secret_id = approle_config.get('secret_id', None)

    auth_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using approle")


def _auth_jwt(client, config):
    jwt_config = config.get('jwt', {})
    role = jwt_config.get('role')
    jwt = jwt_config.get('jwt')

    auth_response = client.auth.jwt.jwt_login(role=role, jwt=jwt)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using jwt")


def _auth_ldap(client, config):
    ldap_config = config.get('ldap', {})
    username = ldap_config.get('username')
    password = ldap_config.get('password')

    auth_response = client.auth.ldap.login(username=username, password=password)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using ldap")


def _auth_github(client, config):
    token = config['token']
    auth_response = client.auth.github.login(token=token)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using github")


def _auth_gcp(client, config):
    gcp_config = config.get('gcp', {})
    role = gcp_config.get('role')
    jwt = gcp_config.get('jwt')

    auth_response = client.auth.gcp.login(role=role, jwt=jwt)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using gcp")


def _auth_azure(client, config):
    azure_config = config.get('azure', {})
    role = azure_config.get('role')
    jwt = azure_config.get('jwt')
    subscription_id = azure_config.get('subscription_id', None)
    resource_group_name = azure_config.get('resource_group_name', None)
    vm_name = azure_config.get('vm_name', None)
    vmss_name = azure_config.get('vmss_name', None)

    auth_response = client.auth.azure.login(role=role, jwt=jwt, subscription_id=subscription_id,
                                            resource_group_name=resource_group_name,
                                            vm_name=vm_name, vmss_name=vmss_name)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using azure")


def _auth_aws_iam(client, config):
    iam_config = config.get('aws_iam', {})
    access_key = iam_config.get('access_key')
    secret_key = iam_config.get('secret_key')
    session_token = iam_config.get('session_token', None)
    header_value = iam_config.get('header_value', None)
    role = iam_config.get('role', None)

    auth_response = client.auth.aws.iam_login(access_key=access_key, secret_key=secret_key, session_token=session_token,
                                              header_value=header_value, role=role)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using aws iam")


def _auth_aws_ec2(client, config):
    ec2_config = config.get('aws_ec2', {})
    pkcs7 = ec2_config.get('pkcs7')
    nonce = ec2_config.get('nonce', None)
    role = ec2_config.get('role', None)

    auth_response = client.auth.aws.ec2_login(pkcs7=pkcs7, nonce=nonce, role=role)
    client.token = auth_response['auth']['client_token']
    logger.info("Vault authenticated using aws ec2")


# Map auth methods to corresponding functions
AUTH_METHODS = {
    'userpass': _auth_userpass,
    'token': _auth_token,
    'approle': _auth_approle,
    'jwt': _auth_jwt,
    'ldap': _auth_ldap,
    'github': _auth_github,
    'gcp': _auth_gcp,
    'azure': _auth_azure,
    'aws_iam': _auth_aws_iam,
    'aws_ec2': _auth_aws_ec2,
}


def authenticate_vault(client, config):
    vault_config = config.get('vault', {})
    auth_method = vault_config.get('authentication', 'userpass')  # default to userpass

    try:
        auth_func = AUTH_METHODS.get(auth_method)
        if not auth_func:
            raise ValueError(f"Unsupported authentication method: {auth_method}")
        auth_func(client, vault_config)
    except Exception as e:
        logger.error(f"Vault authentication failed using {auth_method}: {str(e)}")
        raise
