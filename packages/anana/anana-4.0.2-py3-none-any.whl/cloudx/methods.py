class Method:
    """
    A class that handles dynamic method calls in a case-insensitive manner.
    Supported methods include HTTP methods, event methods, and DynamoDB stream methods.
    """
    
    # Dictionary mapping method names to function calls
    supported_methods = {
        "get": lambda: "GET",
        "post": lambda: "POST",
        "put": lambda: "PUT",
        "delete": lambda: "DELETE",
        "patch": lambda: "PATCH",
        "options": lambda: "OPTIONS",
        "head": lambda: "HEAD",
        "objectcreated": lambda: "ObjectCreated",
        "objectremoved": lambda: "ObjectRemoved",
        "objectrestore": lambda: "ObjectRestore",
        "reducedredundancylostobject": lambda: "ReducedRedundancyLostObject",
        "replication": lambda: "Replication",
        "lifecycleexpiration": lambda: "LifecycleExpiration",
        "lifecycletransition": lambda: "LifecycleTransition",
        "intelligenttiering": lambda: "IntelligentTiering",
        "objecttagging": lambda: "ObjectTagging",
        "objectacl": lambda: "ObjectAcl",
        "testevent": lambda: "TestEvent",
        "insert": lambda: "INSERT",
        "modify": lambda: "MODIFY",
        "remove": lambda: "REMOVE"
    }

    @classmethod
    def _get_method_name(cls, method):
        """
        Convert the method name to lowercase and capitalize the first letter.
        
        Args:
            method (str): The method name in any case format.
        
        Returns:
            str: The method name with the first letter capitalized and the rest lowercase.
        """
        return method.lower().capitalize()

    @classmethod
    def __class_getitem__(cls, method_name):
        """
        Allows subscripting on the class directly and retrieves the corresponding method.
        Converts the method name to the correct format and checks if it is supported.
        
        Args:
            method_name (str): The method name to be checked and called.
        
        Returns:
            str: The result of calling the corresponding method.
        
        Raises:
            AttributeError: If the method is not supported.
        """
        if not isinstance(method_name, str):
            raise AttributeError("Method is not supported.")  # Raise an error if method is not str (number, Non, array....)
        method_name = cls._get_method_name(method_name)
        if method_name.lower() in cls.supported_methods:
            return cls.supported_methods[method_name.lower()]()  # Call the corresponding lambda function
        else:
            raise AttributeError(f"Method '{method_name}' is not supported.")
