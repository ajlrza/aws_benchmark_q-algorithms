def get_configs_test(config: str):

    config_dict = {
        "ENDPOINT_URL": "http://localhost:4566",
        "METADATA_SERVICE": "http://localhost:4566/latest/meta-data/instance-id",
        "MOCK_INSTANCE_ID": "i-0123456789abcdef0",
        "MOCK_ROLE_AR": "arn:aws:iam::000000000000:role/local-mock-role",
    }

    return config_dict[config]
