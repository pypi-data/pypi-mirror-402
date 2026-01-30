Hashicorp-vault-python
=========================

Hashicorp vault is a Python-Django app for the improvement application security leveraging secrets

Installation
------------

    * pip install hashicorp-vault-django
    * Add ``hashicorp_vault`` to your ``INSTALLED_APPS``

::

Setup in settings
-----------------

    * make config directory at project root level and create application.yml file inside config directory 
    * application.yml sample for vault configuration
        * vault:
              host: vault url  # https
              secret_engine: mount path  # secrests-config
              application: application path # secrets-ai
              username: username
              password: password
    * if your secrets stored in `/vault/secrets/secrets-config/kv/secrets-ai/` then use secrets-config as secret_engine and secrets-ai as application in vault configuration
    * consume vault secrets in your settings.py file 
          from hashicorp_vault.vault import get_vault_secrets

          vault_secrets = get_vault_secrets(BASE_DIR)

          DATABASES = {
            "default": {
                "ENGINE": config["datasource"]["DATABASE_ENGINE"],
                "NAME": vault_secrets.get("db_database"),
                "USER": vault_secrets.get("db_user"),
                "PASSWORD": vault_secrets.get("db_password"),
                "HOST": vault_secrets.get("host"),
                "PORT": vault_secrets.get("db_port"),
                "OPTIONS": {"charset": "utf8mb4"},
            },
        }
    * Use secret keys to access to secret values from vault
::


Vault Authentication Methods
----------------------------
This package supports multiple authentication methods for HashiCorp Vault. Configure your prefered method via the **application.yml** file.
The **vault.authentication** key determines which method will be used.

Supported authentication methods include:
    * userpass
    * token
    * approle
    * jwt
    * ldap
    * github
    * gcp
    * azure
    * aws_iam
    * aws_ec2

Below are the configuration examples for each.

# General Structure (Default authentication method is userpass)
     vault:
         host: vault url  # https or http
         secret_engine: mount path 
         application: application path
         username: username
         password: password
   
    1. userpass
        Authenticates with Vault using the username and password method.

        vault:
             authentication: userpass (Optional)
             host: url
             secret_engine: mount_path
             application: application_path
             username: username
             password: password

    2. token
        Use a pre-generated token to authenticate with Vault.

        vault:
             authentication: token
             host: url
             secret_engine: mount_path
             application: application_path
             token: 00000000-0000-0000-0000-000000000000 

    3. approle
        Use Vault AppRole authentication with role_id and secret_id.

        vault:
             authentication: approle
             host: url
             secret_engine: mount_path
             application: application_path
             app_role:
                role_id: bde2076b-cccb-3cf0-d57e-bca7b1e83a52
                secret_id: 1696536f-1976-73b1-b241-0b4213908d39

    4. jwt
        Authenticate using JWT/OIDC. Commonly used with external identity providers.

        vault:
             authentication: jwt
             host: url
             secret_engine: mount_path
             application: application_path
             jwt:
                role: your-jwt-role
                jwt: your-signed-jwt-token

    5. github
        Authenticate using a GitHub personal access token mapped to a Vault policy.
        
        vault:
             authentication: github
             host: url
             secret_engine: mount_path
             application: application_path
             token: your-github-personal-access-token


    6. gcp
        Authenticate Vault using Google Cloud IAM and JWT identity.
        
        vault:
             authentication: gcp
             host: url
             secret_engine: mount_path
             application: application_path
             gcp:
                role: your-gcp-role
                jwt: your-signed-jwt-from-gcp-service-account

    
    7. ldap
        Authenticate using your LDAP (e.g., Active Directory) credentials.

        vault:
             authentication: ldap
             host: url
             secret_engine: mount_path
             application: application_path
             ldap:
                username: your-ldap-username
                password: your-ldap-password


    8. azure
        Authenticate using Azure VM or VMSS instance identity.

        vault:
             authentication: azure
             host: url
             secret_engine: mount_path
             application: application_path
             azure:
                role: your-azure-role
                jwt: your-signed-jwt-token
                subscription_id: your-subscription-id (Optional)
                resource_group_name: your-resource-group (Optional)
                vm_name: your-vm-name (Optional)
                vmss_name: your-vmss-name (Optional)


    9. aws_iam
        Authenticate via AWS IAM using signed headers and Vault IAM role

        vault:
             authentication: aws_iam
             host: url
             secret_engine: mount_path
             application: application_path
             aws_iam:
                access_key: your-aws-access-key
                secret_key: your-aws-secret-key
                session_token: optional-session-token (Optional)
                header_value: optional-canonical-request-header (Optional)
                role: your-vault-role (Optional)


    10. aws_ec2
        Authenticate via AWS EC2 metadata service using instance identity document

        vault:
             authentication: aws_ec2
             host: url
             secret_engine: mount_path
             application: application_path
             aws_ec2:
                pkcs7: your-pkcs7-signed-identity-document
                nonce: optional-nonce (Optional)
                role: your-vault-ec2-role (Optional)
        
::

Compatibility
-------------
{py3.8, py3.10}-django{4.* above}
