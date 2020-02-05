
def subVariables(content, enabled=None, variables=None):

    if enabled is False:
        return content

    if isinstance(content, dict):

        if enabled is None:
            config = content.get('Config')

            if config is None:
                return content

            if config.get('variables_enabled', False) is False:
                return content

        new_variables = {variable['id']: variable['value']
                        for variable in content.get('Variable', ())}

        if variables is None:
            variables = new_variables
        else:
            variables = variables.copy().update(new_variables)

        for key, value in content.items():
            new_key = subVariables(key, enabled=enabled, variables=variables)
            new_val = subVariables(value, enabled=enabled, variables=variables)

            content[new_key] = new_val

    elif isinstance(content, list):
        for i, element in enumerate(content):
            content[i] = subVariables(content, enabled=enabled,
                                      variables=variables)
    elif isinstance(content, str):
        if content.startswith('var#'):
            return variables[content[4:].strip()]

    return content
