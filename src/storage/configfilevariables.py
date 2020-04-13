
from simpleeval import simple_eval

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
            variables = variables.copy()
            variables.update(new_variables)

        for key, value in content.items():
            new_key = subVariables(key, enabled=True, variables=variables)
            new_val = subVariables(value, enabled=True, variables=variables)

            content[new_key] = new_val

    elif isinstance(content, list):
        for i, element in enumerate(content):
            content[i] = subVariables(element, enabled=enabled,
                                      variables=variables)
    elif isinstance(content, str):
        if content.startswith('#'):
            return content[1:]
        if content.startswith('raw#'):
            return content[4:]
        if content.startswith('var#'):
            return variables[content[4:].strip()]
        if content.startswith('expr#'):
            return simple_eval(content[5:], names=variables)
        if content.startswith('format#'):
            return content[7:].format(**variables)

    return content
