"""This module contains classes for OneCompute web API client-id and endpoints."""

from typing import Dict

from .environment import Environment


class OneComputeWebApiClientId:
    """
    A class containing static methods for getting OneCompute web API client-id
    based on the environment.
    """

    CLIENT_ID: Dict[Environment, str] = {
        # OCP-DevCore-Global-API_app
        Environment.DevCore: "87e35f82-8b6f-4780-b8a0-2f500540e402",
        # OCP-Dev-Global-API_app
        Environment.Development: "655e104f-6a01-4137-ad1f-a9a673206332",
        # OCP-Test-Global-API_app
        Environment.Testing: "0e21339f-89ab-4c97-91e7-64506c30bc4a",
        # OCP-Prod-Global-API_app
        Environment.Staging: "e7cc9e4d-bb17-4295-aa3e-477e87b5e4d9",
        # OCP-Prod-Global-API_app
        Environment.Production: "e7cc9e4d-bb17-4295-aa3e-477e87b5e4d9",
    }
    """A dictionary of client-ids for different environments."""

    @staticmethod
    def get_onecompute_webapi_client_id(env: Environment) -> str:
        """
        Gets the web API client-id for the given environment.

        Args:
            env (Environment): The environment id.

        Returns:
            str: The web API client-id registered with DNV Veracity.
        """
        return OneComputeWebApiClientId.CLIENT_ID.get(env, "")


class OneComputeWebApiEndpoints:
    """
    A class containing static methods for getting OneCompute web API endpoints
    based on the environment.
    """

    BASE_URLS: Dict[Environment, str] = {
        Environment.DevCore: "https://devcore.onecompute.dnv.com",
        Environment.Development: "https://develop.onecompute.dnv.com",
        Environment.Testing: "https://test.onecompute.dnv.com",
        Environment.Staging: "https://onecompute.dnv.com",
        Environment.Production: "https://onecompute.dnv.com",
    }
    """A dictionary of base URLs for different environments."""

    @staticmethod
    def get_onecompute_webapi_endpoint(env: Environment) -> str:
        """
        Gets the web API endpoint for the given environment.

        Args:
            env (Environment): The environment id.

        Returns:
            str: The web API endpoint.
        """
        return OneComputeWebApiEndpoints.BASE_URLS.get(env, "")
