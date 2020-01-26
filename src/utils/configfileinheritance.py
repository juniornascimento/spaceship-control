
import itertools

def resolvePrefix(name, prefixes):

    for dot_count, char in enumerate(name):
        if char != '.':
            break
    else:
        raise ValueError(f'Could\'nt resolve \'{name}\'')

    if dot_count == 0:
        return name

    parent_returns = dot_count - 1

    if parent_returns > len(prefixes):
        ValueError(f'Could\'nt resolve \'{name}\'')

    new_prefix = tuple(prefixes[: len(prefixes) - parent_returns])

    resolved_name = '/'.join(itertools.chain(new_prefix, (name[dot_count:],)))

    new_prefix += tuple(name.split('/')[: -1])

    return resolved_name, new_prefix

def mergeProperty(child_property, parent_property):
    return child_property

def mergeInheritedFiles(file_content, get_parent_func, prefixes=()):

    config_content = file_content.get('Inheritance')

    if config_content is None:
        return file_content

    parent_name_not_resolved = config_content.get('parent')

    parent_name, parent_prefixes = \
        resolvePrefix(parent_name_not_resolved, prefixes)

    parent_content = get_parent_func(parent_name)

    parent_content = mergeInheritedFiles(parent_content, get_parent_func,
                                         prefixes=parent_prefixes)

    for key, parent_value in parent_content.items():
        child_value = file_content.get(key)
        if child_value is None:
            final_value = parent_value
        else:
            final_value = mergeProperty(child_value, parent_value)

        file_content[key] = final_value

    return file_content
